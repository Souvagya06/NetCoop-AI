"""Create train/test datasets (CSV + JSON) and small sample files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

import config
from data_generator.generator import TelemetryGenerator
from data_generator.scenarios import SCENARIOS
from protocols.telemetry_schema import TelemetrySnapshot
from utils.logger import get_logger

log = get_logger("export_dataset")


def generate_snapshots(per_scenario: int, seed: int) -> List[TelemetrySnapshot]:
    gen = TelemetryGenerator(seed=seed)
    snaps: List[TelemetrySnapshot] = []
    for scenario in SCENARIOS:
        # normal data is the baseline for ML and false-alarm testing: double it
        n = per_scenario * 2 if scenario == "normal" else per_scenario
        snaps.extend(gen.generate_batch(scenario, n))
    return snaps


def snapshots_to_frame(snapshots: List[TelemetrySnapshot]) -> pd.DataFrame:
    rows: List[Dict] = []
    for s in snapshots:
        gt = s.ground_truth
        affected = set(gt.affected_devices) if gt else set()
        for d in s.devices:
            row = {"snapshot_id": s.snapshot_id, "scenario": gt.scenario if gt else "unknown", "device_id": d.device_id, "device_type": d.device_type.value}
            row.update(d.metrics.model_dump())
            row["is_root"] = bool(gt and gt.root_device == d.device_id)
            row["is_affected"] = d.device_id in affected
            rows.append(row)
    return pd.DataFrame(rows)


def export_all(out_dir: Path = config.GENERATED_DIR, sample_dir: Path = config.SAMPLE_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    train = generate_snapshots(config.TRAIN_SNAPSHOTS_PER_SCENARIO, config.TRAIN_SEED)
    test = generate_snapshots(config.TEST_SNAPSHOTS_PER_SCENARIO, config.TEST_SEED)

    train_df, test_df = snapshots_to_frame(train), snapshots_to_frame(test)
    train_df.to_csv(out_dir / "telemetry_train.csv", index=False)
    test_df.to_csv(out_dir / "telemetry_test.csv", index=False)
    with open(out_dir / "telemetry_dataset.json", "w") as fh:  # held-out test snapshots with ground truth
        json.dump([s.model_dump(mode="json") for s in test], fh)

    gen = TelemetryGenerator(seed=7)
    for name in ("normal", "latency_spike", "hardware_failure", "dns_failure"):
        snap = gen.generate_snapshot(name, snapshot_id=f"sample-{name}")
        with open(sample_dir / f"{name}.json", "w") as fh:
            json.dump(snap.model_dump(mode="json"), fh, indent=2)

    info = {"train_rows": len(train_df), "test_rows": len(test_df), "train_snapshots": len(train), "test_snapshots": len(test)}
    log.info("dataset exported: %s", info)
    return info


if __name__ == "__main__":
    print(export_all())

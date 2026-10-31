from __future__ import annotations

import json
from typing import Dict, List, Optional

import config
from data_generator.export_dataset import export_all
from data_generator.generator import TelemetryGenerator
from data_generator.scenarios import SCENARIO_INFO, SCENARIOS
from protocols.telemetry_schema import TelemetrySnapshot


def list_scenarios() -> List[Dict[str, str]]:
    return [{"name": n, "label": SCENARIO_INFO[n][0], "description": SCENARIO_INFO[n][1]} for n in SCENARIOS]


def simulate(scenario: str, seed: Optional[int] = None) -> TelemetrySnapshot:
    return TelemetryGenerator(seed=seed).generate_snapshot(scenario)


def list_samples() -> List[str]:
    return sorted(p.stem for p in config.SAMPLE_DIR.glob("*.json"))


def load_sample(name: str) -> Optional[TelemetrySnapshot]:
    path = config.SAMPLE_DIR / f"{name}.json"
    if not path.exists():
        return None
    return TelemetrySnapshot.model_validate(json.loads(path.read_text()))


def generate_dataset() -> dict:
    return export_all()

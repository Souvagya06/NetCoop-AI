"""Evaluate on the HELD-OUT test set (different seed from training).

Reports (1) end-to-end diagnosis accuracy and confusion matrix, (2) root-device
accuracy, (3) how often the evidence-request round was used, and (4) device-level
anomaly detection of the two Isolation Forest models vs the rule-only baseline.

Usage:  python ml_models/evaluation/evaluate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

import config
from agents.infrastructure_agent import detector as infra_det
from agents.infrastructure_agent import rules as infra_rules
from agents.infrastructure_agent.preprocessing import FEATURES as INFRA_FEATURES
from agents.performance_agent import detector as perf_det
from agents.performance_agent import rules as perf_rules
from agents.performance_agent.preprocessing import FEATURES as PERF_FEATURES
from data_generator.export_dataset import generate_snapshots
from data_generator.scenarios import SCENARIOS
from ml_models.evaluation.metrics import binary_report, classification_report
from orchestrator.orchestrator import Orchestrator
from protocols.telemetry_schema import TelemetrySnapshot

ROOT_CAUSE_OF = {s: s for s in SCENARIOS}  # scenario name == expected root-cause code


def load_test_snapshots():
    path = config.GENERATED_DIR / "telemetry_dataset.json"
    if path.exists():
        return [TelemetrySnapshot.model_validate(s) for s in json.loads(path.read_text())]
    return generate_snapshots(config.TEST_SNAPSHOTS_PER_SCENARIO, config.TEST_SEED)


def evaluate_diagnosis(snapshots, use_ml_note: str = "") -> dict:
    orch = Orchestrator(use_llm=False)
    y_true, y_pred, dev_ok, dev_total, rounds, conf_ok, conf_bad = [], [], 0, 0, 0, [], []
    for s in snapshots:
        r = orch.diagnose(s)
        truth, pred = s.ground_truth.scenario, r["root_cause"]["code"]
        y_true.append(truth)
        y_pred.append(pred)
        (conf_ok if truth == pred else conf_bad).append(r["root_cause"]["confidence"])
        rounds += r["evidence_rounds"] > 0
        if s.ground_truth.root_device and truth == pred:
            dev_total += 1
            dev_ok += r["root_cause"]["root_device"] == s.ground_truth.root_device
    labels = SCENARIOS + [l for l in sorted(set(y_pred)) if l not in SCENARIOS]
    rep = classification_report(y_true, y_pred, labels)
    rep.update({
        "snapshots": len(snapshots),
        "root_device_accuracy_when_cause_correct": round(dev_ok / dev_total, 3) if dev_total else None,
        "evidence_round_used_pct": round(100 * rounds / len(snapshots), 1),
        "mean_confidence_correct": round(float(np.mean(conf_ok)), 3) if conf_ok else None,
        "mean_confidence_wrong": round(float(np.mean(conf_bad)), 3) if conf_bad else None,
        "ml_models_loaded": {"performance": perf_det.detector.available, "infrastructure": infra_det.detector.available},
    })
    return rep


def evaluate_detectors() -> dict:
    """Device-level: does the detector flag devices that really are faulty/affected?"""
    df = pd.read_csv(config.GENERATED_DIR / "telemetry_test.csv")
    df = df[df["reachable"]]
    out = {}
    for name, feats, det, rules_mod in (("performance", PERF_FEATURES, perf_det.detector, perf_rules), ("infrastructure", INFRA_FEATURES, infra_det.detector, infra_rules)):
        # ground truth for the device-level view: the device is the ROOT of a fault
        truth = df["is_root"].tolist()
        rule_pred = [bool(rules_mod.evaluate_device(r)) for r in df[feats + [c for c in rules_mod.THRESHOLDS if c not in feats]].to_dict("records")]
        entry = {"rules_only": binary_report(truth, rule_pred)}
        if det.available:
            ml_pred = (det.score(df[feats]) >= 0.5).tolist()
            entry["isolation_forest_only"] = binary_report(truth, ml_pred)
            entry["rules_or_forest"] = binary_report(truth, [a or b for a, b in zip(rule_pred, ml_pred)])
        out[name] = entry
    return out


def main() -> None:
    snaps = load_test_snapshots()
    diag = evaluate_diagnosis(snaps)
    det = evaluate_detectors() if (config.GENERATED_DIR / "telemetry_test.csv").exists() else {}
    report = {"diagnosis": diag, "detectors_device_level": det}
    out = config.GENERATED_DIR / "evaluation_report.json"
    out.write_text(json.dumps(report, indent=2))

    print(f"\nEnd-to-end diagnosis on {diag['snapshots']} held-out snapshots: accuracy = {diag['accuracy']:.1%}")
    print(f"Root-device accuracy (when cause correct): {diag['root_device_accuracy_when_cause_correct']}")
    print(f"Evidence-request round used in {diag['evidence_round_used_pct']}% of cases | mean evidence score: correct={diag['mean_confidence_correct']}, wrong={diag['mean_confidence_wrong']}")
    print(f"ML models loaded: {diag['ml_models_loaded']}\n")
    print(f"{'scenario':<20}{'precision':>10}{'recall':>8}{'f1':>7}{'n':>6}")
    for l, m in diag["per_class"].items():
        if m["support"]:
            print(f"{l:<20}{m['precision']:>10.2f}{m['recall']:>8.2f}{m['f1']:>7.2f}{m['support']:>6}")
    print("\nConfusion matrix (rows = truth, cols = predicted):")
    labels = diag["labels"]
    print(" " * 20 + "".join(f"{l[:6]:>8}" for l in labels))
    for l, row in zip(labels, diag["confusion_matrix"]):
        if sum(row):
            print(f"{l:<20}" + "".join(f"{v:>8}" for v in row))
    if det:
        print("\nDevice-level detection of the root device (precision / recall):")
        for agent, d in det.items():
            for variant, m in d.items():
                print(f"  {agent:<15}{variant:<24}P={m['precision']:.2f}  R={m['recall']:.2f}  (FP={m['fp']}, FN={m['fn']})")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()

"""Confidence calibration analysis.

Groups diagnoses into confidence buckets and measures what fraction of
each bucket was actually correct, then computes the Expected Calibration
Error (ECE).

Usage (standalone):
    python ml_models/evaluation/calibration.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
from typing import Dict, List, Optional, Tuple

import numpy as np


def calibration_buckets(
    confidences: List[float],
    correct: List[bool],
    n_bins: int = 10,
) -> List[Dict]:
    """Return per-bucket calibration stats.

    Args:
        confidences: model confidence for each prediction in [0, 1].
        correct: whether each prediction was correct.
        n_bins: number of equal-width buckets.

    Returns:
        List of dicts, one per non-empty bucket:
          bucket_lo, bucket_hi, mean_confidence, accuracy, count
    """
    assert len(confidences) == len(correct)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    buckets = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        idx = [i for i, c in enumerate(confidences) if lo <= c < hi]
        if not idx:
            continue
        confs = [confidences[i] for i in idx]
        accs = [correct[i] for i in idx]
        buckets.append({
            "bucket_lo": round(float(lo), 2),
            "bucket_hi": round(float(hi), 2),
            "mean_confidence": round(float(np.mean(confs)), 3),
            "accuracy": round(float(np.mean(accs)), 3),
            "count": len(idx),
        })
    return buckets


def expected_calibration_error(buckets: List[Dict], total: int) -> float:
    """ECE = weighted average |confidence - accuracy| per bucket."""
    if total == 0:
        return 0.0
    ece = sum(b["count"] * abs(b["mean_confidence"] - b["accuracy"]) for b in buckets) / total
    return round(float(ece), 4)


def print_calibration(buckets: List[Dict], ece: float) -> None:
    print(f"\n{'Bucket':>12}  {'Mean conf':>10}  {'Accuracy':>9}  {'Count':>6}  {'Gap':>7}")
    print("-" * 60)
    for b in buckets:
        gap = b["mean_confidence"] - b["accuracy"]
        flag = " ▲ over" if gap > 0.1 else (" ▼ under" if gap < -0.1 else "")
        print(f"[{b['bucket_lo']:.2f},{b['bucket_hi']:.2f})  "
              f"{b['mean_confidence']:>10.3f}  {b['accuracy']:>9.3f}  "
              f"{b['count']:>6}  {gap:>+7.3f}{flag}")
    print(f"\nExpected Calibration Error (ECE): {ece:.4f}")
    if ece < 0.05:
        print("  → Well-calibrated (ECE < 0.05)")
    elif ece < 0.15:
        print("  → Reasonably calibrated")
    else:
        print("  → Poorly calibrated — confidence scores should not be treated as probabilities")


def run_calibration(snapshots, diagnoser=None) -> Dict:
    """Run *diagnoser* on *snapshots* and return calibration results.

    diagnoser must have a .diagnose(snapshot) method; defaults to FullSystem.
    """
    if diagnoser is None:
        from ml_models.evaluation.baselines import FullSystem
        diagnoser = FullSystem()

    confidences, correct = [], []
    for s in snapshots:
        r = diagnoser.diagnose(s)
        truth = s.ground_truth.scenario
        pred = r["root_cause"]["code"]
        conf = r["root_cause"]["confidence"]
        confidences.append(conf)
        correct.append(truth == pred)

    buckets = calibration_buckets(confidences, correct)
    ece = expected_calibration_error(buckets, len(confidences))
    return {
        "diagnoser": getattr(diagnoser, "name", "unknown"),
        "n_snapshots": len(snapshots),
        "overall_accuracy": round(float(np.mean(correct)), 3) if correct else None,
        "mean_confidence": round(float(np.mean(confidences)), 3) if confidences else None,
        "ece": ece,
        "buckets": buckets,
    }


def main() -> None:
    import config
    from ml_models.evaluation.evaluate import load_test_snapshots
    from ml_models.evaluation.baselines import FullSystem

    snaps = load_test_snapshots()
    result = run_calibration(snaps, FullSystem())
    print(f"\nCalibration analysis for {result['diagnoser']} on {result['n_snapshots']} snapshots")
    print(f"Overall accuracy: {result['overall_accuracy']:.1%} | "
          f"Mean confidence: {result['mean_confidence']:.3f}")
    print_calibration(result["buckets"], result["ece"])

    out = config.GENERATED_DIR / "calibration_report.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()


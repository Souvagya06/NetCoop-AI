from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def classification_report(y_true: List[str], y_pred: List[str], labels: List[str]) -> Dict:
    p, r, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {
        "accuracy": round(float(np.mean(np.array(y_true) == np.array(y_pred))), 4),
        "per_class": {l: {"precision": round(float(p[i]), 3), "recall": round(float(r[i]), 3), "f1": round(float(f1[i]), 3), "support": int(support[i])} for i, l in enumerate(labels)},
        "labels": labels,
        "confusion_matrix": cm.tolist(),
    }


def binary_report(y_true: List[bool], y_pred: List[bool]) -> Dict:
    yt, yp = np.array(y_true, dtype=bool), np.array(y_pred, dtype=bool)
    tp, fp, fn, tn = int((yt & yp).sum()), int((~yt & yp).sum()), int((yt & ~yp).sum()), int((~yt & ~yp).sum())
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(tp / (tp + fp), 3) if tp + fp else 0.0,
        "recall": round(tp / (tp + fn), 3) if tp + fn else 0.0,
    }

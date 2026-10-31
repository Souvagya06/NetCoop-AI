"""Shared Isolation Forest wrapper (train on healthy data, score new data 0..1)."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class AnomalyModel:
    """Novelty detector. 0 = looks like training data, 1 = very unusual.

    The raw Isolation Forest score is calibrated against the healthy training data:
    the median healthy score maps to 0, the 99.5th percentile maps to 0.5.
    """

    def __init__(self, features: List[str], n_estimators: int = 200, random_state: int = 42) -> None:
        self.features = features
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.pipeline: Optional[Pipeline] = None
        self.lo = 0.0
        self.hi = 1.0

    def fit(self, df: pd.DataFrame) -> "AnomalyModel":
        X = df[self.features].to_numpy(dtype=float)
        self.pipeline = Pipeline([
            ("scale", StandardScaler()),
            ("iforest", IsolationForest(n_estimators=self.n_estimators, contamination="auto", random_state=self.random_state)),
        ])
        self.pipeline.fit(X)
        raw = -self.pipeline.score_samples(X)
        self.lo = float(np.percentile(raw, 50))
        self.hi = float(np.percentile(raw, 99.5))
        return self

    def score(self, df: pd.DataFrame) -> np.ndarray:
        if self.pipeline is None:
            raise RuntimeError("model not fitted")
        if len(df) == 0:
            return np.zeros(0)
        raw = -self.pipeline.score_samples(df[self.features].to_numpy(dtype=float))
        span = max(self.hi - self.lo, 1e-9)
        return np.clip((raw - self.lo) / (2 * span), 0.0, 1.0)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"features": self.features, "pipeline": self.pipeline, "lo": self.lo, "hi": self.hi, "n_estimators": self.n_estimators, "random_state": self.random_state}, path)
        return path

    @classmethod
    def load(cls, path: Path) -> "AnomalyModel":
        bundle = joblib.load(path)
        m = cls(bundle["features"], bundle.get("n_estimators", 200), bundle.get("random_state", 42))
        m.pipeline, m.lo, m.hi = bundle["pipeline"], bundle["lo"], bundle["hi"]
        return m


class OptionalDetector:
    """Loads a saved model if present; otherwise agents fall back to rules only."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.model: Optional[AnomalyModel] = None
        if path.exists():
            try:
                self.model = AnomalyModel.load(path)
            except Exception:  # corrupt / incompatible file -> rules only
                self.model = None

    @property
    def available(self) -> bool:
        return self.model is not None

    def score(self, df: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            return np.zeros(len(df))
        return self.model.score(df)

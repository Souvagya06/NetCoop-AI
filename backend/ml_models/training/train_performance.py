"""Train the Performance Agent's Isolation Forest on HEALTHY readings only."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

import config
from agents.performance_agent.preprocessing import FEATURES
from ml_models.detector_base import AnomalyModel
from utils.logger import get_logger

log = get_logger("train_performance")
MODEL_PATH = config.MODEL_DIR / "performance_model.joblib"


def train(csv_path: Path = config.GENERATED_DIR / "telemetry_train.csv") -> Path:
    df = pd.read_csv(csv_path)
    healthy = df[(df["scenario"] == "normal") & (df["reachable"])]
    model = AnomalyModel(FEATURES).fit(healthy)
    path = model.save(MODEL_PATH)
    log.info("saved %s (trained on %d healthy rows)", path.name, len(healthy))
    return path


if __name__ == "__main__":
    train()

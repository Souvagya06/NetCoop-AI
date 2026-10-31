from __future__ import annotations

import config
from ml_models.detector_base import OptionalDetector

detector = OptionalDetector(config.MODEL_DIR / "performance_model.joblib")


def reload() -> None:
    global detector
    detector = OptionalDetector(config.MODEL_DIR / "performance_model.joblib")

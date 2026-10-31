"""Central configuration. Values can be overridden with environment variables / .env"""
from __future__ import annotations

import os
from pathlib import Path

try:  # optional dependency
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # pragma: no cover
    pass

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets"
GENERATED_DIR = DATASET_DIR / "generated"
SAMPLE_DIR = DATASET_DIR / "sample"
MODEL_DIR = BASE_DIR / "ml_models" / "saved"

# --- dataset generation ---------------------------------------------------
# Train and test use DIFFERENT seeds so evaluation is on unseen random draws.
TRAIN_SEED = int(os.getenv("TRAIN_SEED", 42))
TEST_SEED = int(os.getenv("TEST_SEED", 2026))
TRAIN_SNAPSHOTS_PER_SCENARIO = int(os.getenv("TRAIN_SNAPSHOTS_PER_SCENARIO", 150))
TEST_SNAPSHOTS_PER_SCENARIO = int(os.getenv("TEST_SNAPSHOTS_PER_SCENARIO", 60))

# --- orchestration -------------------------------------------------------
AGENT_TIMEOUT_S = float(os.getenv("AGENT_TIMEOUT_S", 10))
MAX_EVIDENCE_ROUNDS = int(os.getenv("MAX_EVIDENCE_ROUNDS", 2))
INCIDENT_THRESHOLD = float(os.getenv("INCIDENT_THRESHOLD", 0.45))
CONTEST_MARGIN = float(os.getenv("CONTEST_MARGIN", 0.10))

# --- API -----------------------------------------------------------------
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")]
HISTORY_SIZE = int(os.getenv("HISTORY_SIZE", 200))

# --- optional Gemini summary (reporting agent) -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # verify the current model name in Google AI docs

"""Generate train/test datasets, sample files, and train both Isolation Forest models.

Usage (from the project root):  python scripts/generate_dataset.py [--no-train]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from data_generator.export_dataset import export_all  # noqa: E402
from ml_models.training import train_infrastructure, train_performance  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-train", action="store_true", help="only generate data; skip model training")
    args = ap.parse_args()
    print(export_all())
    if not args.no_train:
        print("saved:", train_performance.train())
        print("saved:", train_infrastructure.train())


if __name__ == "__main__":
    main()

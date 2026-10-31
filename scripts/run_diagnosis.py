"""Run one diagnosis from the command line.

Examples (from the project root):
  python scripts/run_diagnosis.py --scenario cpu_overload --seed 5
  python scripts/run_diagnosis.py --file backend/datasets/sample/hardware_failure.json --json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from data_generator.scenarios import SCENARIOS  # noqa: E402
from protocols.telemetry_schema import TelemetrySnapshot  # noqa: E402
from services import dataset_service, diagnosis_service  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=SCENARIOS, default="cpu_overload")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--file", help="diagnose a telemetry snapshot JSON file instead of simulating")
    ap.add_argument("--json", action="store_true", help="print the full JSON result instead of the report")
    args = ap.parse_args()

    if args.file:
        snap = TelemetrySnapshot.model_validate(json.loads(Path(args.file).read_text()))
    else:
        snap = dataset_service.simulate(args.scenario, args.seed)
    result = diagnosis_service.diagnose(snap)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return
    print("\n--- TIMELINE ---")
    for e in result["timeline"]:
        print(f"{e['t_ms']:>7.1f} ms  {e['actor']:<22} {e['event']:<17} {e['detail']}")
    print("\n" + result["report"]["markdown"])
    gt = result["ground_truth_simulation_only"]
    if gt:
        print(f"\n[simulation ground truth: {gt['scenario']} at {gt['root_device']}]")


if __name__ == "__main__":
    main()

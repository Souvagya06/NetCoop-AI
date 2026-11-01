from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from data_generator.scenarios import SCENARIOS
from protocols.telemetry_schema import TelemetrySnapshot
from services import dataset_service, diagnosis_service
from services.telemetry_buffer import get_buffer

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str = "normal"
    seed: Optional[int] = Field(default=None, ge=0, strict=True)


@router.get("/live")
def live_telemetry():
    """Returns current simulated network telemetry across all devices."""
    return diagnosis_service.get_current_telemetry()


@router.get("/buffer")
def buffer_summary():
    """Return rolling-window trend statistics for every tracked device.

    Only available after at least one diagnosis run has been performed.
    The window grows up to 10 readings (one per diagnosis call).
    """
    summaries = get_buffer().summaries()
    return {
        "window_size_max": get_buffer().window_size,
        "devices_tracked": len(summaries),
        "device_windows": summaries,
    }


@router.post("/push")
def push_snapshot(snapshot: TelemetrySnapshot):
    """Push an external telemetry snapshot into the rolling buffer.

    This endpoint exists so that future real / emulated data adapters can
    feed metrics into the buffer without triggering a full diagnosis run.
    Returns the per-device window summaries after ingestion.
    """
    buf = get_buffer()
    buf.push(snapshot)
    return {
        "accepted": True,
        "snapshot_id": snapshot.snapshot_id,
        "devices_in_buffer": len(buf.device_ids()),
    }


@router.post("/generate")
def generate(req: SimulateRequest):
    """Generate one synthetic telemetry snapshot (includes simulation ground truth)."""
    if req.scenario not in SCENARIOS:
        raise HTTPException(422, f"unknown scenario '{req.scenario}'. Valid: {SCENARIOS}")
    return dataset_service.simulate(req.scenario, req.seed).model_dump(mode="json")


@router.get("/samples")
def samples():
    return {"samples": dataset_service.list_samples()}


@router.get("/samples/{name}")
def sample(name: str):
    snap = dataset_service.load_sample(name)
    if snap is None:
        raise HTTPException(404, f"sample '{name}' not found. Run scripts/generate_dataset.py first.")
    return snap.model_dump(mode="json")

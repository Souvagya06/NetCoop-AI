from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from data_generator.scenarios import SCENARIOS
from services import dataset_service

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str = "normal"
    seed: Optional[int] = Field(default=None, ge=0, strict=True)


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

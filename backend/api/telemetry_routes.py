from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data_generator.scenarios import SCENARIOS
from services import dataset_service

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class SimulateRequest(BaseModel):
    scenario: str = "normal"
    seed: Optional[int] = None


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

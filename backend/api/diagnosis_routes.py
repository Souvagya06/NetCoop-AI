from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from data_generator.scenarios import SCENARIOS
from protocols.telemetry_schema import TelemetrySnapshot
from services import diagnosis_service

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str = "cpu_overload"
    seed: Optional[int] = Field(default=None, ge=0, strict=True)


@router.post("/run")
def run(snapshot: TelemetrySnapshot):
    """Diagnose a telemetry snapshot you provide."""
    return diagnosis_service.diagnose(snapshot)


@router.post("/simulate")
def simulate(req: SimulateRequest):
    """Generate a snapshot for a scenario, then diagnose it (best for demos)."""
    if req.scenario not in SCENARIOS:
        raise HTTPException(422, f"unknown scenario '{req.scenario}'. Valid: {SCENARIOS}")
    return diagnosis_service.simulate_and_diagnose(req.scenario, req.seed)


@router.get("/history")
def history():
    return {"incidents": diagnosis_service.list_incidents()}


@router.get("/{incident_id}")
def get_incident(incident_id: str):
    result = diagnosis_service.get_incident(incident_id)
    if result is None:
        raise HTTPException(404, f"incident '{incident_id}' not found (history is in-memory)")
    return result

from fastapi import APIRouter

from agents.connectivity_agent.topology import default_topology
from api import diagnosis_routes, telemetry_routes
from services import dataset_service, diagnosis_service

router = APIRouter()
router.include_router(diagnosis_routes.router)
router.include_router(telemetry_routes.router)


@router.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "NetCoop AI"}


@router.get("/scenarios", tags=["system"])
def scenarios():
    return {"scenarios": dataset_service.list_scenarios()}


@router.get("/topology", tags=["system"])
def topology():
    return default_topology().to_dict()


@router.get("/agents", tags=["system"])
def agents():
    return {"agents": diagnosis_service.agents_info()}

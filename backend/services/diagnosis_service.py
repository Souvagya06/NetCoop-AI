from __future__ import annotations

from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, List, Optional

import config
from orchestrator.orchestrator import Orchestrator
from protocols.telemetry_schema import TelemetrySnapshot
from services import dataset_service

_orchestrator: Optional[Orchestrator] = None
_history: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_lock = Lock()


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def diagnose(snapshot: TelemetrySnapshot) -> Dict[str, Any]:
    result = get_orchestrator().diagnose(snapshot)
    with _lock:
        _history[result["incident_id"]] = result
        while len(_history) > config.HISTORY_SIZE:
            _history.popitem(last=False)
    return result


def simulate_and_diagnose(scenario: str, seed: Optional[int] = None) -> Dict[str, Any]:
    return diagnose(dataset_service.simulate(scenario, seed))


def get_incident(incident_id: str) -> Optional[Dict[str, Any]]:
    return _history.get(incident_id)


def list_incidents() -> List[Dict[str, Any]]:
    with _lock:
        return [
            {"incident_id": r["incident_id"], "created_at": r["created_at"], "root_cause": r["root_cause"]["label"],
             "severity": r["root_cause"]["severity"], "confidence": r["root_cause"]["confidence"], "root_device": r["root_cause"]["root_device"]}
            for r in reversed(_history.values())
        ]


def agents_info() -> List[dict]:
    return get_orchestrator().registry.describe()

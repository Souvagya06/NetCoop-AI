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
_current_snapshot: Optional[TelemetrySnapshot] = None
_lock = Lock()


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def diagnose(snapshot: TelemetrySnapshot) -> Dict[str, Any]:
    global _current_snapshot
    with _lock:
        _current_snapshot = snapshot
    result = get_orchestrator().diagnose(snapshot)
    with _lock:
        _history[result["incident_id"]] = result
        while len(_history) > config.HISTORY_SIZE:
            _history.popitem(last=False)
    return result


def simulate_and_diagnose(scenario: str, seed: Optional[int] = None) -> Dict[str, Any]:
    snap = dataset_service.simulate(scenario, seed)
    return diagnose(snap)


def get_incident(incident_id: str) -> Optional[Dict[str, Any]]:
    return _history.get(incident_id)


def list_incidents() -> List[Dict[str, Any]]:
    with _lock:
        if not _history:
            # Seed with initial healthy baseline run if completely empty
            baseline = dataset_service.simulate("normal", seed=42)
            _lock.release()
            try:
                diagnose(baseline)
            finally:
                _lock.acquire()

        return [
            {
                "incident_id": r["incident_id"],
                "created_at": r["created_at"],
                "root_cause": r["root_cause"]["label"],
                "severity": r["root_cause"]["severity"],
                "confidence": r["root_cause"]["confidence"],
                "root_device": r["root_cause"]["root_device"],
            }
            for r in reversed(_history.values())
        ]


def get_current_telemetry() -> Dict[str, Any]:
    global _current_snapshot
    with _lock:
        if _current_snapshot is None:
            _current_snapshot = dataset_service.simulate("normal", seed=42)
        snap = _current_snapshot

    devices = [d.model_dump(mode="json") for d in snap.devices]
    n = len(devices) if devices else 1

    return {
        "snapshot_id": snap.snapshot_id,
        "timestamp": snap.timestamp.isoformat(),
        "device_count": len(devices),
        "online_count": sum(1 for d in snap.devices if d.metrics.reachable),
        "healthy_count": sum(
            1
            for d in snap.devices
            if d.metrics.reachable
            and d.metrics.cpu_utilization_pct < 80
            and d.metrics.latency_ms < 80
            and d.metrics.packet_loss_pct < 1.0
        ),
        "warning_count": sum(
            1
            for d in snap.devices
            if d.metrics.reachable
            and (
                d.metrics.cpu_utilization_pct >= 80
                or d.metrics.latency_ms >= 80
                or d.metrics.packet_loss_pct >= 1.0
            )
        ),
        "critical_count": sum(
            1
            for d in snap.devices
            if not d.metrics.reachable
            or d.metrics.cpu_utilization_pct >= 95
            or d.metrics.packet_loss_pct >= 10.0
        ),
        "averages": {
            "avg_cpu_pct": round(sum(d.metrics.cpu_utilization_pct for d in snap.devices) / n, 1),
            "avg_memory_pct": round(sum(d.metrics.memory_utilization_pct for d in snap.devices) / n, 1),
            "avg_latency_ms": round(sum(d.metrics.latency_ms for d in snap.devices) / n, 1),
            "avg_packet_loss_pct": round(sum(d.metrics.packet_loss_pct for d in snap.devices) / n, 2),
            "avg_link_util_pct": round(sum(d.metrics.link_utilization_pct for d in snap.devices) / n, 1),
        },
        "devices": devices,
    }


def agents_info() -> List[dict]:
    return get_orchestrator().registry.describe()

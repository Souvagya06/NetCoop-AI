"""Telemetry contract: what the data generator (or a real collector) must produce."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    SERVER = "server"


class DeviceMetrics(BaseModel):
    cpu_utilization_pct: float = Field(ge=0, le=100)
    memory_utilization_pct: float = Field(ge=0, le=100)
    link_utilization_pct: float = Field(ge=0, le=100)
    latency_ms: float = Field(ge=0)
    jitter_ms: float = Field(ge=0)
    packet_loss_pct: float = Field(ge=0, le=100)
    queue_drops: float = Field(ge=0)
    interface_errors: float = Field(ge=0)
    # connectivity-service health as seen from / at this device
    dns_success_pct: float = Field(default=100.0, ge=0, le=100)
    dhcp_success_pct: float = Field(default=100.0, ge=0, le=100)
    reachable: bool = True


METRIC_FIELDS = list(DeviceMetrics.model_fields.keys())


class DeviceTelemetry(BaseModel):
    device_id: str
    device_type: DeviceType
    metrics: DeviceMetrics


class GroundTruth(BaseModel):
    """Simulation-only labels. NEVER passed to agents (the orchestrator strips it)."""

    scenario: str
    root_device: Optional[str] = None
    root_link: Optional[List[str]] = None
    affected_devices: List[str] = Field(default_factory=list)
    severity: float = 0.0


class TelemetrySnapshot(BaseModel):
    """All device readings for one point in time."""

    snapshot_id: str = "snap-0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    devices: List[DeviceTelemetry]
    ground_truth: Optional[GroundTruth] = None

    def without_ground_truth(self) -> "TelemetrySnapshot":
        return self.model_copy(update={"ground_truth": None})

    def get(self, device_id: str) -> Optional[DeviceTelemetry]:
        for d in self.devices:
            if d.device_id == device_id:
                return d
        return None

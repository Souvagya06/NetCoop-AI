"""pytest config: puts backend/ on sys.path and provides hand-built (non-random) snapshots."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.connectivity_agent.topology import default_topology  # noqa: E402
from protocols.telemetry_schema import DeviceMetrics, DeviceTelemetry, DeviceType, TelemetrySnapshot  # noqa: E402

HEALTHY = dict(cpu_utilization_pct=25, memory_utilization_pct=40, link_utilization_pct=35, latency_ms=10, jitter_ms=2,
               packet_loss_pct=0.1, queue_drops=2, interface_errors=0, dns_success_pct=100, dhcp_success_pct=100, reachable=True)


def build_snapshot(overrides: dict | None = None, snapshot_id: str = "test") -> TelemetrySnapshot:
    """All-healthy snapshot; `overrides` = {device_id: {metric: value}}."""
    topo, overrides = default_topology(), overrides or {}
    devices = []
    for d in topo.device_ids():
        m = {**HEALTHY, **overrides.get(d, {})}
        devices.append(DeviceTelemetry(device_id=d, device_type=DeviceType(topo.type_of(d)), metrics=DeviceMetrics(**m)))
    return TelemetrySnapshot(snapshot_id=snapshot_id, devices=devices)


@pytest.fixture
def make_snapshot():
    return build_snapshot


@pytest.fixture
def topology():
    return default_topology()

"""Synthetic telemetry generator."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from agents.connectivity_agent.topology import NetworkTopology, default_topology
from data_generator.metric_distributions import apply_profile, degrade, finalize, sample_normal_metrics
from data_generator.scenarios import FAULT_PROFILES, PROPAGATION, SCENARIOS, TARGET_TYPES
from protocols.telemetry_schema import DeviceMetrics, DeviceTelemetry, DeviceType, GroundTruth, TelemetrySnapshot
from utils.helpers import clip


class TelemetryGenerator:
    def __init__(self, seed: Optional[int] = None, topology: Optional[NetworkTopology] = None) -> None:
        self.rng = np.random.default_rng(seed)
        self.topology = topology or default_topology()
        self._counter = 0

    # ---- public --------------------------------------------------------
    def generate_snapshot(self, scenario: str = "normal", snapshot_id: Optional[str] = None) -> TelemetrySnapshot:
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario '{scenario}'. Valid: {SCENARIOS}")
        self._counter += 1
        snapshot_id = snapshot_id or f"snap-{self._counter:05d}"
        topo = self.topology
        metrics: Dict[str, Dict[str, float]] = {d: sample_normal_metrics(self.rng, topo.type_of(d)) for d in topo.device_ids()}

        if scenario == "normal":
            truth = GroundTruth(scenario="normal")
        elif scenario == "link_failure":
            truth = self._link_failure(metrics)
        elif scenario == "dns_failure":
            truth = self._service_failure(metrics, "dns")
        elif scenario == "dhcp_failure":
            truth = self._service_failure(metrics, "dhcp")
        else:
            truth = self._device_fault(scenario, metrics)

        devices = [
            DeviceTelemetry(device_id=d, device_type=DeviceType(topo.type_of(d)), metrics=DeviceMetrics(**finalize(m)))
            for d, m in metrics.items()
        ]
        return TelemetrySnapshot(snapshot_id=snapshot_id, devices=devices, ground_truth=truth)

    def generate_batch(self, scenario: str, n: int) -> List[TelemetrySnapshot]:
        return [self.generate_snapshot(scenario) for _ in range(n)]

    # ---- fault injection -----------------------------------------------
    def _severity(self) -> float:
        return float(self.rng.uniform(0.15, 1.0))

    def _device_fault(self, scenario: str, metrics: Dict[str, Dict[str, float]]) -> GroundTruth:
        topo, rng = self.topology, self.rng
        sev = self._severity()
        candidates = topo.devices_of_type(*TARGET_TYPES[scenario])
        root = str(rng.choice(candidates))
        apply_profile(metrics[root], FAULT_PROFILES[scenario], sev, rng)
        affected = [root]
        factor = PROPAGATION[scenario]
        if factor > 0:
            for d in topo.downstream(root):
                degrade(metrics[d], factor, sev, rng)
                affected.append(d)
        return GroundTruth(scenario=scenario, root_device=root, affected_devices=affected, severity=round(sev, 3))

    def _link_failure(self, metrics: Dict[str, Dict[str, float]]) -> GroundTruth:
        topo, rng = self.topology, self.rng
        sev = self._severity()
        child = str(rng.choice(topo.devices_of_type("switch", "access_point")))
        parent = topo.parent(child)
        subtree = [child] + topo.downstream(child)
        for d in subtree:  # probes time out: no valid measurements behind the cut
            metrics[d].update(reachable=False, latency_ms=2000.0, jitter_ms=0.0, packet_loss_pct=100.0)
        metrics[child]["interface_errors"] = 30 + 470 * sev
        return GroundTruth(scenario="link_failure", root_device=child, root_link=[parent, child], affected_devices=subtree, severity=round(sev, 3))

    def _service_failure(self, metrics: Dict[str, Dict[str, float]], service: str) -> GroundTruth:
        topo, rng = self.topology, self.rng
        sev = self._severity()
        key = f"{service}_success_pct"
        targets = topo.device_ids() if service == "dns" else topo.devices_of_type("switch", "access_point")
        affected = []
        for d in targets:
            metrics[d][key] = clip(100 - 85 * sev + float(rng.normal(0, 6)), 0, 100)
            if metrics[d][key] < 90:
                affected.append(d)
        return GroundTruth(scenario=f"{service}_failure", root_device=topo.server_with_role(service), affected_devices=affected, severity=round(sev, 3))

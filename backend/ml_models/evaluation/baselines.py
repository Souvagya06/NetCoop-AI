"""Diagnostic baselines for ablation study.

Three baselines to compare against the full multi-agent system:

1. RuleOnlyDiagnoser  – disables Isolation Forest; uses rule engine only.
2. MLOnlyDiagnoser    – disables rule thresholds; uses IF anomaly score only.
3. MaxSeverityBaseline – returns the highest-severity finding (no correlation).
4. SingleAgentBaseline – only the Performance Agent feeds correlation.

All implement the same interface: diagnose(snapshot) → dict with at least:
  root_cause: {code, label, confidence}
  evidence_rounds: int
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from typing import Any, Dict, List, Optional

from agents.connectivity_agent.agent import ConnectivityAgent
from agents.correlation_agent.agent import CorrelationAgent
from agents.correlation_agent import correlation_engine as eng
from agents.infrastructure_agent.agent import InfrastructureAgent
from agents.performance_agent.agent import PerformanceAgent
from agents.reporting_agent.agent import ReportingAgent
from orchestrator.agent_registry import AgentRegistry
from orchestrator.orchestrator import Orchestrator
from protocols.message_schema import AgentMessage, MessageType, Status
from protocols.telemetry_schema import TelemetrySnapshot


# ---------------------------------------------------------------------------
# Helper: build a registry with patched agents
# ---------------------------------------------------------------------------

def _make_registry(perf_agent=None, infra_agent=None, conn_agent=None) -> AgentRegistry:
    from agents.connectivity_agent.topology import default_topology
    topo = default_topology()
    reg = AgentRegistry(
        analysis={
            "performance_agent": perf_agent or PerformanceAgent(),
            "infrastructure_agent": infra_agent or InfrastructureAgent(),
            "connectivity_agent": conn_agent or ConnectivityAgent(topo),
        },
        correlation=CorrelationAgent(topo),
        reporting=ReportingAgent(),
    )
    return reg


# ---------------------------------------------------------------------------
# Patch helpers: monkey-patch detector so it always returns "no anomaly"
# or rules so they never fire.
# ---------------------------------------------------------------------------

class _NoMLDetector:
    """Replacement detector whose anomaly score is always 0."""
    available = False

    def score(self, X):
        import numpy as np
        return np.zeros(len(X))


class _NoRuleAgent:
    """Wraps an agent and replaces its findings with empty ones (rules silent)."""
    def __init__(self, inner):
        self._inner = inner
        self.name = inner.name

    def analyze(self, snapshot, incident_id):
        msg = self._inner.analyze(snapshot, incident_id)
        # Zero out all finding confidences so the rule engine contributes nothing.
        for f in msg.findings:
            f.confidence = 0.0
        return msg

    def handle_request(self, snapshot, incident_id, req):
        return self._inner.handle_request(snapshot, incident_id, req)


# ---------------------------------------------------------------------------
# 1. Rule-only diagnoser
# ---------------------------------------------------------------------------

class RuleOnlyDiagnoser:
    """Full pipeline but Isolation Forest models are disabled."""

    name = "rule_only"
    description = "Rule thresholds only; Isolation Forest disabled"

    def __init__(self) -> None:
        from agents.performance_agent import detector as perf_det
        from agents.infrastructure_agent import detector as infra_det

        # Temporarily replace detectors
        self._orig_perf_det = perf_det.detector
        self._orig_infra_det = infra_det.detector
        perf_det.detector = _NoMLDetector()
        infra_det.detector = _NoMLDetector()

        self._orch = Orchestrator(use_llm=False)

        # Restore
        perf_det.detector = self._orig_perf_det
        infra_det.detector = self._orig_infra_det

        # Rebuild after restore so the orchestrator uses patched versions at call time
        # by swapping at diagnose() time instead
        self._perf_det_mod = perf_det
        self._infra_det_mod = infra_det

    def diagnose(self, snapshot: TelemetrySnapshot) -> Dict[str, Any]:
        self._perf_det_mod.detector = _NoMLDetector()
        self._infra_det_mod.detector = _NoMLDetector()
        try:
            return self._orch.diagnose(snapshot)
        finally:
            self._perf_det_mod.detector = self._orig_perf_det
            self._infra_det_mod.detector = self._orig_infra_det


# ---------------------------------------------------------------------------
# 2. ML-only diagnoser (rules silenced, only IF anomaly score drives findings)
# ---------------------------------------------------------------------------

class MLOnlyDiagnoser:
    """Isolation Forest only; rule thresholds are silenced (findings have conf=0)."""

    name = "ml_only"
    description = "Isolation Forest anomaly scores only; rule thresholds silenced"

    def __init__(self) -> None:
        from agents.connectivity_agent.topology import default_topology
        topo = default_topology()

        perf = PerformanceAgent()
        infra = InfrastructureAgent()
        conn = ConnectivityAgent(topo)

        reg = AgentRegistry(
            analysis={
                "performance_agent": _NoRuleAgent(perf),
                "infrastructure_agent": _NoRuleAgent(infra),
                "connectivity_agent": _NoRuleAgent(conn),
            },
            correlation=CorrelationAgent(topo),
            reporting=ReportingAgent(),
        )
        self._orch = Orchestrator(topology=topo, registry=reg, use_llm=False)

    def diagnose(self, snapshot: TelemetrySnapshot) -> Dict[str, Any]:
        return self._orch.diagnose(snapshot)


# ---------------------------------------------------------------------------
# 3. Max-severity baseline (pick single highest-confidence finding, no correlation)
# ---------------------------------------------------------------------------

class MaxSeverityBaseline:
    """Returns the finding with highest confidence as the root cause — no
    multi-agent correlation, just a simple argmax.
    """

    name = "max_severity"
    description = "Pick highest-confidence finding from any agent (no correlation)"

    def __init__(self) -> None:
        self._perf = PerformanceAgent()
        self._infra = InfrastructureAgent()
        from agents.connectivity_agent.topology import default_topology
        self._conn = ConnectivityAgent(default_topology())

    def diagnose(self, snapshot: TelemetrySnapshot) -> Dict[str, Any]:
        clean = snapshot.without_ground_truth()
        iid = "BL-MAX"
        msgs = [
            self._perf.analyze(clean, iid),
            self._infra.analyze(clean, iid),
            self._conn.analyze(clean, iid),
        ]
        best_conf = 0.0
        best_code = "normal"
        best_label = "No incident (healthy / minor noise)"
        for msg in msgs:
            for f in msg.findings:
                if f.confidence > best_conf:
                    best_conf = f.confidence
                    best_code = f.code
                    best_label = f.description

        # Map finding code → hypothesis code (best effort)
        hyp_code = best_code
        if best_code == "device_overload":
            hyp_code = "cpu_overload"
        elif best_code == "memory_pressure":
            hyp_code = "memory_overload"

        return {
            "root_cause": {"code": hyp_code, "label": best_label, "confidence": round(best_conf, 3)},
            "evidence_rounds": 0,
        }


# ---------------------------------------------------------------------------
# 4. Single-agent baseline (Performance Agent only → correlation)
# ---------------------------------------------------------------------------

class SingleAgentBaseline:
    """Only the Performance Agent feeds the Correlation Agent."""

    name = "single_agent"
    description = "Performance Agent only → correlation (infrastructure & connectivity absent)"

    def __init__(self) -> None:
        from agents.connectivity_agent.topology import default_topology
        topo = default_topology()
        reg = AgentRegistry(
            analysis={"performance_agent": PerformanceAgent()},
            correlation=CorrelationAgent(topo),
            reporting=ReportingAgent(),
        )
        self._orch = Orchestrator(topology=topo, registry=reg, use_llm=False)

    def diagnose(self, snapshot: TelemetrySnapshot) -> Dict[str, Any]:
        return self._orch.diagnose(snapshot)


# ---------------------------------------------------------------------------
# 5. Full multi-agent system (the production system, for comparison)
# ---------------------------------------------------------------------------

class FullSystem:
    name = "full_system"
    description = "All five agents, full correlation (production configuration)"

    def __init__(self) -> None:
        self._orch = Orchestrator(use_llm=False)

    def diagnose(self, snapshot: TelemetrySnapshot) -> Dict[str, Any]:
        return self._orch.diagnose(snapshot)


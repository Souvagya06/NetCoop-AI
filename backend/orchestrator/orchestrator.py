"""Hybrid orchestration.

The orchestrator owns the workflow; agents never call each other.
  1. fan-out : analysis agents run in parallel on the same snapshot
  2. fan-in  : every reply is validated against the protocol
  3. correlate: the correlation agent may ask (via the orchestrator) for more
                evidence, at most MAX_EVIDENCE_ROUNDS times
  4. report  : the reporting agent writes the final report
A failing/slow agent never stops the diagnosis; it is recorded in `limitations`.
"""
from __future__ import annotations

import itertools
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import config
from agents.connectivity_agent.topology import NetworkTopology, default_topology
from orchestrator.agent_registry import AgentRegistry, build_default_registry
from protocols.message_schema import AgentMessage, MessageType, Status
from protocols.telemetry_schema import TelemetrySnapshot
from protocols.validator import ProtocolError, validate_message, validate_snapshot
from utils.logger import get_logger

log = get_logger("orchestrator")


class Orchestrator:
    def __init__(self, topology: Optional[NetworkTopology] = None, registry: Optional[AgentRegistry] = None,
                 max_rounds: int = config.MAX_EVIDENCE_ROUNDS, agent_timeout: float = config.AGENT_TIMEOUT_S, use_llm: bool = True) -> None:
        self.topology = topology or default_topology()
        self.registry = registry or build_default_registry(self.topology)
        self.max_rounds = max_rounds
        self.agent_timeout = agent_timeout
        self.use_llm = use_llm
        self._counter = itertools.count(1)
        self._lock = threading.Lock()

    def _next_id(self) -> str:
        with self._lock:
            return f"NC-{next(self._counter):03d}"

    @staticmethod
    def _error_message(sender: str, incident_id: str, reason: str) -> AgentMessage:
        return AgentMessage(incident_id=incident_id, sender=sender, message_type=MessageType.ERROR, status=Status.HEALTHY,
                            limitations=[f"{sender} unavailable: {reason}"])

    def diagnose(self, snapshot: Any) -> Dict[str, Any]:
        t0 = time.perf_counter()
        snapshot = validate_snapshot(snapshot)
        clean = snapshot.without_ground_truth()  # agents must never see simulation labels
        incident_id = self._next_id()
        timeline: List[Dict[str, Any]] = []

        def event(actor: str, kind: str, detail: str) -> None:
            timeline.append({"t_ms": round((time.perf_counter() - t0) * 1000, 1), "actor": actor, "event": kind, "detail": detail})

        event("orchestrator", "incident_opened", f"{incident_id} for snapshot {snapshot.snapshot_id} ({len(snapshot.devices)} devices)")

        # 1+2. fan-out / fan-in --------------------------------------------------
        messages: List[AgentMessage] = []
        names = self.registry.analysis_names()
        pool = ThreadPoolExecutor(max_workers=max(1, len(names)))
        futures = {n: pool.submit(self.registry.analysis[n].analyze, clean, incident_id) for n in names}
        event("orchestrator", "fan_out", f"dispatched telemetry to {', '.join(names)}")
        for n, fut in futures.items():
            try:
                msg = validate_message(fut.result(timeout=self.agent_timeout), expected_sender=n, expected_incident=incident_id)
                event(n, "finding", f"status={msg.status.value}, {len(msg.findings)} finding(s), evidence={msg.confidence:.2f}")
            except Exception as exc:  # timeout, crash, or protocol violation
                reason = f"{type(exc).__name__}: {exc}" if not isinstance(exc, ProtocolError) else str(exc)
                msg = self._error_message(n, incident_id, reason or "timeout")
                event(n, "error", msg.limitations[0])
                log.warning("%s failed: %s", n, reason)
            messages.append(msg)
        pool.shutdown(wait=False, cancel_futures=True)

        # 3. correlation with bounded evidence requests ---------------------------
        corr_agent = self.registry.correlation
        asked: set = set()
        diagnosis = corr_agent.analyze(incident_id, messages, allow_request=self.max_rounds > 0, asked=asked)
        while diagnosis.message_type == MessageType.REQUEST_EVIDENCE and len(asked) < self.max_rounds:
            req = diagnosis.request
            event("correlation_agent", "request_evidence", f"asks {req.to} about {req.device_id}: {req.question}")
            asked.add(req.to)
            target = self.registry.analysis.get(req.to)
            try:
                reply = validate_message(target.handle_request(clean, incident_id, req), expected_sender=req.to, expected_incident=incident_id)
                event(req.to, "evidence_reply", f"detailed signals: {reply.evidence.get('detailed_signals')}")
                messages.append(reply)
            except Exception as exc:
                event(req.to, "error", f"evidence request failed: {exc}")
                messages.append(self._error_message(req.to, incident_id, f"evidence request failed: {exc}"))
            diagnosis = corr_agent.analyze(incident_id, messages, allow_request=len(asked) < self.max_rounds, asked=asked)
        if diagnosis.message_type == MessageType.REQUEST_EVIDENCE:  # safety net
            diagnosis = corr_agent.analyze(incident_id, messages, allow_request=False, asked=asked)
        ev = diagnosis.evidence
        event("correlation_agent", "diagnosis", f"root cause={ev['root_cause']}, evidence={diagnosis.confidence:.2f}, root_device={ev.get('root_device')}")

        # 4. reporting ---------------------------------------------------------------
        report_msg = self.registry.reporting.analyze(incident_id, diagnosis, messages, clean, use_llm=self.use_llm)
        report = report_msg.evidence["report"]
        event("reporting_agent", "report", f"generated by {report['generated_by']}")

        result = {
            "incident_id": incident_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_id": snapshot.snapshot_id,
            "root_cause": {
                "code": ev["root_cause"], "label": ev["root_cause_label"], "confidence": round(diagnosis.confidence, 3),
                "incident_declared": ev["incident_declared"], "root_device": ev.get("root_device"), "root_link": ev.get("root_link"),
                "affected_devices": ev.get("affected_devices", []), "severity": diagnosis.status.value,
            },
            "agent_messages": [m.model_dump(mode="json") for m in messages],
            "correlation": diagnosis.model_dump(mode="json"),
            "report": report,
            "timeline": timeline,
            "evidence_rounds": len(asked),
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
            "ground_truth_simulation_only": snapshot.ground_truth.model_dump(mode="json") if snapshot.ground_truth else None,
        }
        log.info("%s -> %s (%.2f) in %.0f ms", incident_id, ev["root_cause"], diagnosis.confidence, result["duration_ms"])
        return result

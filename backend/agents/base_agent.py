"""Shared plumbing for the three analysis agents.

Agents NEVER import each other. They take a TelemetrySnapshot and return an
AgentMessage (protocols/message_schema.py)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from protocols.message_schema import AgentMessage, EvidenceRequest, Finding, Status, worst_status
from protocols.telemetry_schema import TelemetrySnapshot
from utils.helpers import clip01


class AnalysisAgent(ABC):
    name: str = "analysis_agent"
    description: str = ""

    @abstractmethod
    def analyze(self, snapshot: TelemetrySnapshot, incident_id: str, focus_device: Optional[str] = None) -> AgentMessage:
        """Analyse the snapshot. If `focus_device` is set, add a detailed per-signal breakdown for it."""

    def handle_request(self, snapshot: TelemetrySnapshot, incident_id: str, request: EvidenceRequest) -> AgentMessage:
        """Answer an evidence request routed by the orchestrator."""
        return self.analyze(snapshot, incident_id, focus_device=request.device_id)


# per_device: {device_id: {finding_code: (confidence, severity)}}
PerDevice = Dict[str, Dict[str, Tuple[float, Status]]]


def aggregate_findings(per_device: PerDevice, descriptions: Dict[str, str]) -> List[Finding]:
    """Collapse per-device results into one Finding per code."""
    by_code: Dict[str, Dict[str, Tuple[float, Status]]] = {}
    for dev, codes in per_device.items():
        for code, (conf, sev) in codes.items():
            by_code.setdefault(code, {})[dev] = (conf, sev)

    findings: List[Finding] = []
    for code, devs in by_code.items():
        scores = {d: round(clip01(c), 3) for d, (c, _) in devs.items()}
        top = max(scores, key=scores.get)
        findings.append(Finding(
            code=code,
            description=descriptions.get(code, code).format(device=top, n=len(devs)),
            severity=worst_status(s for _, s in devs.values()),
            devices=sorted(devs),
            device_scores=scores,
            confidence=scores[top],
        ))
    findings.sort(key=lambda f: f.confidence, reverse=True)
    return findings

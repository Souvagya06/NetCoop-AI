"""Inter-agent communication protocol (the 'interoperability' contract).

Every agent returns an AgentMessage. Agents never import each other; they only
share this schema. `confidence` is an *evidence score* in [0, 1] built from rule
strength (and an Isolation Forest score where available). It is NOT a calibrated
probability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field


class Status(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


STATUS_RANK = {Status.HEALTHY: 0, Status.WARNING: 1, Status.CRITICAL: 2}


def worst_status(statuses: Iterable[Status]) -> Status:
    worst = Status.HEALTHY
    for s in statuses:
        if STATUS_RANK[s] > STATUS_RANK[worst]:
            worst = s
    return worst


class MessageType(str, Enum):
    FINDING = "finding"                    # analysis agent -> orchestrator
    REQUEST_EVIDENCE = "request_evidence"  # correlation agent -> orchestrator -> agent
    DIAGNOSIS = "diagnosis"                # correlation agent final output
    REPORT = "report"                      # reporting agent final output
    ERROR = "error"                        # orchestrator-generated when an agent fails


class Finding(BaseModel):
    code: str                                        # e.g. "device_overload"
    description: str
    severity: Status = Status.WARNING
    devices: List[str] = Field(default_factory=list)  # all devices involved/affected
    # devices implicated as the *source*, with a per-device evidence score
    device_scores: Dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class EvidenceRequest(BaseModel):
    to: str                      # agent name
    check: str                   # e.g. "detailed_signals"
    device_id: Optional[str] = None
    question: str = ""


class AgentMessage(BaseModel):
    incident_id: str
    sender: str
    message_type: MessageType = MessageType.FINDING
    status: Status = Status.HEALTHY
    findings: List[Finding] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)
    request: Optional[EvidenceRequest] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

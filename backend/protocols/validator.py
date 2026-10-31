"""Protocol validation. The orchestrator validates every message before routing it."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from protocols.message_schema import AgentMessage, MessageType
from protocols.telemetry_schema import TelemetrySnapshot


class ProtocolError(ValueError):
    """Raised when a message or snapshot violates the protocol."""


def validate_message(
    raw: Any,
    expected_sender: Optional[str] = None,
    expected_incident: Optional[str] = None,
) -> AgentMessage:
    try:
        msg = raw if isinstance(raw, AgentMessage) else AgentMessage.model_validate(raw)
    except ValidationError as exc:
        raise ProtocolError(f"malformed agent message: {exc.errors()[:2]}") from exc

    if expected_sender and msg.sender != expected_sender:
        raise ProtocolError(f"sender mismatch: expected {expected_sender}, got {msg.sender}")
    if expected_incident and msg.incident_id != expected_incident:
        raise ProtocolError(f"incident mismatch: expected {expected_incident}, got {msg.incident_id}")
    if msg.message_type == MessageType.REQUEST_EVIDENCE and msg.request is None:
        raise ProtocolError("request_evidence message without a request payload")
    return msg


def validate_snapshot(raw: Any) -> TelemetrySnapshot:
    try:
        snap = raw if isinstance(raw, TelemetrySnapshot) else TelemetrySnapshot.model_validate(raw)
    except ValidationError as exc:
        raise ProtocolError(f"malformed telemetry snapshot: {exc.errors()[:2]}") from exc
    if not snap.devices:
        raise ProtocolError("snapshot contains no devices")
    ids = [d.device_id for d in snap.devices]
    if len(ids) != len(set(ids)):
        raise ProtocolError("duplicate device_id in snapshot")
    return snap

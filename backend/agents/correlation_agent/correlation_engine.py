"""Evidence-weighted hypothesis scoring.

For every candidate root cause we define:
  primary      the finding code that MUST be present (otherwise score = 0)
  base         fraction of the primary evidence kept even with no corroboration
  supporting   other findings that increase the score (weight)
  contradicting findings that suggest a different/more fundamental cause (weight)

score = primary_conf * (base + (1-base) * corroboration) * (1 - penalty)

Scores are evidence scores, not probabilities.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from protocols.message_schema import AgentMessage, MessageType, Status, STATUS_RANK

HYPOTHESES: Dict[str, dict] = {
    "network_congestion": dict(
        primary="network_congestion", base=0.6,
        supporting={"latency_spike": 0.4, "packet_loss": 0.4, "downstream_degradation": 0.3},
        contradicting={"device_overload": 0.35, "hardware_failure": 0.5, "interface_failure": 0.3, "link_failure": 0.5, "memory_pressure": 0.2},
    ),
    "latency_spike": dict(
        primary="latency_spike", base=0.6,
        supporting={"downstream_degradation": 0.2},
        contradicting={"network_congestion": 0.4, "device_overload": 0.4, "memory_pressure": 0.3, "hardware_failure": 0.5, "interface_failure": 0.3, "link_failure": 0.5, "packet_loss": 0.25},
    ),
    "packet_loss": dict(
        primary="packet_loss", base=0.6,
        supporting={"latency_spike": 0.3},
        contradicting={"interface_failure": 0.5, "hardware_failure": 0.5, "link_failure": 0.5, "network_congestion": 0.3, "device_overload": 0.3, "latency_spike": 0.25},
    ),
    "cpu_overload": dict(
        primary="device_overload", base=0.6,
        supporting={"network_congestion": 0.3, "latency_spike": 0.3, "packet_loss": 0.2, "downstream_degradation": 0.3},
        contradicting={"hardware_failure": 0.6, "memory_pressure": 0.25},
    ),
    "memory_overload": dict(
        primary="memory_pressure", base=0.6,
        supporting={"latency_spike": 0.2, "packet_loss": 0.1},
        contradicting={"hardware_failure": 0.6, "device_overload": 0.3},
    ),
    "hardware_failure": dict(
        primary="hardware_failure", base=0.6,
        supporting={"device_overload": 0.4, "memory_pressure": 0.4, "packet_loss": 0.4, "latency_spike": 0.3, "downstream_degradation": 0.3},
        contradicting={},
    ),
    "interface_failure": dict(
        primary="interface_failure", base=0.6,
        supporting={"packet_loss": 0.5, "latency_spike": 0.2},
        contradicting={"hardware_failure": 0.7, "device_overload": 0.3},
    ),
    "link_failure": dict(primary="link_failure", base=0.9, supporting={}, contradicting={}),
    "dns_failure": dict(primary="dns_failure", base=1.0, supporting={}, contradicting={}),
    "dhcp_failure": dict(primary="dhcp_failure", base=1.0, supporting={}, contradicting={}),
}

LABELS = {
    "normal": "No incident (healthy / minor noise)",
    "undetermined": "Undetermined (analysis agents unavailable)",
    "network_congestion": "Network congestion",
    "latency_spike": "Latency spike",
    "packet_loss": "Packet loss",
    "cpu_overload": "Device CPU overload",
    "memory_overload": "Device memory overload",
    "hardware_failure": "Hardware failure",
    "interface_failure": "Interface failure",
    "link_failure": "Link failure",
    "dns_failure": "DNS failure",
    "dhcp_failure": "DHCP failure",
}

# hypotheses whose effect spreads to everything behind the root device
PROPAGATING = {"network_congestion", "cpu_overload", "hardware_failure", "latency_spike"}

# Tie-break: how detailed per-signal strengths (0..1) favour/disfavour a hypothesis.
TIEBREAK: Dict[str, Dict[str, float]] = {
    "hardware_failure": {"interface_errors": 1.0, "packet_loss": 0.5, "memory": 0.3},
    "cpu_overload": {"cpu": 1.0, "interface_errors": -0.6, "packet_loss": -0.2},
    "memory_overload": {"memory": 1.0, "cpu": -0.3, "interface_errors": -0.5},
    "network_congestion": {"link_util": 1.0, "cpu": -0.3, "interface_errors": -0.4},
    "interface_failure": {"interface_errors": 1.0, "cpu": -0.5, "link_util": -0.3},
    "latency_spike": {"latency": 1.0, "link_util": -0.4, "cpu": -0.3},
    "packet_loss": {"packet_loss": 1.0, "interface_errors": -0.3, "cpu": -0.3},
}
TIEBREAK_WEIGHT = 0.15

SIGNAL_OWNER = {
    "cpu": "infrastructure_agent", "memory": "infrastructure_agent",
    "queue_drops": "infrastructure_agent", "interface_errors": "infrastructure_agent",
    "latency": "performance_agent", "jitter": "performance_agent",
    "packet_loss": "performance_agent", "link_util": "performance_agent",
}


def collect_findings(messages: Iterable[AgentMessage]) -> Dict[str, dict]:
    """Merge all agents' findings by code (max confidence, union of devices)."""
    by_code: Dict[str, dict] = {}
    for m in messages:
        if m.message_type == MessageType.ERROR:
            continue
        for f in m.findings:
            info = by_code.setdefault(f.code, {"confidence": 0.0, "severity": Status.HEALTHY, "devices": set(), "device_scores": defaultdict(float), "senders": set()})
            info["confidence"] = max(info["confidence"], f.confidence)
            if STATUS_RANK[f.severity] > STATUS_RANK[info["severity"]]:
                info["severity"] = f.severity
            info["devices"].update(f.devices)
            for d, s in f.device_scores.items():
                info["device_scores"][d] = max(info["device_scores"][d], s)
            info["senders"].add(m.sender)
    return by_code


def score_hypotheses(by_code: Dict[str, dict]) -> Dict[str, dict]:
    conf = {c: v["confidence"] for c, v in by_code.items()}
    out: Dict[str, dict] = {}
    for name, h in HYPOTHESES.items():
        primary = conf.get(h["primary"], 0.0)
        if primary <= 0:
            continue
        sup_total = sum(h["supporting"].values())
        corroboration = sum(w * conf.get(c, 0.0) for c, w in h["supporting"].items()) / sup_total if sup_total else 0.0
        penalty = min(0.9, sum(w * conf.get(c, 0.0) for c, w in h["contradicting"].items()))
        score = primary * (h["base"] + (1 - h["base"]) * corroboration) * (1 - penalty)
        out[name] = {
            "score": round(score, 4),
            "primary_confidence": round(primary, 3),
            "corroboration": round(corroboration, 3),
            "penalty": round(penalty, 3),
            "supporting_present": sorted(c for c in h["supporting"] if conf.get(c, 0) > 0),
            "contradicting_present": sorted(c for c in h["contradicting"] if conf.get(c, 0) > 0),
        }
    return out


def gather_signals(messages: Iterable[AgentMessage]) -> Dict[str, float]:
    signals: Dict[str, float] = {}
    for m in messages:
        sig = m.evidence.get("detailed_signals") if m.evidence else None
        if sig:
            signals.update(sig)
    return signals


def apply_tiebreak(scored: Dict[str, dict], contested: List[str], signals: Dict[str, float]) -> None:
    """Nudge contested hypotheses using the detailed signals returned by agents."""
    for name in contested:
        weights = {s: w for s, w in TIEBREAK.get(name, {}).items() if s in signals}
        if not weights:
            continue
        tb = sum(w * signals[s] for s, w in weights.items()) / sum(abs(w) for w in weights.values())
        scored[name]["tiebreak"] = round(tb, 3)
        scored[name]["score"] = round(max(0.0, scored[name]["score"] + TIEBREAK_WEIGHT * tb), 4)

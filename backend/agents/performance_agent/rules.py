"""Heuristic thresholds (warn, crit). These are illustrative, not vendor standards."""
from __future__ import annotations

from typing import Dict, Tuple

from protocols.message_schema import Status
from utils.helpers import ramp

THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "latency_ms": (100.0, 250.0),
    "jitter_ms": (30.0, 60.0),
    "packet_loss_pct": (1.0, 5.0),
    "link_utilization_pct": (80.0, 92.0),
    "queue_drops": (300.0, 2000.0),
}

# signal name -> (metric, 'normal-ish' level, 'critical' level) for detailed 0..1 strengths
DETAIL_RANGES = {
    "latency": ("latency_ms", 25.0, 250.0),
    "jitter": ("jitter_ms", 6.0, 60.0),
    "packet_loss": ("packet_loss_pct", 0.3, 5.0),
    "link_util": ("link_utilization_pct", 50.0, 92.0),
}

DESCRIPTIONS = {
    "latency_spike": "Abnormal latency/jitter on {n} device(s); worst: {device}.",
    "packet_loss": "Significant packet loss on {n} device(s); worst: {device}.",
    "network_congestion": "High link utilisation with queue drops/latency on {n} device(s); worst: {device}.",
    "statistical_anomaly": "Isolation Forest flags unusual performance pattern on {n} device(s); e.g. {device}.",
}


def level(metric: str, value: float) -> int:
    warn, crit = THRESHOLDS[metric]
    return 2 if value >= crit else 1 if value >= warn else 0


def strength(metric: str, value: float) -> float:
    warn, crit = THRESHOLDS[metric]
    return ramp(value, warn, crit)


def _sev(lv: int) -> Status:
    return Status.CRITICAL if lv >= 2 else Status.WARNING


def evaluate_device(m: Dict[str, float]) -> Dict[str, Tuple[float, Status]]:
    lv = {k: level(k, m[k]) for k in THRESHOLDS}
    st = {k: strength(k, m[k]) for k in THRESHOLDS}
    out: Dict[str, Tuple[float, Status]] = {}

    delay_lv = max(lv["latency_ms"], lv["jitter_ms"])
    if delay_lv >= 1:
        out["latency_spike"] = (0.4 + 0.6 * max(st["latency_ms"], st["jitter_ms"]), _sev(delay_lv))
    if lv["packet_loss_pct"] >= 1:
        out["packet_loss"] = (0.4 + 0.6 * st["packet_loss_pct"], _sev(lv["packet_loss_pct"]))
    if lv["link_utilization_pct"] >= 1 and (lv["queue_drops"] >= 1 or lv["latency_ms"] >= 1):
        s = (st["link_utilization_pct"] + max(st["queue_drops"], st["latency_ms"])) / 2
        out["network_congestion"] = (0.4 + 0.6 * s, _sev(max(lv["link_utilization_pct"], lv["queue_drops"], lv["latency_ms"])))
    return out


def detailed_signals(m: Dict[str, float]) -> Dict[str, float]:
    return {name: round(ramp(m[metric], lo, hi), 3) for name, (metric, lo, hi) in DETAIL_RANGES.items()}

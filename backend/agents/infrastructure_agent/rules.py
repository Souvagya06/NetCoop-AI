from __future__ import annotations

from typing import Dict, Tuple

from protocols.message_schema import Status
from utils.helpers import ramp

THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "cpu_utilization_pct": (75.0, 92.0),
    "memory_utilization_pct": (80.0, 93.0),
    "queue_drops": (500.0, 3000.0),
    "interface_errors": (25.0, 150.0),
}

DETAIL_RANGES = {
    "cpu": ("cpu_utilization_pct", 30.0, 92.0),
    "memory": ("memory_utilization_pct", 50.0, 93.0),
    "queue_drops": ("queue_drops", 30.0, 3000.0),
    "interface_errors": ("interface_errors", 2.0, 150.0),
}

DESCRIPTIONS = {
    "device_overload": "CPU utilisation critically/abnormally high on {n} device(s); worst: {device}.",
    "memory_pressure": "Memory utilisation abnormally high on {n} device(s); worst: {device}.",
    "hardware_failure": "Multiple internal health indicators degraded together (CPU/memory/queues/interface errors) on {device}.",
    "interface_failure": "Elevated interface errors without matching resource exhaustion on {n} device(s); worst: {device}.",
    "statistical_anomaly": "Isolation Forest flags unusual device-health pattern on {n} device(s); e.g. {device}.",
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

    if lv["cpu_utilization_pct"] >= 1:
        out["device_overload"] = (0.4 + 0.6 * st["cpu_utilization_pct"], _sev(lv["cpu_utilization_pct"]))
    if lv["memory_utilization_pct"] >= 1:
        out["memory_pressure"] = (0.4 + 0.6 * st["memory_utilization_pct"], _sev(lv["memory_utilization_pct"]))

    if lv["interface_errors"] >= 1:
        others = [k for k in ("cpu_utilization_pct", "memory_utilization_pct", "queue_drops") if lv[k] >= 1]
        if len(others) >= 2:  # errors AND at least two other degraded health indicators
            s = (st["interface_errors"] + sum(st[k] for k in others)) / (1 + len(others))
            out["hardware_failure"] = (0.4 + 0.6 * s, Status.CRITICAL)
        else:
            out["interface_failure"] = (0.4 + 0.6 * st["interface_errors"], _sev(lv["interface_errors"]))
    return out


def detailed_signals(m: Dict[str, float]) -> Dict[str, float]:
    return {name: round(ramp(m[metric], lo, hi), 3) for name, (metric, lo, hi) in DETAIL_RANGES.items()}

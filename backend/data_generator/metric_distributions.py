"""Statistical models for *healthy* device behaviour plus helpers to inject faults."""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from utils.helpers import clip

# mean values per device type (cpu %, mem %, link %, latency ms)
BASELINES: Dict[str, Dict[str, float]] = {
    "router": {"cpu": 30, "mem": 45, "link": 45, "lat": 8},
    "switch": {"cpu": 25, "mem": 40, "link": 40, "lat": 6},
    "access_point": {"cpu": 20, "mem": 35, "link": 30, "lat": 14},
    "server": {"cpu": 35, "mem": 55, "link": 25, "lat": 10},
}

# Probability that a *healthy* device shows a harmless transient spike. This creates
# realistic false-positive pressure so evaluation is not trivially perfect.
BENIGN_SPIKE_PROB = 0.01


def sample_normal_metrics(rng: np.random.Generator, device_type: str) -> Dict[str, float]:
    b = BASELINES[device_type]
    m = {
        "cpu_utilization_pct": clip(rng.normal(b["cpu"], 8), 2, 70),
        "memory_utilization_pct": clip(rng.normal(b["mem"], 8), 10, 75),
        "link_utilization_pct": clip(rng.normal(b["link"], 12), 1, 75),
        "latency_ms": clip(rng.lognormal(np.log(b["lat"]), 0.35), 1, 90),
        "jitter_ms": clip(rng.gamma(2.0, 1.2), 0.1, 20),
        "packet_loss_pct": clip(rng.exponential(0.12), 0.0, 1.5),
        "queue_drops": float(rng.poisson(3)),
        "interface_errors": float(rng.poisson(0.6)),
        "dns_success_pct": min(100.0, float(rng.normal(99.6, 0.6))),
        "dhcp_success_pct": min(100.0, float(rng.normal(99.6, 0.6))),
        "reachable": True,
    }
    if rng.random() < BENIGN_SPIKE_PROB:
        kind = int(rng.integers(0, 5))
        if kind == 0:
            m["cpu_utilization_pct"] = float(rng.uniform(72, 90))
        elif kind == 1:
            m["latency_ms"] = float(rng.uniform(60, 140))
        elif kind == 2:
            m["link_utilization_pct"] = float(rng.uniform(75, 90))
        elif kind == 3:
            m["packet_loss_pct"] = float(rng.uniform(0.8, 2.0))
        else:
            m["queue_drops"] = float(rng.uniform(100, 400))
    return m


def apply_profile(metrics: Dict[str, float], profile: Dict[str, Tuple[float, float]], severity: float, rng: np.random.Generator) -> None:
    """Overwrite metrics with a value interpolated between a mild and a severe level."""
    for key, (mild, severe) in profile.items():
        value = mild + (severe - mild) * severity
        metrics[key] = value * float(rng.normal(1.0, 0.05))


def degrade(metrics: Dict[str, float], factor: float, severity: float, rng: np.random.Generator) -> None:
    """Mild knock-on degradation for devices downstream of a faulty device."""
    metrics["latency_ms"] += factor * severity * float(rng.uniform(15, 120))
    metrics["packet_loss_pct"] += factor * severity * float(rng.uniform(0.3, 3.0))
    metrics["jitter_ms"] += factor * severity * float(rng.uniform(3, 25))


def finalize(metrics: Dict[str, float]) -> Dict[str, float]:
    out = dict(metrics)
    for k in ("cpu_utilization_pct", "memory_utilization_pct", "link_utilization_pct", "packet_loss_pct", "dns_success_pct", "dhcp_success_pct"):
        out[k] = round(clip(float(out[k]), 0.0, 100.0), 2)
    for k in ("latency_ms", "jitter_ms"):
        out[k] = round(max(0.0, float(out[k])), 2)
    for k in ("queue_drops", "interface_errors"):
        out[k] = float(int(round(max(0.0, float(out[k])))))
    out["reachable"] = bool(out["reachable"])
    return out

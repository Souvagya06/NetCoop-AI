"""Rolling per-device telemetry buffer.

Accumulates the last N snapshots so that agents can consider *trends*
(is CPU rising or falling?) and *persistence* (has latency been high for
multiple consecutive readings?), not just the most recent value.

Thread-safe for concurrent diagnose() + live-telemetry reads.
"""
from __future__ import annotations

import threading
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional

from protocols.telemetry_schema import DeviceMetrics, TelemetrySnapshot

# Numeric metric names used for trend / persistence computation
_NUMERIC_METRICS = [
    "cpu_utilization_pct",
    "memory_utilization_pct",
    "link_utilization_pct",
    "latency_ms",
    "jitter_ms",
    "packet_loss_pct",
    "queue_drops",
    "interface_errors",
    "dns_success_pct",
    "dhcp_success_pct",
]

DEFAULT_WINDOW_SIZE = 10  # keep last 10 snapshots per device


class DeviceWindow:
    """Rolling statistics for a single device."""

    def __init__(self, device_id: str, window_size: int = DEFAULT_WINDOW_SIZE) -> None:
        self.device_id = device_id
        self.window_size = window_size
        self._readings: deque[DeviceMetrics] = deque(maxlen=window_size)
        self._timestamps: deque[datetime] = deque(maxlen=window_size)

    # ------------------------------------------------------------------
    def push(self, metrics: DeviceMetrics, timestamp: datetime) -> None:
        self._readings.append(metrics)
        self._timestamps.append(timestamp)

    @property
    def length(self) -> int:
        return len(self._readings)

    # ------------------------------------------------------------------
    def _values(self, metric: str) -> List[float]:
        return [getattr(r, metric, 0.0) for r in self._readings]

    def trend(self, metric: str) -> float:
        """Simple linear slope (units/reading). Positive = rising.
        Returns 0.0 if fewer than 2 readings.
        """
        vals = self._values(metric)
        n = len(vals)
        if n < 2:
            return 0.0
        # Least-squares slope using index as x
        mean_x = (n - 1) / 2.0
        mean_y = sum(vals) / n
        num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(vals))
        den = sum((i - mean_x) ** 2 for i in range(n))
        return round(num / den if den else 0.0, 4)

    def persistence(self, metric: str, threshold: float, above: bool = True) -> float:
        """Fraction of readings where metric is above/below threshold.
        Returns a [0, 1] score; 1.0 means every reading in the window triggered.
        """
        vals = self._values(metric)
        if not vals:
            return 0.0
        count = sum(1 for v in vals if (v >= threshold if above else v <= threshold))
        return round(count / len(vals), 3)

    def rate_of_change(self, metric: str) -> float:
        """Absolute change between the oldest and newest reading, normalised by
        the number of steps. Returns 0.0 with fewer than 2 readings.
        """
        vals = self._values(metric)
        if len(vals) < 2:
            return 0.0
        return round((vals[-1] - vals[0]) / (len(vals) - 1), 4)

    def summary(self) -> Dict[str, object]:
        """Return a dict suitable for embedding into agent evidence."""
        if not self._readings:
            return {"length": 0}
        latest = self._readings[-1]
        out: Dict[str, object] = {
            "length": self.length,
            "window_size": self.window_size,
        }
        for m in _NUMERIC_METRICS:
            out[f"{m}_trend"] = self.trend(m)
            out[f"{m}_roc"] = self.rate_of_change(m)
        # Persistence at commonly-used alert thresholds
        out["cpu_persistence_80"] = self.persistence("cpu_utilization_pct", 80)
        out["latency_persistence_80"] = self.persistence("latency_ms", 80)
        out["packet_loss_persistence_1"] = self.persistence("packet_loss_pct", 1.0)
        out["link_util_persistence_80"] = self.persistence("link_utilization_pct", 80)
        return out


class TelemetryBuffer:
    """Thread-safe store of per-device rolling windows."""

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE) -> None:
        self.window_size = window_size
        self._windows: Dict[str, DeviceWindow] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def push(self, snapshot: TelemetrySnapshot) -> None:
        """Record every device's metrics from *snapshot*."""
        ts = snapshot.timestamp
        with self._lock:
            for dev in snapshot.devices:
                if dev.device_id not in self._windows:
                    self._windows[dev.device_id] = DeviceWindow(dev.device_id, self.window_size)
                self._windows[dev.device_id].push(dev.metrics, ts)

    def get_window(self, device_id: str) -> Optional[DeviceWindow]:
        with self._lock:
            return self._windows.get(device_id)

    def summaries(self) -> Dict[str, Dict[str, object]]:
        """Return a {device_id: summary_dict} for all devices."""
        with self._lock:
            return {did: w.summary() for did, w in self._windows.items()}

    def device_ids(self) -> List[str]:
        with self._lock:
            return list(self._windows.keys())


# ---------------------------------------------------------------------------
# Module-level singleton shared by diagnosis_service and the telemetry route.
# ---------------------------------------------------------------------------
_buffer: Optional[TelemetryBuffer] = None
_buffer_lock = threading.Lock()


def get_buffer(window_size: int = DEFAULT_WINDOW_SIZE) -> TelemetryBuffer:
    global _buffer
    with _buffer_lock:
        if _buffer is None:
            _buffer = TelemetryBuffer(window_size)
        return _buffer


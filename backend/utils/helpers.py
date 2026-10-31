from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def clip01(value: float) -> float:
    return clip(float(value), 0.0, 1.0)


def ramp(value: float, start: float, end: float) -> float:
    """0 at/below `start`, 1 at/above `end`, linear in between."""
    if end == start:
        return 1.0 if value >= end else 0.0
    return clip((value - start) / (end - start), 0.0, 1.0)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def snapshot_to_frame(snapshot: Any) -> pd.DataFrame:
    """TelemetrySnapshot -> DataFrame indexed by device_id (one row per device)."""
    rows = []
    for dev in snapshot.devices:
        row = {"device_id": dev.device_id, "device_type": dev.device_type.value}
        row.update(dev.metrics.model_dump())
        rows.append(row)
    return pd.DataFrame(rows).set_index("device_id")


def round_dict(d: dict, ndigits: int = 2) -> dict:
    return {k: (round(v, ndigits) if isinstance(v, float) else v) for k, v in d.items()}

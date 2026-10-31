from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from protocols.telemetry_schema import TelemetrySnapshot
from utils.helpers import snapshot_to_frame

FEATURES = ["cpu_utilization_pct", "memory_utilization_pct", "queue_drops", "interface_errors"]


def prepare(snapshot: TelemetrySnapshot) -> Tuple[pd.DataFrame, List[str]]:
    """Unreachable devices only have stale values, so they are excluded."""
    df = snapshot_to_frame(snapshot)
    unreachable = df.index[~df["reachable"]].tolist()
    return df[df["reachable"]].copy(), unreachable

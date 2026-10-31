from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from protocols.telemetry_schema import TelemetrySnapshot
from utils.helpers import snapshot_to_frame

FEATURES = ["latency_ms", "jitter_ms", "packet_loss_pct", "link_utilization_pct"]


def prepare(snapshot: TelemetrySnapshot) -> Tuple[pd.DataFrame, List[str]]:
    """Return (rows of reachable devices, ids of unreachable devices).
    Unreachable devices have probe-timeout values, not real measurements."""
    df = snapshot_to_frame(snapshot)
    unreachable = df.index[~df["reachable"]].tolist()
    return df[df["reachable"]].copy(), unreachable

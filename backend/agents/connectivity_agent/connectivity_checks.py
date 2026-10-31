"""Topology-aware checks. Each returns a list of finding dicts the agent turns into Findings."""
from __future__ import annotations

from typing import Dict, List, Set

import pandas as pd

from agents.connectivity_agent import rules
from agents.connectivity_agent.topology import NetworkTopology
from protocols.message_schema import Status
from utils.helpers import clip, clip01


def check_unreachable(df: pd.DataFrame, topo: NetworkTopology) -> List[dict]:
    """Find the cut points that explain the set of unreachable devices."""
    unreachable: Set[str] = set(df.index[~df["reachable"]])
    results = []
    if not unreachable:
        return results
    # topmost unreachable devices: parent is reachable
    tops = [d for d in unreachable if topo.parent(d) not in unreachable]
    for top in sorted(tops):
        subtree = {top, *topo.downstream(top)}
        consistent = subtree <= unreachable and subtree >= (unreachable & subtree)
        covered = len(subtree & unreachable) / len(subtree)
        parent = topo.parent(top)
        results.append({
            "link": [parent, top],
            "devices": sorted(subtree & unreachable),
            "confidence": 0.9 if covered == 1.0 else clip(0.5 + 0.3 * covered, 0.5, 0.8),
            "consistent": consistent and covered == 1.0,
            "alternate_path": topo.has_alternate_path(top),
        })
    return results


def check_service(df: pd.DataFrame, topo: NetworkTopology, service: str) -> dict | None:
    col, floor = (f"{service}_success_pct", rules.DNS_FAIL_BELOW if service == "dns" else rules.DHCP_FAIL_BELOW)
    pool = df[df["reachable"]]
    if service == "dhcp":
        pool = pool[pool["device_type"].isin(["switch", "access_point"])]
    if pool.empty:
        return None
    failing = pool[pool[col] < floor]
    if len(failing) / len(pool) < rules.SERVICE_MIN_FRACTION:
        return None
    mean_success = float(pool[col].mean())
    server = topo.server_with_role(service)
    return {
        "devices": sorted(failing.index),
        "server": server,
        "mean_success_pct": round(mean_success, 1),
        "failing_fraction": round(len(failing) / len(pool), 2),
        "confidence": clip01(0.55 + (100 - mean_success) / 100 + 0.2 * len(failing) / len(pool)) * 0.95,
    }


def check_downstream_degradation(df: pd.DataFrame, topo: NetworkTopology) -> List[dict]:
    reach = df[df["reachable"]]
    degraded: Set[str] = set(reach.index[
        (reach["latency_ms"] > rules.DEGRADED_LATENCY_MS)
        | (reach["packet_loss_pct"] > rules.DEGRADED_LOSS_PCT)
        | (reach["jitter_ms"] > rules.DEGRADED_JITTER_MS)
    ])
    qualifying: Dict[str, dict] = {}
    for dev in reach.index:
        desc = [d for d in topo.downstream(dev) if d in reach.index]
        if len(desc) < rules.DOWNSTREAM_MIN_DEVICES:
            continue
        bad = [d for d in desc if d in degraded]
        frac = len(bad) / len(desc)
        if len(bad) >= rules.DOWNSTREAM_MIN_DEVICES and frac >= rules.DOWNSTREAM_MIN_FRACTION:
            qualifying[dev] = {"devices": sorted(bad), "fraction": round(frac, 2), "confidence": clip01(0.45 + 0.4 * frac + 0.02 * len(bad))}
    # keep only topmost qualifying devices (no qualifying ancestor)
    out = []
    for dev, info in qualifying.items():
        anc = set(topo.path_to_core(dev)[1:])
        if not (anc & set(qualifying)):
            out.append({"root": dev, **info})
    return out

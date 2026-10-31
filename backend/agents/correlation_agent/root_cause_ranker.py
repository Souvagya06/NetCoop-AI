from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

import config
from agents.connectivity_agent.topology import NetworkTopology
from agents.correlation_agent.correlation_engine import HYPOTHESES, PROPAGATING, SIGNAL_OWNER, TIEBREAK
from protocols.message_schema import AgentMessage, EvidenceRequest


def rank(scored: Dict[str, dict]) -> List[Tuple[str, dict]]:
    return sorted(scored.items(), key=lambda kv: kv[1]["score"], reverse=True)


def contested(ranked: List[Tuple[str, dict]], margin: float = config.CONTEST_MARGIN) -> List[str]:
    if not ranked:
        return []
    top = ranked[0][1]["score"]
    return [n for n, s in ranked if s["score"] >= top - margin and s["score"] > 0]


def attribute_root(hypothesis: str, by_code: Dict[str, dict], messages: List[AgentMessage]) -> Tuple[Optional[str], Optional[List[str]]]:
    """Which device (or link) is the most likely source for this hypothesis?"""
    if hypothesis == "link_failure":
        for m in messages:
            links = m.evidence.get("failed_links") if m.evidence else None
            if links:
                return links[0][1], links[0]
    h = HYPOTHESES[hypothesis]
    weights = {h["primary"]: 1.0, **h["supporting"]}
    totals: Dict[str, float] = defaultdict(float)
    for code, w in weights.items():
        for dev, sc in by_code.get(code, {}).get("device_scores", {}).items():
            totals[dev] += w * sc
    if not totals:
        return None, None
    return max(totals, key=totals.get), None


def affected_devices(hypothesis: str, by_code: Dict[str, dict], root: Optional[str], topo: NetworkTopology) -> List[str]:
    h = HYPOTHESES[hypothesis]
    affected: Set[str] = set()
    for code in [h["primary"], *h["supporting"]]:
        affected.update(by_code.get(code, {}).get("devices", set()))
    if root:
        affected.add(root)
        if hypothesis in PROPAGATING:
            affected.update(topo.downstream(root))
    return sorted(affected)


def choose_request(contested_names: List[str], root: Optional[str], asked: Set[str]) -> Optional[EvidenceRequest]:
    """Pick the not-yet-asked agent that owns the signals that best separate the contested hypotheses."""
    if not root:
        return None
    totals: Dict[str, float] = defaultdict(float)
    for name in contested_names:
        for sig, w in TIEBREAK.get(name, {}).items():
            owner = SIGNAL_OWNER[sig]
            if owner not in asked:
                totals[owner] += abs(w)
    if not totals:
        return None
    agent = max(totals, key=totals.get)
    return EvidenceRequest(
        to=agent, check="detailed_signals", device_id=root,
        question=f"Top hypotheses are close ({', '.join(contested_names[:3])}). Provide a detailed per-signal breakdown for {root}.",
    )

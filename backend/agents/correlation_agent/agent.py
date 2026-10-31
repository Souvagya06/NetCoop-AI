from __future__ import annotations

from typing import List, Optional, Set

import config
from agents.connectivity_agent.topology import NetworkTopology, default_topology
from agents.correlation_agent import correlation_engine as eng
from agents.correlation_agent import root_cause_ranker as ranker
from protocols.message_schema import AgentMessage, Finding, MessageType, Status, worst_status
from utils.helpers import clip01

CONFIDENCE_NOTE = ("Evidence score in [0,1] = hypothesis score scaled by its margin over the runner-up. "
                   "It is a heuristic ranking signal, not a calibrated probability.")


class CorrelationAgent:
    name = "correlation_agent"
    description = "Compares the other agents' evidence and ranks probable root causes."

    def __init__(self, topology: Optional[NetworkTopology] = None) -> None:
        self.topology = topology or default_topology()

    def analyze(self, incident_id: str, messages: List[AgentMessage], allow_request: bool = True, asked: Optional[Set[str]] = None) -> AgentMessage:
        asked = asked or set()
        usable = [m for m in messages if m.message_type != MessageType.ERROR]
        errors = [m for m in messages if m.message_type == MessageType.ERROR]
        limitations = [lim for m in errors for lim in m.limitations]
        limitations.append("Diagnosis rests on a single telemetry snapshot and heuristic signatures.")

        analysis_senders = {m.sender for m in usable}
        if not usable or not ({"performance_agent", "infrastructure_agent", "connectivity_agent"} & analysis_senders):
            return self._final(incident_id, "undetermined", 0.0, [], None, None, [], Status.HEALTHY, limitations, {}, 0)

        by_code = eng.collect_findings(usable)
        scored = eng.score_hypotheses(by_code)
        ranked = ranker.rank(scored)
        cont = ranker.contested(ranked)
        signals = eng.gather_signals(usable)

        if signals and len(cont) >= 2:
            eng.apply_tiebreak(scored, cont, signals)
            ranked = ranker.rank(scored)
            cont = ranker.contested(ranked)

        top_name, top = (ranked[0] if ranked else ("normal", {"score": 0.0}))
        declared = bool(ranked) and top["score"] >= config.INCIDENT_THRESHOLD

        if declared and len(cont) >= 2 and allow_request:
            root, _ = ranker.attribute_root(top_name, by_code, usable)
            req = ranker.choose_request(cont, root, asked)
            if req:
                return AgentMessage(
                    incident_id=incident_id, sender=self.name, message_type=MessageType.REQUEST_EVIDENCE,
                    status=Status.WARNING, request=req, confidence=clip01(top["score"]),
                    evidence={"contested": cont, "scores": {n: s["score"] for n, s in ranked[:4]}},
                    limitations=limitations,
                )

        rounds_used = len(asked)
        if not declared:
            ev_rank = [{"cause": n, **s} for n, s in ranked[:3]]
            lim = limitations + ([f"Minor anomalies below the incident threshold were ignored: {', '.join(n for n, _ in ranked[:3])}."] if ranked else [])
            return self._final(incident_id, "normal", 1.0 if not ranked else 1 - top["score"], ev_rank, None, None, [], Status.HEALTHY, lim, by_code, rounds_used, signals)

        root, link = ranker.attribute_root(top_name, by_code, usable)
        affected = ranker.affected_devices(top_name, by_code, root, self.topology)
        second = ranked[1][1]["score"] if len(ranked) > 1 else 0.0
        margin = top["score"] - second
        confidence = clip01(top["score"] * (0.5 + 0.5 * min(1.0, margin / 0.25)))
        severity = by_code[eng.HYPOTHESES[top_name]["primary"]]["severity"]
        if len(cont) >= 2:
            limitations.append(f"Close call between {', '.join(cont[:3])}; margin {margin:.2f}. Verify manually.")
        ev_rank = [{"cause": n, **s} for n, s in ranked[:4]]
        return self._final(incident_id, top_name, confidence, ev_rank, root, link, affected, severity, limitations, by_code, rounds_used, signals, margin)

    def _final(self, incident_id, cause, confidence, ranking, root, link, affected, status, limitations, by_code, rounds_used, signals=None, margin=0.0) -> AgentMessage:
        findings = []
        for r in ranking[:3]:
            findings.append(Finding(code=r["cause"], description=eng.LABELS.get(r["cause"], r["cause"]), severity=status if r["cause"] == cause else Status.WARNING, devices=affected if r["cause"] == cause else [], confidence=clip01(r["score"])))
        evidence = {
            "root_cause": cause,
            "root_cause_label": eng.LABELS.get(cause, cause),
            "incident_declared": cause not in ("normal", "undetermined"),
            "root_device": root,
            "root_link": link,
            "affected_devices": affected,
            "ranking": ranking,
            "margin_over_runner_up": round(margin, 3),
            "evidence_rounds_used": rounds_used,
            "detailed_signals_used": signals or {},
            "findings_considered": sorted(by_code),
            "confidence_definition": CONFIDENCE_NOTE,
        }
        return AgentMessage(
            incident_id=incident_id, sender=self.name, message_type=MessageType.DIAGNOSIS, status=status,
            findings=findings, evidence=evidence, confidence=clip01(confidence), limitations=limitations,
        )

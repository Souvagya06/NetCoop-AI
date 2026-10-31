from __future__ import annotations

from typing import List

from agents.reporting_agent import recommendation_engine as rec
from agents.reporting_agent import report_generator as gen
from protocols.message_schema import AgentMessage, MessageType, Status
from protocols.telemetry_schema import TelemetrySnapshot

KEY_METRICS = [("cpu_utilization_pct", "CPU utilisation (%)"), ("memory_utilization_pct", "Memory utilisation (%)"), ("link_utilization_pct", "Link utilisation (%)"),
               ("latency_ms", "Latency (ms)"), ("packet_loss_pct", "Packet loss (%)"), ("queue_drops", "Queue drops"), ("interface_errors", "Interface errors")]


class ReportingAgent:
    name = "reporting_agent"
    description = "Turns the ranked diagnosis into an explainable report with advisory actions."

    def analyze(self, incident_id: str, diagnosis: AgentMessage, messages: List[AgentMessage], snapshot: TelemetrySnapshot, use_llm: bool = True) -> AgentMessage:
        ev = diagnosis.evidence
        cause, root, link = ev["root_cause"], ev.get("root_device"), ev.get("root_link")

        key_metrics = {}
        dev = snapshot.get(root) if root else None
        if dev and cause not in ("normal", "undetermined"):
            m = dev.metrics.model_dump()
            key_metrics = {label: m[k] for k, label in KEY_METRICS}

        evidence_lines = []
        for m in messages:
            if m.message_type == MessageType.ERROR:
                continue
            for f in m.findings[:3]:
                if f.code == "statistical_anomaly":
                    continue
                evidence_lines.append(f"{m.sender}: {f.code} (evidence {f.confidence:.2f}) - {f.description}")
        if ev.get("ranking"):
            r0 = ev["ranking"][0]
            evidence_lines.append(f"correlation_agent: top hypothesis '{r0['cause']}' score {r0['score']:.2f}; margin over runner-up {ev.get('margin_over_runner_up', 0):.2f}")
        if not evidence_lines:
            evidence_lines.append("All analysis agents report normal behaviour.")

        label = ev["root_cause_label"]
        if cause == "normal":
            summary = "No significant incident detected."
        elif cause == "undetermined":
            summary = "A diagnosis could not be produced because the analysis agents were unavailable."
        else:
            where = f" Most likely source: {root}." if root else ""
            summary = f"{label} is the most probable root cause.{where} {len(ev.get('affected_devices', []))} device(s) appear affected."

        report = {
            "incident_id": incident_id,
            "title": f"Incident Report {incident_id}",
            "severity": diagnosis.status.value if cause != "normal" else Status.HEALTHY.value,
            "probable_root_cause": label,
            "root_cause_code": cause,
            "confidence": round(diagnosis.confidence, 3),
            "summary": summary,
            "root_device": root,
            "root_link": link,
            "key_metrics": key_metrics,
            "affected_devices": ev.get("affected_devices", []),
            "evidence": evidence_lines,
            "alternatives": [{"cause": r["cause"], "score": r["score"]} for r in ev.get("ranking", [])[1:3]],
            "recommended_actions": rec.recommend(cause, root, link),
            "limitations": diagnosis.limitations,
            "disclaimer": gen.DISCLAIMER,
            "generated_by": "rules",
        }
        if use_llm and cause not in ("normal", "undetermined"):
            text = gen.gemini_summary(report)
            if text:
                report["ai_summary"], report["generated_by"] = text, "rules+gemini"
        report["markdown"] = gen.to_markdown(report)

        return AgentMessage(incident_id=incident_id, sender=self.name, message_type=MessageType.REPORT, status=diagnosis.status,
                            evidence={"report": report}, confidence=diagnosis.confidence, limitations=diagnosis.limitations)

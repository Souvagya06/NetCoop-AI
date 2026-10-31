from __future__ import annotations

from typing import Optional

from agents.base_agent import AnalysisAgent, PerDevice, aggregate_findings
from agents.infrastructure_agent import detector as det
from agents.infrastructure_agent import rules
from agents.infrastructure_agent.preprocessing import FEATURES, prepare
from protocols.message_schema import AgentMessage, Status, worst_status
from protocols.telemetry_schema import TelemetrySnapshot
from utils.helpers import clip01, round_dict

ML_BLEND = 0.25
ML_ONLY_THRESHOLD = 0.75


class InfrastructureAgent(AnalysisAgent):
    name = "infrastructure_agent"
    description = "Checks device health: CPU, memory, queue drops and interface errors."

    def analyze(self, snapshot: TelemetrySnapshot, incident_id: str, focus_device: Optional[str] = None) -> AgentMessage:
        df, unreachable = prepare(snapshot)
        if focus_device is not None:
            df = df[df.index == focus_device]

        ml_scores = det.detector.score(df[FEATURES]) if len(df) else []
        ml_on = det.detector.available
        per_device: PerDevice = {}
        ml_by_dev = {}
        for (dev, row), ml in zip(df.iterrows(), ml_scores):
            ml_by_dev[dev] = float(ml)
            found = {}
            for code, (rule_conf, sev) in rules.evaluate_device(row.to_dict()).items():
                conf = (1 - ML_BLEND) * rule_conf + ML_BLEND * ml if ml_on else rule_conf
                found[code] = (clip01(conf), sev)
            if ml_on and not found and ml >= ML_ONLY_THRESHOLD:
                found["statistical_anomaly"] = (clip01(0.6 * ml), Status.WARNING)
            if found:
                per_device[dev] = found

        findings = aggregate_findings(per_device, rules.DESCRIPTIONS)
        status = worst_status(f.severity for f in findings)
        evidence = {
            "devices_analysed": int(len(df)),
            "ml_model_used": ml_on,
            "thresholds": {k: {"warn": v[0], "crit": v[1]} for k, v in rules.THRESHOLDS.items()},
            "flagged_devices": {d: {**round_dict({k: float(df.loc[d, k]) for k in FEATURES}), "ml_anomaly_score": round(ml_by_dev[d], 3)} for d in per_device},
        }
        if focus_device is not None and focus_device in df.index:
            evidence["focus_device"] = focus_device
            evidence["detailed_signals"] = rules.detailed_signals(df.loc[focus_device].to_dict())

        limitations = ["Analysis uses a single telemetry snapshot (no trend over time).", "Cannot inspect running processes or logs; only aggregate health metrics."]
        if unreachable:
            limitations.append(f"{len(unreachable)} unreachable device(s) excluded (health metrics are stale).")
        if not ml_on:
            limitations.append("Isolation Forest model not loaded; rules only.")

        confidence = max((f.confidence for f in findings), default=clip01(0.85 - 0.3 * max(ml_by_dev.values(), default=0.0)))
        return AgentMessage(incident_id=incident_id, sender=self.name, status=status, findings=findings, evidence=evidence, confidence=confidence, limitations=limitations)

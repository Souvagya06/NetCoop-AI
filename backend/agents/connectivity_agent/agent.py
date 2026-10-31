from __future__ import annotations

from typing import List, Optional

from agents.base_agent import AnalysisAgent
from agents.connectivity_agent import connectivity_checks as checks
from agents.connectivity_agent import rules
from agents.connectivity_agent.topology import NetworkTopology, default_topology
from protocols.message_schema import AgentMessage, Finding, Status, worst_status
from protocols.telemetry_schema import TelemetrySnapshot
from utils.helpers import clip01, snapshot_to_frame


class ConnectivityAgent(AnalysisAgent):
    name = "connectivity_agent"
    description = "Examines topology, unreachable segments, DNS and DHCP health (NetworkX + rules)."

    def __init__(self, topology: Optional[NetworkTopology] = None) -> None:
        self.topology = topology or default_topology()

    def analyze(self, snapshot: TelemetrySnapshot, incident_id: str, focus_device: Optional[str] = None) -> AgentMessage:
        topo = self.topology
        df = snapshot_to_frame(snapshot)
        known = df.index.isin(topo.device_ids())
        limitations = ["Analysis uses a single telemetry snapshot; intermittent failures may be missed.", "Reachability comes from probe results in the telemetry, not live pings."]
        if not known.all():
            limitations.append(f"{int((~known).sum())} device(s) not in the known topology were ignored.")
            df = df[known]

        findings: List[Finding] = []
        evidence: dict = {}

        links = checks.check_unreachable(df, topo)
        if links:
            findings.append(Finding(
                code="link_failure",
                description=rules.DESCRIPTIONS["link_failure"].format(n=sum(len(l["devices"]) for l in links)),
                severity=Status.CRITICAL,
                devices=sorted({d for l in links for d in l["devices"]}),
                device_scores={l["link"][1]: round(l["confidence"], 3) for l in links},
                confidence=round(max(l["confidence"] for l in links), 3),
            ))
            evidence["failed_links"] = [l["link"] for l in links]
            evidence["link_details"] = links
            if any(not l["consistent"] for l in links):
                limitations.append("Unreachable set does not match a clean subtree; cause could also be a failed device rather than a link.")

        for service in ("dns", "dhcp"):
            res = checks.check_service(df, topo, service)
            if res:
                srv = res["server"]
                findings.append(Finding(
                    code=f"{service}_failure",
                    description=rules.DESCRIPTIONS[f"{service}_failure"].format(n=len(res["devices"])),
                    severity=Status.CRITICAL if res["mean_success_pct"] < 50 else Status.WARNING,
                    devices=res["devices"],
                    device_scores={srv: round(res["confidence"], 3)} if srv else {},
                    confidence=round(res["confidence"], 3),
                ))
                evidence[f"{service}"] = {k: v for k, v in res.items() if k != "devices"}

        for deg in checks.check_downstream_degradation(df, topo):
            findings.append(Finding(
                code="downstream_degradation",
                description=rules.DESCRIPTIONS["downstream_degradation"].format(device=deg["root"]),
                severity=Status.WARNING,
                devices=deg["devices"],
                device_scores={deg["root"]: round(deg["confidence"], 3)},
                confidence=round(deg["confidence"], 3),
            ))
            evidence.setdefault("downstream", []).append({"root": deg["root"], "degraded": deg["devices"], "fraction": deg["fraction"]})

        if focus_device and topo.has_device(focus_device):
            evidence["focus_device"] = focus_device
            evidence["path_to_core"] = topo.path_to_core(focus_device)
            evidence["alternate_path_available"] = topo.has_alternate_path(focus_device)

        evidence["devices_analysed"] = int(len(df))
        evidence["unreachable_count"] = int((~df["reachable"]).sum())
        status = worst_status(f.severity for f in findings)
        confidence = max((f.confidence for f in findings), default=0.85)
        return AgentMessage(incident_id=incident_id, sender=self.name, status=status, findings=findings, evidence=evidence, confidence=clip01(confidence), limitations=limitations)

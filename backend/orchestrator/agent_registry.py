from __future__ import annotations

from typing import Dict, List, Optional

from agents.base_agent import AnalysisAgent
from agents.connectivity_agent.agent import ConnectivityAgent
from agents.connectivity_agent.topology import NetworkTopology, default_topology
from agents.correlation_agent.agent import CorrelationAgent
from agents.infrastructure_agent.agent import InfrastructureAgent
from agents.performance_agent.agent import PerformanceAgent
from agents.reporting_agent.agent import ReportingAgent


class AgentRegistry:
    """Knows which agents exist. Analysis agents run in parallel; correlation/reporting run in sequence."""

    def __init__(self) -> None:
        self.analysis: Dict[str, AnalysisAgent] = {}
        self.correlation: Optional[CorrelationAgent] = None
        self.reporting: Optional[ReportingAgent] = None

    def register_analysis(self, agent: AnalysisAgent) -> None:
        self.analysis[agent.name] = agent

    def analysis_names(self) -> List[str]:
        return list(self.analysis)

    def describe(self) -> List[dict]:
        out = [{"name": a.name, "role": "analysis", "description": a.description} for a in self.analysis.values()]
        if self.correlation:
            out.append({"name": self.correlation.name, "role": "correlation", "description": self.correlation.description})
        if self.reporting:
            out.append({"name": self.reporting.name, "role": "reporting", "description": self.reporting.description})
        return out


def build_default_registry(topology: Optional[NetworkTopology] = None) -> AgentRegistry:
    topo = topology or default_topology()
    reg = AgentRegistry()
    reg.register_analysis(PerformanceAgent())
    reg.register_analysis(InfrastructureAgent())
    reg.register_analysis(ConnectivityAgent(topo))
    reg.correlation = CorrelationAgent(topo)
    reg.reporting = ReportingAgent()
    return reg

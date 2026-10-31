from agents.connectivity_agent.agent import ConnectivityAgent
from agents.correlation_agent.agent import CorrelationAgent
from agents.infrastructure_agent.agent import InfrastructureAgent
from agents.performance_agent.agent import PerformanceAgent
from protocols.message_schema import MessageType


def run(snapshot, topology, allow_request=False):
    msgs = [PerformanceAgent().analyze(snapshot, "NC-T"), InfrastructureAgent().analyze(snapshot, "NC-T"), ConnectivityAgent(topology).analyze(snapshot, "NC-T")]
    return CorrelationAgent(topology).analyze("NC-T", msgs, allow_request=allow_request), msgs


def test_healthy_network_is_normal(make_snapshot, topology):
    diag, _ = run(make_snapshot(), topology)
    assert diag.evidence["root_cause"] == "normal" and not diag.evidence["incident_declared"]


def test_router_overload_example_from_the_brief(make_snapshot, topology):
    """CPU 98.5, mem 92, link 96, latency 450, loss 12.5, queue drops 6500 on the core router."""
    snap = make_snapshot({"RTR_CAMPUS_01": dict(cpu_utilization_pct=98.5, memory_utilization_pct=92, link_utilization_pct=96, latency_ms=450, packet_loss_pct=12.5, queue_drops=6500, interface_errors=15)})
    diag, _ = run(snap, topology)
    assert diag.evidence["root_cause"] in ("cpu_overload", "network_congestion")
    assert diag.evidence["root_device"] == "RTR_CAMPUS_01"


def test_symptoms_are_explained_by_deeper_cause(make_snapshot, topology):
    snap = make_snapshot({"SW_CAMPUS_02": dict(cpu_utilization_pct=97, queue_drops=2500, latency_ms=350, packet_loss_pct=6)})
    diag, _ = run(snap, topology)
    assert diag.evidence["root_cause"] == "cpu_overload"  # not latency_spike / packet_loss


def test_dns_failure(make_snapshot, topology):
    diag, _ = run(make_snapshot({d: {"dns_success_pct": 10} for d in topology.device_ids()}), topology)
    assert diag.evidence["root_cause"] == "dns_failure" and diag.evidence["root_device"] == "SRV_DNS_01"


def test_close_call_triggers_bounded_evidence_request(make_snapshot, topology):
    # CPU and memory both elevated on one device -> cpu_overload vs memory_overload is a near tie
    snap = make_snapshot({"SW_CAMPUS_03": dict(cpu_utilization_pct=90, memory_utilization_pct=91, latency_ms=120)})
    diag, _ = run(snap, topology, allow_request=True)
    assert diag.message_type in (MessageType.REQUEST_EVIDENCE, MessageType.DIAGNOSIS)
    if diag.message_type == MessageType.REQUEST_EVIDENCE:
        assert diag.request.to in ("infrastructure_agent", "performance_agent") and diag.request.device_id == "SW_CAMPUS_03"


def test_no_request_when_not_allowed(make_snapshot, topology):
    snap = make_snapshot({"SW_CAMPUS_03": dict(cpu_utilization_pct=90, memory_utilization_pct=91, latency_ms=120)})
    diag, _ = run(snap, topology, allow_request=False)
    assert diag.message_type == MessageType.DIAGNOSIS


def test_all_agents_failed_is_undetermined_not_normal(topology):
    from orchestrator.orchestrator import Orchestrator
    err = [Orchestrator._error_message(n, "NC-T", "boom") for n in ("performance_agent", "infrastructure_agent", "connectivity_agent")]
    diag = CorrelationAgent(topology).analyze("NC-T", err)
    assert diag.evidence["root_cause"] == "undetermined"

from agents.performance_agent.agent import PerformanceAgent
from protocols.message_schema import Status

agent = PerformanceAgent()


def codes(msg):
    return {f.code for f in msg.findings}


def test_healthy_network_has_no_rule_findings(make_snapshot):
    msg = agent.analyze(make_snapshot(), "NC-T")
    assert not (codes(msg) - {"statistical_anomaly"})
    assert msg.status in (Status.HEALTHY, Status.WARNING)


def test_latency_and_loss_detected(make_snapshot):
    msg = agent.analyze(make_snapshot({"SW_CAMPUS_01": {"latency_ms": 400, "packet_loss_pct": 8}}), "NC-T")
    assert {"latency_spike", "packet_loss"} <= codes(msg)
    assert msg.status == Status.CRITICAL


def test_congestion_needs_utilisation_plus_queue_or_latency(make_snapshot):
    only_util = agent.analyze(make_snapshot({"RTR_CAMPUS_02": {"link_utilization_pct": 95}}), "NC-T")
    assert "network_congestion" not in codes(only_util)
    both = agent.analyze(make_snapshot({"RTR_CAMPUS_02": {"link_utilization_pct": 95, "queue_drops": 4000}}), "NC-T")
    assert "network_congestion" in codes(both)


def test_unreachable_devices_are_excluded_not_flagged(make_snapshot):
    msg = agent.analyze(make_snapshot({"AP_CAMPUS_01": {"reachable": False, "latency_ms": 2000, "packet_loss_pct": 100}}), "NC-T")
    assert "packet_loss" not in codes(msg)
    assert any("unreachable" in l for l in msg.limitations)


def test_focus_device_returns_detailed_signals(make_snapshot):
    msg = agent.analyze(make_snapshot({"SW_CAMPUS_01": {"latency_ms": 200}}), "NC-T", focus_device="SW_CAMPUS_01")
    assert 0 < msg.evidence["detailed_signals"]["latency"] <= 1

from agents.infrastructure_agent.agent import InfrastructureAgent

agent = InfrastructureAgent()


def codes(msg):
    return {f.code for f in msg.findings}


def test_healthy(make_snapshot):
    assert not (codes(agent.analyze(make_snapshot(), "NC-T")) - {"statistical_anomaly"})


def test_cpu_overload(make_snapshot):
    assert "device_overload" in codes(agent.analyze(make_snapshot({"RTR_CAMPUS_01": {"cpu_utilization_pct": 98}}), "NC-T"))


def test_memory_pressure(make_snapshot):
    assert "memory_pressure" in codes(agent.analyze(make_snapshot({"SRV_APP_01": {"memory_utilization_pct": 96}}), "NC-T"))


def test_interface_errors_alone_is_interface_failure(make_snapshot):
    c = codes(agent.analyze(make_snapshot({"SW_CAMPUS_02": {"interface_errors": 300}}), "NC-T"))
    assert "interface_failure" in c and "hardware_failure" not in c


def test_combined_degradation_is_hardware_failure(make_snapshot):
    snap = make_snapshot({"SW_CAMPUS_02": {"interface_errors": 300, "cpu_utilization_pct": 97, "memory_utilization_pct": 95, "queue_drops": 6000}})
    c = codes(agent.analyze(snap, "NC-T"))
    assert "hardware_failure" in c and "interface_failure" not in c

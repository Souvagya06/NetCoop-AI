from orchestrator.orchestrator import Orchestrator


def test_report_has_required_sections(make_snapshot):
    snap = make_snapshot({"RTR_CAMPUS_01": dict(cpu_utilization_pct=98.5, queue_drops=6000, latency_ms=300, packet_loss_pct=6)})
    r = Orchestrator(use_llm=False).diagnose(snap)["report"]
    for key in ("incident_id", "severity", "probable_root_cause", "confidence", "evidence", "recommended_actions", "disclaimer", "markdown"):
        assert key in r
    assert r["recommended_actions"] and "advisory" in r["disclaimer"]
    assert r["root_device"] == "RTR_CAMPUS_01"


def test_healthy_report_has_no_incident(make_snapshot):
    r = Orchestrator(use_llm=False).diagnose(make_snapshot())["report"]
    assert r["root_cause_code"] == "normal" and r["severity"] == "healthy"


def test_orchestrator_survives_a_crashing_agent(make_snapshot):
    orch = Orchestrator(use_llm=False)
    orch.registry.analysis["performance_agent"].analyze = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    snap = make_snapshot({"RTR_CAMPUS_01": dict(cpu_utilization_pct=98.5, memory_utilization_pct=92, queue_drops=6000, interface_errors=200)})
    res = orch.diagnose(snap)
    assert res["root_cause"]["code"] == "hardware_failure"
    assert any("performance_agent" in l for l in res["correlation"]["limitations"])


def test_agents_never_see_ground_truth():
    from data_generator.generator import TelemetryGenerator
    seen = {}
    orch = Orchestrator(use_llm=False)
    original = orch.registry.analysis["connectivity_agent"].analyze
    def spy(snapshot, incident_id, focus_device=None):
        seen["gt"] = snapshot.ground_truth
        return original(snapshot, incident_id, focus_device)
    orch.registry.analysis["connectivity_agent"].analyze = spy
    orch.diagnose(TelemetryGenerator(seed=1).generate_snapshot("cpu_overload"))
    assert seen["gt"] is None

from agents.connectivity_agent.agent import ConnectivityAgent

DOWN = {"reachable": False, "latency_ms": 2000, "packet_loss_pct": 100}


def test_healthy_has_no_findings(make_snapshot, topology):
    assert ConnectivityAgent(topology).analyze(make_snapshot(), "NC-T").findings == []


def test_link_failure_identifies_the_cut(make_snapshot, topology):
    sub = ["SW_CAMPUS_01", *topology.downstream("SW_CAMPUS_01")]
    msg = ConnectivityAgent(topology).analyze(make_snapshot({d: DOWN for d in sub}), "NC-T")
    f = next(x for x in msg.findings if x.code == "link_failure")
    assert msg.evidence["failed_links"] == [[topology.parent("SW_CAMPUS_01"), "SW_CAMPUS_01"]]
    assert set(f.devices) == set(sub)


def test_dns_failure_points_at_dns_server(make_snapshot, topology):
    snap = make_snapshot({d: {"dns_success_pct": 20} for d in topology.device_ids()})
    f = next(x for x in ConnectivityAgent(topology).analyze(snap, "NC-T").findings if x.code == "dns_failure")
    assert "SRV_DNS_01" in f.device_scores


def test_dhcp_failure(make_snapshot, topology):
    snap = make_snapshot({d: {"dhcp_success_pct": 10} for d in topology.devices_of_type("switch", "access_point")})
    assert any(f.code == "dhcp_failure" for f in ConnectivityAgent(topology).analyze(snap, "NC-T").findings)


def test_downstream_degradation_when_router_still_reachable(make_snapshot, topology):
    kids = topology.downstream("RTR_CAMPUS_02")
    msg = ConnectivityAgent(topology).analyze(make_snapshot({d: {"latency_ms": 150} for d in kids}), "NC-T")
    assert any(f.code == "downstream_degradation" for f in msg.findings)

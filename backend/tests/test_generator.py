import pytest

from data_generator.generator import TelemetryGenerator
from data_generator.scenarios import SCENARIOS


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_scenario_generates_valid_snapshot(scenario):
    snap = TelemetryGenerator(seed=1).generate_snapshot(scenario)
    assert len(snap.devices) == 20
    assert snap.ground_truth.scenario == scenario


def test_same_seed_is_reproducible():
    a = TelemetryGenerator(seed=5).generate_snapshot("cpu_overload")
    b = TelemetryGenerator(seed=5).generate_snapshot("cpu_overload")
    assert [d.metrics for d in a.devices] == [d.metrics for d in b.devices]


def test_different_seeds_differ():
    a = TelemetryGenerator(seed=5).generate_snapshot("normal")
    b = TelemetryGenerator(seed=6).generate_snapshot("normal")
    assert [d.metrics for d in a.devices] != [d.metrics for d in b.devices]


def test_link_failure_makes_whole_subtree_unreachable(topology):
    snap = TelemetryGenerator(seed=2).generate_snapshot("link_failure")
    gt = snap.ground_truth
    down = {d.device_id for d in snap.devices if not d.metrics.reachable}
    assert down == {gt.root_device, *topology.downstream(gt.root_device)}
    assert gt.root_link == [topology.parent(gt.root_device), gt.root_device]


def test_dns_failure_lowers_dns_success():
    snap = TelemetryGenerator(seed=3).generate_snapshot("dns_failure")
    assert snap.ground_truth.root_device == "SRV_DNS_01"
    assert min(d.metrics.dns_success_pct for d in snap.devices) < 90


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        TelemetryGenerator(seed=1).generate_snapshot("nope")

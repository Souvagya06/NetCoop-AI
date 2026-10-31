from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_scenarios_and_topology_and_agents():
    assert len(client.get("/api/scenarios").json()["scenarios"]) == 11
    assert client.get("/api/topology").json()["core"] == "RTR_CAMPUS_01"
    assert len(client.get("/api/agents").json()["agents"]) == 5


def test_simulate_and_fetch_incident():
    r = client.post("/api/diagnosis/simulate", json={"scenario": "hardware_failure", "seed": 4})
    assert r.status_code == 200
    body = r.json()
    assert body["root_cause"]["code"] == "hardware_failure"
    assert body["report"]["recommended_actions"]
    assert client.get(f"/api/diagnosis/{body['incident_id']}").status_code == 200
    assert any(i["incident_id"] == body["incident_id"] for i in client.get("/api/diagnosis/history").json()["incidents"])


def test_run_with_posted_snapshot(make_snapshot):
    snap = make_snapshot({"SRV_DNS_01": {}}).model_dump(mode="json")
    assert client.post("/api/diagnosis/run", json=snap).json()["root_cause"]["code"] == "normal"


def test_bad_inputs():
    assert client.post("/api/diagnosis/simulate", json={"scenario": "nope"}).status_code == 422
    assert client.post("/api/diagnosis/run", json={"devices": []}).status_code == 422
    assert client.get("/api/diagnosis/NC-9999").status_code == 404

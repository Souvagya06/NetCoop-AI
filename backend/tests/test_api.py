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


def test_cors_allows_frontend_loopback_origins():
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = client.options(
            "/api/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_cors_does_not_allow_unconfigured_origins():
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_validation_errors_have_a_safe_consistent_shape():
    response = client.post("/api/diagnosis/simulate", json={"scenario": "cpu_overload", "seed": -1})
    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Request validation failed"
    assert body["code"] == "request_validation_error"
    assert body["errors"][0]["location"] == ["body", "seed"]
    assert "input" not in body["errors"][0]

    protocol_error = client.post("/api/diagnosis/run", json={"devices": []})
    assert protocol_error.status_code == 422
    assert protocol_error.json()["code"] == "protocol_error"
    assert isinstance(protocol_error.json()["detail"], str)


def test_simulation_requests_reject_unknown_fields_and_non_integer_seeds():
    extra_field = client.post("/api/telemetry/generate", json={"scenario": "normal", "typo": True})
    fractional_seed = client.post(
        "/api/diagnosis/simulate",
        json={"scenario": "normal", "seed": 1.5},
    )
    assert extra_field.status_code == 422
    assert fractional_seed.status_code == 422
    assert extra_field.json()["code"] == "request_validation_error"
    assert fractional_seed.json()["code"] == "request_validation_error"

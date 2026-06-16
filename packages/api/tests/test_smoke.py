from fastapi.testclient import TestClient
from labooke_api.main import app


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_config_endpoint():
    client = TestClient(app)
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert body["chunk_pages"] >= 1
    assert "embed_model" in body

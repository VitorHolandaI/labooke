"""Verify the CORS middleware reacts to the ``cors_origins`` setting."""

from __future__ import annotations

from fastapi.testclient import TestClient
from labooke_api.app import create_app
from labooke_core.config import Settings


def test_cors_off_by_default(tmp_path):
    settings = Settings(data_dir=tmp_path / "data", import_dir=tmp_path / "inbox")
    app = create_app(settings=settings)
    with TestClient(app) as client:
        response = client.get(
            "/healthz", headers={"Origin": "http://localhost:5173"}
        )
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_configured_origin(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        import_dir=tmp_path / "inbox",
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings=settings)
    with TestClient(app) as client:
        response = client.get(
            "/healthz", headers={"Origin": "http://localhost:5173"}
        )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

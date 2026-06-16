"""Tests for the FastAPI application factory and lifespan wiring."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from labooke_api.app import create_app
from labooke_api.container import build_container
from labooke_core.config import Settings


def _ephemeral_settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data", import_dir=tmp_path / "inbox")


def test_lifespan_attaches_container(tmp_path):
    settings = _ephemeral_settings(tmp_path)
    app = create_app(settings=settings)
    with TestClient(app):
        assert app.state.container.settings is settings
        assert app.state.container.search is not None


def test_injected_container_is_reused(tmp_path):
    settings = _ephemeral_settings(tmp_path)
    container = build_container(settings)
    try:
        app = create_app(settings=settings, container=container)
        with TestClient(app):
            assert app.state.container is container
    finally:
        container.close()

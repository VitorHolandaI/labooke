"""Validate `Settings` env parsing for tricky list-style fields."""

import pytest
from labooke_core.config import Settings


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # avoid loading the repo .env
    monkeypatch.delenv("LABOOKE_CORS_ORIGINS", raising=False)


def test_cors_origins_defaults_to_empty():
    assert Settings().cors_origins == []


def test_cors_origins_empty_env_is_empty_list(monkeypatch):
    monkeypatch.setenv("LABOOKE_CORS_ORIGINS", "")
    assert Settings().cors_origins == []


def test_cors_origins_parses_csv(monkeypatch):
    monkeypatch.setenv(
        "LABOOKE_CORS_ORIGINS",
        "http://localhost:5173, http://host.local:5173",
    )
    assert Settings().cors_origins == [
        "http://localhost:5173",
        "http://host.local:5173",
    ]


def test_cors_origins_ignores_blank_segments(monkeypatch):
    monkeypatch.setenv("LABOOKE_CORS_ORIGINS", "http://a,, http://b ,")
    assert Settings().cors_origins == ["http://a", "http://b"]


def test_embed_cache_model_can_be_disabled(monkeypatch):
    monkeypatch.setenv("LABOOKE_EMBED_CACHE_MODEL", "false")
    assert Settings().embed_cache_model is False


def test_embed_worker_idle_seconds_can_be_configured(monkeypatch):
    monkeypatch.setenv("LABOOKE_EMBED_WORKER_IDLE_SECONDS", "2.5")
    assert Settings().embed_worker_idle_seconds == 2.5

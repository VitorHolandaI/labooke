"""Tests for the domain-to-HTTP exception handlers."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from labooke_api.app import create_app
from labooke_core.config import Settings
from labooke_core.store.books_repo import BookNotFound
from labooke_core.store.chunks_repo import ChunkNotFound
from labooke_core.store.tags_repo import TagNotFound


def _build_app(tmp_path: Path) -> FastAPI:
    settings = Settings(data_dir=tmp_path / "data", import_dir=tmp_path / "inbox")
    return create_app(settings=settings)


def test_book_not_found_returns_404(tmp_path):
    app = _build_app(tmp_path)

    @app.get("/_raise/book")
    def _raise():
        raise BookNotFound("no book with id=42")

    with TestClient(app) as client:
        response = client.get("/_raise/book")
    assert response.status_code == 404
    assert response.json() == {"code": "book_not_found", "message": "no book with id=42"}


def test_tag_not_found_returns_404(tmp_path):
    app = _build_app(tmp_path)

    @app.get("/_raise/tag")
    def _raise():
        raise TagNotFound("no tag with slug='x'")

    with TestClient(app) as client:
        response = client.get("/_raise/tag")
    assert response.status_code == 404
    assert response.json()["code"] == "tag_not_found"


def test_chunk_not_found_returns_404(tmp_path):
    app = _build_app(tmp_path)

    @app.get("/_raise/chunk")
    def _raise():
        raise ChunkNotFound("no chunk with id=1")

    with TestClient(app) as client:
        response = client.get("/_raise/chunk")
    assert response.status_code == 404
    assert response.json()["code"] == "chunk_not_found"


def test_value_error_returns_400(tmp_path):
    app = _build_app(tmp_path)

    @app.get("/_raise/value")
    def _raise():
        raise ValueError("page_no must be >= 1, got 0")

    with TestClient(app) as client:
        response = client.get("/_raise/value")
    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_argument",
        "message": "page_no must be >= 1, got 0",
    }

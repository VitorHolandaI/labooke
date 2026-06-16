"""Tests for the dependency providers in :mod:`labooke_api.deps`."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from labooke_api.app import create_app
from labooke_api.deps import (
    get_ingest_service,
    get_library_scanner,
    get_reembed_service,
    get_search_service,
    get_settings,
)
from labooke_core.config import Settings
from labooke_core.services import (
    IngestService,
    LibraryScanner,
    ReembedService,
    SearchService,
)


def _build_app(tmp_path: Path) -> tuple[FastAPI, Settings]:
    settings = Settings(data_dir=tmp_path / "data", import_dir=tmp_path / "inbox")
    return create_app(settings=settings), settings


def test_get_settings_returns_active_instance(tmp_path):
    app, settings = _build_app(tmp_path)

    @app.get("/_settings")
    def _read(active: Annotated[Settings, Depends(get_settings)]) -> dict[str, str]:
        return {"data_dir": str(active.data_dir)}

    with TestClient(app) as client:
        body = client.get("/_settings").json()
    assert body == {"data_dir": str(settings.data_dir)}


def test_per_request_services_have_correct_types(tmp_path):
    app, _ = _build_app(tmp_path)

    @app.get("/_probe")
    def _probe(
        ingest: Annotated[IngestService, Depends(get_ingest_service)],
        reembed: Annotated[ReembedService, Depends(get_reembed_service)],
        scanner: Annotated[LibraryScanner, Depends(get_library_scanner)],
        search: Annotated[SearchService, Depends(get_search_service)],
    ) -> dict[str, str]:
        return {
            "ingest": type(ingest).__name__,
            "reembed": type(reembed).__name__,
            "scanner": type(scanner).__name__,
            "search": type(search).__name__,
        }

    with TestClient(app) as client:
        body = client.get("/_probe").json()
    assert body == {
        "ingest": "IngestService",
        "reembed": "ReembedService",
        "scanner": "LibraryScanner",
        "search": "SearchService",
    }

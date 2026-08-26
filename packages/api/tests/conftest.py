"""Shared test fixtures for the API package."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from labooke_api.app import create_app
from labooke_api.container import AppContainer, build_container
from labooke_core.config import Settings
from labooke_core.domain.models import Book


class FakePipeline:
    """Embed-free stand-in for ``BookEmbeddingPipeline`` used in tests."""

    def __init__(self, page_count: int = 3) -> None:
        self.page_count = page_count
        self.rebuilt_books: list[int] = []

    def rebuild(self, book: Book) -> int:
        """Record the rebuild request and return the canned page count."""
        self.rebuilt_books.append(book.id)
        return self.page_count


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        import_dir=tmp_path / "inbox",
        # hermético: ignora um .env local que ligue LLM ou CORS
        cors_origins=[],
        embed_base_url="",
        llm_base_url="",
        llm_model="",
    )


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """Yield a TestClient backed by an isolated on-disk DB under ``tmp_path``."""
    app = create_app(settings=_make_settings(tmp_path))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def container(client: TestClient) -> AppContainer:
    """Return the API app container attached to the test client."""
    app = cast(FastAPI, client.app)
    return cast(AppContainer, app.state.container)


@pytest.fixture
def client_with_fake_pipeline(tmp_path: Path) -> Iterator[tuple[TestClient, FakePipeline]]:
    """Yield a TestClient whose container ingest uses ``FakePipeline``."""
    settings = _make_settings(tmp_path)
    container = build_container(settings)
    fake = FakePipeline()
    container.pipeline = fake  # type: ignore[assignment]
    app = create_app(settings=settings, container=container)
    try:
        with TestClient(app) as test_client:
            yield test_client, fake
    finally:
        container.close()

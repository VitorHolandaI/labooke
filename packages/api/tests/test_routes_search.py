"""Coverage for the search route under lexical mode."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from labooke_api.container import AppContainer
from labooke_core.domain.models import BookStatus


def _seed_two_books(container: AppContainer) -> tuple[int, int]:
    alpha = container.books.insert(
        sha256="alpha",
        path=Path("/tmp/alpha.pdf"),
        title="Alpha Adventures",
        format="pdf",
        page_count=10,
        status=BookStatus.READY,
    )
    beta = container.books.insert(
        sha256="beta",
        path=Path("/tmp/beta.pdf"),
        title="Beta Tales",
        format="pdf",
        page_count=10,
        status=BookStatus.READY,
    )
    return alpha.id, beta.id


def test_lexical_search_returns_matching_book(
    client: TestClient, container: AppContainer
) -> None:
    alpha_id, _ = _seed_two_books(container)
    response = client.get("/api/search", params={"q": "alpha", "mode": "lexical"})
    assert response.status_code == 200
    body = response.json()
    assert body["grouped"] is False
    assert [hit["book_id"] for hit in body["items"]] == [alpha_id]


def test_search_grouped_response(client: TestClient, container: AppContainer) -> None:
    alpha_id, _ = _seed_two_books(container)
    response = client.get(
        "/api/search",
        params={"q": "alpha", "mode": "lexical", "group_by_book": "true"},
    )
    body = response.json()
    assert body["grouped"] is True
    assert [group["book_id"] for group in body["groups"]] == [alpha_id]

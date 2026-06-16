"""Coverage for bookmark and reading-progress routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from labooke_api.container import AppContainer
from labooke_core.domain.models import BookStatus


def _book_id(container: AppContainer) -> int:
    book = container.books.insert(
        sha256="zz",
        path=Path("/tmp/zz.pdf"),
        title="ZZ",
        format="pdf",
        page_count=100,
        status=BookStatus.READY,
    )
    return book.id


def test_bookmark_round_trip(client: TestClient, container: AppContainer) -> None:
    book_id = _book_id(container)
    created = client.post(
        f"/api/books/{book_id}/bookmarks",
        json={"page_no": 5, "label": "intro", "note": "first"},
    ).json()
    assert created["page_no"] == 5

    listed = client.get(f"/api/books/{book_id}/bookmarks").json()
    assert [b["id"] for b in listed] == [created["id"]]

    patched = client.patch(
        f"/api/bookmarks/{created['id']}", json={"note": "updated"}
    ).json()
    assert patched["note"] == "updated"

    assert client.delete(f"/api/bookmarks/{created['id']}").status_code == 204
    assert client.get(f"/api/books/{book_id}/bookmarks").json() == []


def test_progress_returns_404_when_unset(
    client: TestClient, container: AppContainer
) -> None:
    book_id = _book_id(container)
    response = client.get(f"/api/books/{book_id}/progress")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "progress_not_found"


def test_progress_upserts(client: TestClient, container: AppContainer) -> None:
    book_id = _book_id(container)
    response = client.put(
        f"/api/books/{book_id}/progress", json={"page_no": 7}
    )
    assert response.status_code == 200
    assert response.json()["page_no"] == 7

    refreshed = client.put(
        f"/api/books/{book_id}/progress", json={"page_no": 9}
    ).json()
    assert refreshed["page_no"] == 9

    assert client.get(f"/api/books/{book_id}/progress").json()["page_no"] == 9


def test_progress_validates_page_no(
    client: TestClient, container: AppContainer
) -> None:
    book_id = _book_id(container)
    response = client.put(
        f"/api/books/{book_id}/progress", json={"page_no": 0}
    )
    assert response.status_code == 422

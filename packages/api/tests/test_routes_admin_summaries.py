"""Route coverage for the batch-summary and runtime-config admin endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from labooke_api.container import AppContainer
from labooke_core.domain.models import BookStatus


def _insert_book(container: AppContainer, *, sha256: str, title: str) -> int:
    return container.books.insert(
        sha256=sha256,
        path=Path(f"/tmp/{sha256}.pdf"),
        title=title,
        format="pdf",
        status=BookStatus.READY,
    ).id


def test_invalidate_clears_summaries(client: TestClient, container: AppContainer) -> None:
    book_id = _insert_book(container, sha256="a", title="Alpha")
    container.books.update_description(book_id, "A summary")

    response = client.post("/api/admin/summaries/invalidate")

    assert response.status_code == 200
    assert response.json() == {"invalidated": 1}
    assert container.books.get(book_id).description is None


def test_summarize_random_returns_candidates_without_summary(
    client: TestClient, container: AppContainer
) -> None:
    with_summary = _insert_book(container, sha256="b", title="Beta")
    container.books.update_description(with_summary, "done")
    missing = _insert_book(container, sha256="c", title="Gamma")

    response = client.post("/api/admin/summaries/random", json={"count": 5})

    assert response.status_code == 202
    assert response.json()["book_ids"] == [missing]


def test_summarize_random_rejects_count_below_one(client: TestClient) -> None:
    assert client.post("/api/admin/summaries/random", json={"count": 0}).status_code == 422


def test_summarize_batch_accepts_explicit_ids(
    client: TestClient, container: AppContainer
) -> None:
    book_id = _insert_book(container, sha256="d", title="Delta")
    response = client.post("/api/admin/summaries/batch", json={"book_ids": [book_id]})
    assert response.status_code == 202
    assert response.json()["book_ids"] == [book_id]


def test_put_config_persists_summary_pages(
    client: TestClient, container: AppContainer
) -> None:
    response = client.put("/api/admin/config", json={"llm_summary_pages": 20})
    assert response.status_code == 200
    assert response.json() == {"llm_summary_pages": 20}
    assert client.get("/api/config").json()["llm_summary_pages"] == 20


def test_put_config_null_resets_to_env_default(
    client: TestClient, container: AppContainer
) -> None:
    client.put("/api/admin/config", json={"llm_summary_pages": 20})
    response = client.put("/api/admin/config", json={"llm_summary_pages": None})
    assert response.status_code == 200
    default = container.settings.llm_summary_pages
    assert response.json()["llm_summary_pages"] == default
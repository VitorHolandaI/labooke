"""Route coverage for LLM features (summarize + ask)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from labooke_api.container import AppContainer
from labooke_core.domain.models import BookStatus
from labooke_core.services.ask_service import AskAnswer


def _insert_book(container: AppContainer, *, sha256: str, title: str) -> int:
    return container.books.insert(
        sha256=sha256,
        path=Path(f"/tmp/{sha256}.pdf"),
        title=title,
        format="pdf",
        status=BookStatus.READY,
    ).id


def test_summarize_returns_503_when_llm_unconfigured(
    client: TestClient, container: AppContainer
) -> None:
    book_id = _insert_book(container, sha256="s", title="Science")
    response = client.post(f"/api/books/{book_id}/summarize")
    assert response.status_code == 503
    assert response.json()["code"] == "llm_unavailable"


def test_ask_returns_503_when_llm_unconfigured(client: TestClient) -> None:
    response = client.post("/api/ask", json={"question": "um livro sobre ciência"})
    assert response.status_code == 503
    assert response.json()["code"] == "llm_unavailable"


def test_summarize_happy_path(client: TestClient, container: AppContainer) -> None:
    book_id = _insert_book(container, sha256="s2", title="Science")

    class _FakeSummarize:
        def summarize(self, book_id: int):
            book = container.books.get(book_id)
            return book.model_copy(update={"description": "A summary!", "author": "Jane"})

    container.summarize = _FakeSummarize()  # type: ignore[assignment]
    response = client.post(f"/api/books/{book_id}/summarize")
    assert response.status_code == 200
    assert response.json()["description"] == "A summary!"
    assert response.json()["author"] == "Jane"


def test_ask_happy_path(client: TestClient, container: AppContainer) -> None:
    book_id = _insert_book(container, sha256="a2", title="Astrofísica")
    book = container.books.get(book_id)

    class _FakeAsk:
        def ask(self, question: str):
            return AskAnswer(
                answer="Recomendo Astrofísica.",
                books=[book],
                reasons={book.id: "Explica ciência estelar para iniciantes."},
            )

    container.ask = _FakeAsk()  # type: ignore[assignment]
    response = client.post("/api/ask", json={"question": "quero um livro sobre ciência"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Recomendo Astrofísica."
    assert response.json()["books"][0]["id"] == book_id
    assert response.json()["recommendations"][0]["book"]["id"] == book_id
    assert "iniciantes" in response.json()["recommendations"][0]["reason"]

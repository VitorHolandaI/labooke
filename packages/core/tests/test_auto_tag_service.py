from pathlib import Path

import pytest
from labooke_core.domain.models import BookStatus
from labooke_core.llm import ChatMessage
from labooke_core.services.auto_tag_service import AutoTagService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.tags_repo import TagsRepo


class _FakeChatClient:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.calls: list[list[ChatMessage]] = []

    def chat(self, messages) -> str:
        self.calls.append(list(messages))
        return self._reply


@pytest.fixture
def repos():
    conn = open_db(":memory:", seed_tags=False)
    return BooksRepo(conn), TagsRepo(conn)


def _book(books: BooksRepo, *, description: str | None = "Resumo"):
    return books.insert(
        sha256="auto-tag-book",
        path=Path("/tmp/book.pdf"),
        title="Sistemas Distribuídos",
        description=description,
        format="pdf",
        status=BookStatus.READY,
    )


def test_auto_tag_attaches_only_existing_ids(repos):
    books, tags = repos
    distributed = tags.insert(name="Distribuídos", slug="distribuidos")
    security = tags.insert(name="Segurança", slug="seguranca")
    book = _book(books)
    client = _FakeChatClient(f'{{"tag_ids":[{distributed.id},999,{distributed.id},{security.id}]}}')

    attached = AutoTagService(books, tags, client).tag_book(book.id)

    assert [tag.id for tag in attached] == [distributed.id, security.id]
    assert "Resumo" in client.calls[0][1].content


def test_auto_tag_requires_a_summary_profile(repos):
    books, tags = repos
    tags.insert(name="Tecnologia", slug="tecnologia")
    book = _book(books, description=None)

    with pytest.raises(ValueError, match=f"book id={book.id}.*expected non-empty text"):
        AutoTagService(books, tags, _FakeChatClient('{"tag_ids":[]}')).tag_book(book.id)

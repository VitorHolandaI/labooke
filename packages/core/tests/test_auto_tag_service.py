from datetime import UTC, datetime
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


class _FixedClock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


_TAGGED_AT = datetime(2026, 10, 23, 9, 30, tzinfo=UTC)


def test_auto_tag_marks_the_book_as_classified(repos):
    books, tags = repos
    distributed = tags.insert(name="Distribuídos", slug="distribuidos")
    book = _book(books)
    client = _FakeChatClient(f'{{"tag_ids":[{distributed.id}]}}')

    AutoTagService(books, tags, client, clock=_FixedClock(_TAGGED_AT)).tag_book(book.id)

    assert books.get(book.id).auto_tagged_at == _TAGGED_AT


# A run where no tag fits still counts as done, or the admin list would keep
# offering the same book forever.
def test_auto_tag_marks_the_book_even_when_no_tag_fits(repos):
    books, tags = repos
    tags.insert(name="Culinária", slug="culinaria")
    book = _book(books)
    client = _FakeChatClient('{"tag_ids":[]}')

    AutoTagService(books, tags, client, clock=_FixedClock(_TAGGED_AT)).tag_book(book.id)

    assert books.get(book.id).auto_tagged_at == _TAGGED_AT


def test_auto_tag_leaves_the_mark_unset_without_a_tag_vocabulary(repos):
    books, tags = repos
    book = _book(books)
    client = _FakeChatClient('{"tag_ids":[]}')

    AutoTagService(books, tags, client, clock=_FixedClock(_TAGGED_AT)).tag_book(book.id)

    assert client.calls == []
    assert books.get(book.id).auto_tagged_at is None

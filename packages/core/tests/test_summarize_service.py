from pathlib import Path

import numpy as np
import pytest
from labooke_core.config import Settings
from labooke_core.domain.models import BookStatus, PageText
from labooke_core.llm import ChatMessage, LlmUnavailable
from labooke_core.services.summarize_service import SummarizeService, _parse_summary
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.summaries_repo import SummariesRepo


class _FakeChatClient:
    def __init__(self, reply: str):
        self._reply = reply
        self.calls: list[list[ChatMessage]] = []

    def chat(self, messages) -> str:
        self.calls.append(list(messages))
        return self._reply


class _FakeExtractor:
    def pages(self, path):
        for page_no in range(1, 4):
            yield PageText(page_no=page_no, text=f"page {page_no} content")

    def page_text(self, path, page_no):
        return f"page {page_no} content"

    def page_count(self, path):
        return 3

    def write_cover_thumbnail(self, path, destination):
        return Path(destination)


def _fake_encoder(texts):
    return np.zeros((len(texts), 384), dtype=np.float32)


@pytest.fixture
def conn():
    return open_db(":memory:", seed_tags=False)


@pytest.fixture
def books(conn):
    return BooksRepo(conn)


@pytest.fixture
def summaries(conn):
    return SummariesRepo(conn)


def _make_book(books, *, sha: str | None = None):
    return books.insert(
        sha256=sha or "abc",
        path=Path("/tmp/abc.pdf"),
        title="Some Book",
        format="pdf",
        status=BookStatus.READY,
    )


def _settings():
    return Settings(llm_base_url="http://x/v1", llm_model="m", llm_summary_pages=10)


def _service(books, summaries, client, settings=None):
    return SummarizeService(
        settings or _settings(),
        books,
        summaries,
        client,
        extractor_factory=lambda _fmt: _FakeExtractor(),
        encode_texts=_fake_encoder,
    )


def test_parse_summary_extracts_fields():
    result = _parse_summary(
        '{"author": "Jane", "summary": "About things.", "rag_summary": "topics: A, B"}'
    )
    assert result.author == "Jane"
    assert result.summary == "About things."
    assert result.rag_text == "topics: A, B"


def test_parse_summary_falls_back_to_raw_text():
    result = _parse_summary("just plain text")
    assert result.author is None
    assert result.summary == "just plain text"
    assert result.rag_text is None


def test_parse_summary_strips_markdown_fences():
    result = _parse_summary(
        '```json\n{"author": "Jane", "summary": "About X.", "rag_summary": "A, B"}\n```'
    )
    assert result.author == "Jane"
    assert result.summary == "About X."
    assert result.rag_text == "A, B"


def test_parse_summary_ignores_trailing_prose():
    result = _parse_summary('{"author": "Jane", "summary": "About X."} Espero ter ajudado!')
    assert result.author == "Jane"
    assert result.summary == "About X."


def test_summarize_writes_description_author_and_vector(books, summaries):
    client = _FakeChatClient(
        '{"author": "Jane Doe", "summary": "A science book.", "rag_summary": "science topics"}'
    )
    service = _service(books, summaries, client)
    book_id = _make_book(books).id

    updated = service.summarize(book_id)

    assert updated.description == "A science book."
    assert updated.author == "Jane Doe"
    assert updated.rag_text == "science topics"
    assert summaries.knn(query=[0.0] * 384, k=1)[0][0] == book_id
    assert client.calls[0][0].role == "system"


def test_summarize_many_isolates_failures(books, summaries):
    client = _FakeChatClient('{"author": "Jane", "summary": "S", "rag_summary": "R"}')
    service = _service(books, summaries, client)
    good = _make_book(books).id
    results = service.summarize_many([good, 9999])
    assert results[0] == (good, None)
    assert results[1][0] == 9999
    assert results[1][1] is not None


def test_pick_random_candidates_returns_missing_only(books, summaries):
    client = _FakeChatClient('{"author": "J", "summary": "S", "rag_summary": "R"}')
    service = _service(books, summaries, client)
    missing_a = _make_book(books, sha="a").id
    missing_b = _make_book(books, sha="b").id
    books.update_description(missing_a, "done")
    picked = service.pick_random_candidates(10)
    assert missing_a not in picked
    assert missing_b in picked


def test_invalidate_all_clears_summaries(books, summaries):
    client = _FakeChatClient(
        '{"author": "Jane", "summary": "S", "rag_summary": "R"}'
    )
    service = _service(books, summaries, client)
    book_id = _make_book(books).id
    service.summarize(book_id)
    assert service.invalidate_all() == 1
    assert books.get(book_id).description is None
    assert books.get(book_id).rag_text is None
    assert summaries.knn(query=[0.0] * 384, k=5) == []


def test_summarize_requires_client(books, summaries):
    service = SummarizeService(
        _settings(),
        books,
        summaries,
        None,
        extractor_factory=lambda _fmt: _FakeExtractor(),
        encode_texts=_fake_encoder,
    )
    with pytest.raises(LlmUnavailable, match="not configured"):
        service.summarize(_make_book(books).id)

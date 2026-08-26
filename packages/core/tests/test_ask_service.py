from pathlib import Path

import numpy as np
import pytest
from labooke_core.config import Settings
from labooke_core.domain.models import BookStatus
from labooke_core.llm import ChatMessage, LlmUnavailable
from labooke_core.services.ask_service import AskService, _parse_queries
from labooke_core.services.library_service import LibraryService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.progress_repo import ProgressRepo
from labooke_core.store.summaries_repo import SummariesRepo
from labooke_core.store.tags_repo import TagsRepo
from labooke_core.store.vectors_repo import VEC_DIM


class _ScriptedClient:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls: list[list[ChatMessage]] = []

    def chat(self, messages) -> str:
        self.calls.append(list(messages))
        return self._replies.pop(0)


def _fake_encoder(texts):
    return np.zeros((len(texts), VEC_DIM), dtype=np.float32)


@pytest.fixture
def conn():
    return open_db(":memory:", seed_tags=False)


@pytest.fixture
def books(conn):
    return BooksRepo(conn)


@pytest.fixture
def tags(conn):
    return TagsRepo(conn)


@pytest.fixture
def progress(conn):
    return ProgressRepo(conn)


@pytest.fixture
def summaries(conn):
    return SummariesRepo(conn)


def _make_library(books, tags, progress):
    return LibraryService(books, tags, progress)


def test_ask_retrieves_reranks_and_returns_reasons(books, tags, progress, summaries):
    book = books.insert(
        sha256="abc",
        path=Path("/tmp/abc.pdf"),
        title="Astrofísica para Iniciantes",
        format="pdf",
        status=BookStatus.READY,
        description="Uma introdução à astronomia e física estelar.",
    )
    summaries.upsert(book_id=book.id, vector=[0.1] * VEC_DIM)
    library = _make_library(books, tags, progress)
    client = _ScriptedClient(
        [
            '{"queries":["astronomia para iniciantes","livro introdutório de astrofísica"]}',
            '{"message":"Encontrei uma opção.","recommendations":'
            f'[{{"book_id":{book.id},"reason":"Introdução direta à astrofísica."}}]}}'
        ]
    )
    service = AskService(
        Settings(llm_rag_k=10),
        library,
        summaries,
        client,
        encode_texts=_fake_encoder,
    )

    result = service.ask("quero um livro sobre ciência")

    assert result.answer == "Encontrei uma opção."
    assert [b.id for b in result.books] == [book.id]
    assert result.reasons[book.id] == "Introdução direta à astrofísica."
    assert "quero um livro sobre ciência" in client.calls[0][1].content
    assert "Uma introdução à astronomia e física estelar." in client.calls[1][1].content
    assert "retrieval_profile" not in client.calls[1][1].content


def test_query_expansion_falls_back_to_original_request():
    assert _parse_queries("not JSON", "livro sobre ciência") == ["livro sobre ciência"]


def test_ask_requires_client(books, tags, progress, summaries):
    service = AskService(
        Settings(llm_rag_k=10),
        _make_library(books, tags, progress),
        summaries,
        None,
        encode_texts=_fake_encoder,
    )
    with pytest.raises(LlmUnavailable, match="not configured"):
        service.ask("qualquer pergunta")

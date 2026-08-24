from pathlib import Path

import numpy as np
import pytest
from labooke_core.config import Settings
from labooke_core.domain.models import BookStatus
from labooke_core.llm import ChatMessage, LlmUnavailable
from labooke_core.services.ask_service import AskService
from labooke_core.services.library_service import LibraryService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.progress_repo import ProgressRepo
from labooke_core.store.summaries_repo import SummariesRepo
from labooke_core.store.tags_repo import TagsRepo


class _ScriptedClient:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls: list[list[ChatMessage]] = []

    def chat(self, messages) -> str:
        self.calls.append(list(messages))
        return self._replies.pop(0)


def _fake_encoder(texts):
    return np.zeros((len(texts), 384), dtype=np.float32)


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


def test_ask_reformulates_retrieves_and_answers(books, tags, progress, summaries):
    book = books.insert(
        sha256="abc",
        path=Path("/tmp/abc.pdf"),
        title="Astrofísica para Iniciantes",
        format="pdf",
        status=BookStatus.READY,
        description="Uma introdução à astronomia e física estelar.",
    )
    summaries.upsert(book_id=book.id, vector=[0.1] * 384)
    library = _make_library(books, tags, progress)
    client = _ScriptedClient(["astrofísica", "Recomendo Astrofísica para Iniciantes."])
    service = AskService(
        Settings(llm_rag_k=10),
        library,
        summaries,
        client,
        encode_texts=_fake_encoder,
    )

    result = service.ask("quero um livro sobre ciência")

    assert result.answer == "Recomendo Astrofísica para Iniciantes."
    assert [b.id for b in result.books] == [book.id]
    assert client.calls[0][0].role == "system"


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

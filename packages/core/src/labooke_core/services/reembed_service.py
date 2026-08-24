"""Rebuild chunk/vector rows for existing books."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

from labooke_core.domain.models import Book, BookStatus
from labooke_core.embed import encode_passages
from labooke_core.services._book_embedding_pipeline import BookEmbeddingPipeline
from labooke_core.services.common import TaskRunner, inline_task_runner
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.summaries_repo import SummariesRepo


class ReembedService:
    """Refresh stored chunks and vectors for one or all books.

    Chunk vectors (content search) are rebuilt from the source pages;
    summary vectors (``vec_summaries``, used by the ask RAG) are
    re-embedded from the stored ``rag_text`` (or ``description``) with
    no LLM call.

    Example:
        >>> type(ReembedService(None, None)).__name__
        'ReembedService'
    """

    def __init__(
        self,
        books: BooksRepo,
        pipeline: BookEmbeddingPipeline,
        summaries: SummariesRepo | None = None,
        *,
        schedule_task: TaskRunner = inline_task_runner,
        encode_texts: Callable[[Sequence[str]], np.ndarray] = encode_passages,
    ) -> None:
        self._books = books
        self._pipeline = pipeline
        self._summaries = summaries
        self._schedule_task = schedule_task
        self._encode_texts = encode_texts

    def reembed_book(self, book_id: int) -> Book:
        """Mark one book as reembedding and schedule the rebuild work.

        Example:
            >>> service = ReembedService(None, None)
            >>> service.reembed_book.__name__
            'reembed_book'
        """
        self._books.set_status(book_id, status=BookStatus.REEMBEDDING, ingest_error=None)
        self._schedule_task(lambda: self._run_reembed(book_id))
        return self._books.get(book_id)

    def reembed_all(self) -> list[Book]:
        """Schedule reembedding for every stored book.

        Example:
            >>> service = ReembedService(None, None)
            >>> service.reembed_all.__name__
            'reembed_all'
        """
        return [self.reembed_book(book.id) for book in self._books.list_all()]

    def _run_reembed(self, book_id: int) -> None:
        try:
            page_count = self._pipeline.rebuild(self._books.get(book_id))
            self._books.set_status(
                book_id,
                status=BookStatus.READY,
                ingest_error=None,
                page_count=page_count,
            )
        except Exception as exc:
            self._books.set_status(book_id, status=BookStatus.FAILED, ingest_error=str(exc))
            return
        self._reembed_summary(book_id)

    def _reembed_summary(self, book_id: int) -> None:
        """Refresh the book's ``vec_summaries`` row from stored text.

        A failure here must not fail the chunk reembed, so it is
        swallowed (the ask search falls back to existing vectors).
        """
        if self._summaries is None:
            return
        try:
            book = self._books.get(book_id)
            text = book.rag_text or book.description
            if not text:
                return
            matrix = self._encode_texts([text])
            vector = [float(value) for value in matrix[0]]
            self._summaries.upsert(book_id=book_id, vector=vector)
        except Exception:
            pass

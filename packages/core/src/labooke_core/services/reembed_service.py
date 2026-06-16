"""Rebuild chunk/vector rows for existing books."""

from __future__ import annotations

from labooke_core.domain.models import Book, BookStatus
from labooke_core.services._book_embedding_pipeline import BookEmbeddingPipeline
from labooke_core.services.common import TaskRunner, inline_task_runner
from labooke_core.store.books_repo import BooksRepo


class ReembedService:
    """Refresh stored chunks and vectors for one or all books.

    Example:
        >>> type(ReembedService(None, None)).__name__
        'ReembedService'
    """

    def __init__(
        self,
        books: BooksRepo,
        pipeline: BookEmbeddingPipeline,
        *,
        schedule_task: TaskRunner = inline_task_runner,
    ) -> None:
        self._books = books
        self._pipeline = pipeline
        self._schedule_task = schedule_task

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

"""Book ingest orchestration."""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

from labooke_core.config import Settings
from labooke_core.domain.models import Book, BookStatus
from labooke_core.services._book_embedding_pipeline import BookEmbeddingPipeline
from labooke_core.services.common import (
    TaskRunner,
    file_sha256,
    format_from_path,
    inline_task_runner,
)
from labooke_core.services.library_service import LibraryService
from labooke_core.store.books_repo import BookNotFound, BooksRepo
from labooke_core.store.tags_repo import TagsRepo


class IngestService:
    """Create library rows, deduplicate uploads, and schedule extraction.

    Example:
        >>> type(IngestService(None, None, None, None)).__name__
        'IngestService'
    """

    def __init__(
        self,
        settings: Settings,
        books: BooksRepo,
        tags: TagsRepo,
        library: LibraryService,
        pipeline: BookEmbeddingPipeline,
        *,
        schedule_task: TaskRunner = inline_task_runner,
    ) -> None:
        self._settings = settings
        self._books = books
        self._tags = tags
        self._library = library
        self._pipeline = pipeline
        self._schedule_task = schedule_task

    def ingest_book(
        self,
        path: Path | str,
        tags: Sequence[int] = (),
        *,
        title: str | None = None,
        move_source: bool = False,
    ) -> Book:
        """Deduplicate by sha256, create a pending row, and schedule ingest work.

        Example:
            >>> service = IngestService(None, None, None, None, None)
            >>> service.ingest_book.__name__
            'ingest_book'
        """
        source = Path(path)
        sha256 = file_sha256(source)
        try:
            existing = self._books.get_by_sha256(sha256)
        except BookNotFound:
            return self._new_ingest(source, sha256, tags, title=title, move_source=move_source)
        self._attach_tags(existing.id, tags)
        if move_source and source.exists():
            source.unlink()
        return self._library.get_book(existing.id)

    def _new_ingest(
        self,
        source: Path,
        sha256: str,
        tag_ids: Sequence[int],
        *,
        title: str | None = None,
        move_source: bool,
    ) -> Book:
        format_name = format_from_path(source)
        destination = self._destination_path(source, sha256)
        self._stage_managed_copy(source, destination)
        book = self._books.insert(
            sha256=sha256,
            path=destination,
            title=title or source.stem,
            format=format_name,
            status=BookStatus.PENDING,
        )
        self._attach_tags(book.id, tag_ids)
        self._schedule_task(lambda: self._run_ingest(book.id, source if move_source else None))
        return self._library.get_book(book.id)

    def _attach_tags(self, book_id: int, tag_ids: Sequence[int]) -> None:
        for tag_id in tag_ids:
            self._tags.attach(book_id, tag_id)

    def _destination_path(self, source: Path, sha256: str) -> Path:
        self._settings.books_dir.mkdir(parents=True, exist_ok=True)
        return self._settings.books_dir / f"{sha256}{source.suffix.lower()}"

    def _stage_managed_copy(self, source: Path, destination: Path) -> None:
        if destination.exists():
            return
        shutil.copy2(source, destination)

    def _run_ingest(self, book_id: int, source_to_remove: Path | None) -> None:
        try:
            page_count = self._pipeline.rebuild(self._books.get(book_id))
            self._books.set_status(
                book_id,
                status=BookStatus.READY,
                ingest_error=None,
                page_count=page_count,
            )
            if source_to_remove is not None and source_to_remove.exists():
                source_to_remove.unlink()
        except Exception as exc:
            self._books.set_status(book_id, status=BookStatus.FAILED, ingest_error=str(exc))

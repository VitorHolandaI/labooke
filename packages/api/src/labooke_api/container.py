"""Long-lived object graph wired during the API lifespan.

The container owns the SQLite connection, repositories, and services
whose lifetime matches the application process. Request-scoped wiring
(``IngestService``, ``ReembedService``, ``LibraryScanner``) is built
per-request in :mod:`labooke_api.deps` so background tasks attach to
the active ``BackgroundTasks`` queue.
"""

from __future__ import annotations

from dataclasses import dataclass

from labooke_core.config import Settings
from labooke_core.services import (
    LibraryService,
    ReaderService,
    SearchService,
    SnippetService,
)
from labooke_core.services._book_embedding_pipeline import BookEmbeddingPipeline
from labooke_core.store.bookmarks_repo import BookmarksRepo
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.db import LockedConnection, open_db
from labooke_core.store.progress_repo import ProgressRepo
from labooke_core.store.tags_repo import TagsRepo
from labooke_core.store.vectors_repo import VectorsRepo


@dataclass(slots=True)
class AppContainer:
    """Process-wide singletons shared across requests."""

    settings: Settings
    conn: LockedConnection
    books: BooksRepo
    tags: TagsRepo
    chunks: ChunksRepo
    vectors: VectorsRepo
    bookmarks: BookmarksRepo
    progress: ProgressRepo
    pipeline: BookEmbeddingPipeline
    library: LibraryService
    reader: ReaderService
    snippets: SnippetService
    search: SearchService

    def close(self) -> None:
        """Close the owned SQLite connection."""
        self.conn.close()


def build_container(settings: Settings) -> AppContainer:
    """Open the DB and assemble repositories and long-lived services.

    Example:
        >>> from labooke_core.config import Settings
        >>> from pathlib import Path
        >>> container = build_container(Settings(data_dir=Path('/tmp/_lb_demo')))
        >>> type(container.search).__name__
        'SearchService'
        >>> container.close()
    """
    conn = open_db(settings.db_path)
    books = BooksRepo(conn)
    tags = TagsRepo(conn)
    chunks = ChunksRepo(conn)
    vectors = VectorsRepo(conn)
    bookmarks = BookmarksRepo(conn)
    progress = ProgressRepo(conn)
    library = LibraryService(books, tags)
    reader = ReaderService(books)
    snippets = SnippetService(books)
    search = SearchService(library, chunks, vectors, snippets, books)
    pipeline = BookEmbeddingPipeline(books, chunks, vectors)
    return AppContainer(
        settings=settings,
        conn=conn,
        books=books,
        tags=tags,
        chunks=chunks,
        vectors=vectors,
        bookmarks=bookmarks,
        progress=progress,
        pipeline=pipeline,
        library=library,
        reader=reader,
        snippets=snippets,
        search=search,
    )

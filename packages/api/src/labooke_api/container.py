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
from labooke_core.llm import ChatClient, build_chat_client
from labooke_core.services import (
    AskService,
    LibraryService,
    ReaderService,
    SearchService,
    SnippetService,
    SummarizeService,
)
from labooke_core.services._book_embedding_pipeline import (
    BookEmbeddingPipeline,
)
from labooke_core.store.bookmarks_repo import BookmarksRepo
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.db import LockedConnection, open_db
from labooke_core.store.progress_repo import ProgressRepo
from labooke_core.store.settings_repo import SettingsRepo
from labooke_core.store.summaries_repo import SummariesRepo
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
    summaries: SummariesRepo
    settings_repo: SettingsRepo
    bookmarks: BookmarksRepo
    progress: ProgressRepo
    pipeline: BookEmbeddingPipeline
    library: LibraryService
    reader: ReaderService
    snippets: SnippetService
    search: SearchService
    chat_client: ChatClient | None
    summarize: SummarizeService
    ask: AskService

    def close(self) -> None:
        """Close the owned SQLite connection."""
        self.conn.close()


def build_container(settings: Settings) -> AppContainer:
    """Open the DB and assemble repositories and long-lived services.

    Example:
        >>> from labooke_core.config import Settings
        >>> from pathlib import Path
        >>> settings = Settings(data_dir=Path("/tmp/_lb_demo"))
        >>> container = build_container(settings)
        >>> type(container.search).__name__
        'SearchService'
        >>> container.close()
    """
    conn = open_db(settings.db_path)
    books = BooksRepo(conn)
    tags = TagsRepo(conn)
    chunks = ChunksRepo(conn)
    vectors = VectorsRepo(conn)
    summaries = SummariesRepo(conn)
    settings_repo = SettingsRepo(conn)
    bookmarks = BookmarksRepo(conn)
    progress = ProgressRepo(conn)
    library = LibraryService(books, tags, progress)
    reader = ReaderService(books)
    snippets = SnippetService(books)
    search = SearchService(library, chunks, vectors, snippets, books)
    pipeline = BookEmbeddingPipeline(books, chunks, vectors)
    chat_client = build_chat_client(settings)
    summarize = SummarizeService(
        settings,
        books,
        summaries,
        chat_client,
        pages_provider=lambda: int(
            settings_repo.get("llm_summary_pages")
            or settings.llm_summary_pages
        ),
    )
    ask = AskService(settings, library, summaries, chat_client)
    return AppContainer(
        settings=settings,
        conn=conn,
        books=books,
        tags=tags,
        chunks=chunks,
        vectors=vectors,
        summaries=summaries,
        settings_repo=settings_repo,
        bookmarks=bookmarks,
        progress=progress,
        pipeline=pipeline,
        library=library,
        reader=reader,
        snippets=snippets,
        search=search,
        chat_client=chat_client,
        summarize=summarize,
        ask=ask,
    )

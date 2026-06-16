"""Service container for the Bible CLI."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from labooke_core.config import Settings
from labooke_core.embed import encode as default_encode
from labooke_core.services._book_embedding_pipeline import BookEmbeddingPipeline
from labooke_core.services.ingest_service import IngestService
from labooke_core.services.library_scanner import LibraryScanner
from labooke_core.services.library_service import LibraryService
from labooke_core.services.reader_service import ReaderService
from labooke_core.services.search_service import SearchService
from labooke_core.services.snippet_service import SnippetService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.db import LockedConnection, open_db
from labooke_core.store.tags_repo import TagsRepo
from labooke_core.store.vectors_repo import VectorsRepo

from labooke_bible._history import HistoryStore

EncodeFunc = Callable[[Sequence[str]], Any]


class Container:
    """Holds all services wired to a single DB connection.

    Pass *settings* to override Settings() defaults (useful in tests).
    Pass *encode_texts* to stub out the embedding model (useful in tests).

    Example:
        >>> from labooke_core.store.db import open_db
        >>> c = Container(open_db(":memory:"))
        >>> type(c.tags).__name__
        'TagsRepo'
    """

    def __init__(
        self,
        conn: LockedConnection,
        *,
        settings: Settings | None = None,
        encode_texts: EncodeFunc | None = None,
    ) -> None:
        cfg = settings or Settings()
        encoder = encode_texts or default_encode

        self.tags = TagsRepo(conn)
        self.books_repo = BooksRepo(conn)
        self.library = LibraryService(self.books_repo, self.tags)
        self.reader = ReaderService(self.books_repo)

        chunks = ChunksRepo(conn)
        vectors = VectorsRepo(conn)
        snippets = SnippetService(self.books_repo)
        self.search = SearchService(self.library, chunks, vectors, snippets, encode_texts=encoder)

        pipeline = BookEmbeddingPipeline(self.books_repo, chunks, vectors, encode_texts=encoder)
        ingest = IngestService(cfg, self.books_repo, self.tags, self.library, pipeline)
        self.scanner = LibraryScanner(cfg, ingest)

        self.history = HistoryStore(cfg.data_dir / "bible_history.txt")

    @classmethod
    def from_db_path(cls, path: str) -> Container:
        """Open the DB at *path* and return a wired container."""
        return cls(open_db(path))

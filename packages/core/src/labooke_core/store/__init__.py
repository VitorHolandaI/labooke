"""Storage layer: SQLite + sqlite-vec, migrator, repositories."""

from labooke_core.store.bookmarks_repo import BookmarkNotFound, BookmarksRepo
from labooke_core.store.books_repo import BookNotFound, BooksRepo
from labooke_core.store.chunks_repo import ChunkNotFound, ChunksRepo
from labooke_core.store.db import MIGRATIONS_DIR, connect, open_db
from labooke_core.store.migrator import (
    apply_migration,
    current_version,
    migrate,
    parse_version,
    pending_migrations,
)
from labooke_core.store.progress_repo import ProgressRepo
from labooke_core.store.seed_tags import SEED_TAGS, ensure_seed_tags
from labooke_core.store.tags_repo import TagNotFound, TagsRepo
from labooke_core.store.vectors_repo import VEC_DIM, VectorsRepo

__all__ = [
    "MIGRATIONS_DIR",
    "SEED_TAGS",
    "VEC_DIM",
    "BookNotFound",
    "BookmarkNotFound",
    "BookmarksRepo",
    "BooksRepo",
    "ChunkNotFound",
    "ChunksRepo",
    "ProgressRepo",
    "TagNotFound",
    "TagsRepo",
    "VectorsRepo",
    "apply_migration",
    "connect",
    "current_version",
    "ensure_seed_tags",
    "migrate",
    "open_db",
    "parse_version",
    "pending_migrations",
]

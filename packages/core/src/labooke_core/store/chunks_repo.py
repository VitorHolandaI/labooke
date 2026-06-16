"""Persistence for :class:`Chunk` rows.

A chunk is a contiguous page range of a book; each row corresponds
1:1 to one embedding stored in ``vec_chunks``. There is no text
column — text is re-extracted from the original file when needed.

See decisions/0001-storage-no-text-in-db.md and
decisions/0004-chunk-pages-env-var.md.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import TYPE_CHECKING

from labooke_core.domain.models import Chunk
from labooke_core.store._rowid import last_insert_id

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection

_CHUNK_COLUMNS = "id, book_id, page_start, page_end, text"


def _row_to_chunk(row: sqlite3.Row | tuple) -> Chunk:
    """Map a ``chunks`` row (in column order ``_CHUNK_COLUMNS``) to a Chunk."""
    return Chunk(id=row[0], book_id=row[1], page_start=row[2], page_end=row[3], text=row[4] or "")


class ChunkNotFound(LookupError):
    """Raised when a chunk lookup by id fails."""


class ChunksRepo:
    """Insert, list, and delete chunk rows for a book.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> from labooke_core.store.books_repo import BooksRepo
        >>> conn = open_db(":memory:")
        >>> book = BooksRepo(conn).insert(
        ...     sha256="a", path="/tmp/a.pdf", title="A", format="pdf"
        ... )
        >>> repo = ChunksRepo(conn)
        >>> repo.insert(book_id=book.id, page_start=1, page_end=10).page_end
        10
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def insert(self, *, book_id: int, page_start: int, page_end: int, text: str = "") -> Chunk:
        """Insert a single chunk and return it.

        Raises:
            ValueError: if ``page_end < page_start`` or either is < 1.
        """
        _validate_range(page_start, page_end)
        cursor = self._conn.execute(
            "INSERT INTO chunks (book_id, page_start, page_end, text) VALUES (?, ?, ?, ?)",
            (book_id, page_start, page_end, text),
        )
        self._conn.commit()
        return self.get(last_insert_id(cursor))

    def insert_many(
        self, book_id: int, ranges: Iterable[tuple[int, int, str]]
    ) -> list[Chunk]:
        """Insert multiple chunks for a single book in one transaction.

        ``ranges`` is an iterable of ``(page_start, page_end, text)`` triples.
        Returns the inserted chunks in input order. Empty input returns
        an empty list.
        """
        rows = list(ranges)
        if not rows:
            return []
        for start, end, _ in rows:
            _validate_range(start, end)
        ids: list[int] = []
        with self._conn:
            for start, end, text in rows:
                cursor = self._conn.execute(
                    "INSERT INTO chunks (book_id, page_start, page_end, text) VALUES (?, ?, ?, ?)",
                    (book_id, start, end, text),
                )
                ids.append(last_insert_id(cursor))
        return [self.get(i) for i in ids]

    def get(self, chunk_id: int) -> Chunk:
        """Return the chunk with ``chunk_id`` or raise :class:`ChunkNotFound`."""
        row = self._conn.execute(
            f"SELECT {_CHUNK_COLUMNS} FROM chunks WHERE id = ?", (chunk_id,)
        ).fetchone()
        if row is None:
            raise ChunkNotFound(f"no chunk with id={chunk_id}")
        return _row_to_chunk(row)

    def list_for_book(self, book_id: int) -> list[Chunk]:
        """Return every chunk for a book ordered by page_start."""
        rows = self._conn.execute(
            f"SELECT {_CHUNK_COLUMNS} FROM chunks WHERE book_id = ? "
            "ORDER BY page_start",
            (book_id,),
        ).fetchall()
        return [_row_to_chunk(r) for r in rows]

    def delete_for_book(self, book_id: int) -> int:
        """Delete all chunks for a book; returns the number removed.

        Used by the re-embed flow before re-inserting fresh chunks.
        """
        cursor = self._conn.execute(
            "DELETE FROM chunks WHERE book_id = ?", (book_id,)
        )
        self._conn.commit()
        return int(cursor.rowcount)


def _validate_range(page_start: int, page_end: int) -> None:
    if page_start < 1 or page_end < 1:
        raise ValueError(
            f"page numbers must be >= 1, got start={page_start}, end={page_end}"
        )
    if page_end < page_start:
        raise ValueError(
            f"page_end ({page_end}) must be >= page_start ({page_start})"
        )

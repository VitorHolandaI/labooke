"""Persistence for :class:`ReadingProgress` rows.

One row per book records the last page the user read. Progress is
upserted (the row is created on first set, updated thereafter) so
callers don't need to distinguish first read from later reads.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import TYPE_CHECKING

from labooke_core.domain.models import ReadingProgress

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection


def _row_to_progress(row: sqlite3.Row | tuple) -> ReadingProgress:
    """Map a ``reading_progress`` row to a :class:`ReadingProgress`."""
    return ReadingProgress(
        book_id=row[0],
        page_no=row[1],
        updated_at=datetime.fromisoformat(str(row[2])),
    )


class ProgressRepo:
    """Set, fetch, and clear the user's last-read page per book.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> from labooke_core.store.books_repo import BooksRepo
        >>> conn = open_db(":memory:")
        >>> book = BooksRepo(conn).insert(
        ...     sha256="a", path="/tmp/a.pdf", title="A", format="pdf"
        ... )
        >>> repo = ProgressRepo(conn)
        >>> repo.set(book_id=book.id, page_no=42).page_no
        42
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def set(self, *, book_id: int, page_no: int) -> ReadingProgress:
        """Insert-or-update the progress row for ``book_id``.

        ``updated_at`` is refreshed to ``CURRENT_TIMESTAMP`` on every
        call.

        Raises:
            ValueError: if ``page_no < 1``.
        """
        if page_no < 1:
            raise ValueError(f"page_no must be >= 1, got {page_no}")
        self._conn.execute(
            "INSERT INTO reading_progress (book_id, page_no, updated_at) "
            "VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(book_id) DO UPDATE SET "
            "  page_no = excluded.page_no, "
            "  updated_at = CURRENT_TIMESTAMP",
            (book_id, page_no),
        )
        self._conn.commit()
        progress = self.get(book_id)
        assert progress is not None  # we just upserted
        return progress

    def get(self, book_id: int) -> ReadingProgress | None:
        """Return the progress for ``book_id``, or ``None`` if none exists."""
        row = self._conn.execute(
            "SELECT book_id, page_no, updated_at FROM reading_progress WHERE book_id = ?",
            (book_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_progress(row)

    def clear(self, book_id: int) -> None:
        """Forget the progress for a book. No-op if no row exists."""
        self._conn.execute(
            "DELETE FROM reading_progress WHERE book_id = ?", (book_id,)
        )
        self._conn.commit()

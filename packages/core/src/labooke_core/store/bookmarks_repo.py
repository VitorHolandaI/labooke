"""Persistence for :class:`Bookmark` rows.

A bookmark is a user-saved pointer to a specific page of a book,
with an optional label and free-form note. Highlights (text-range
overlays) are deferred to v2; see decisions/0011.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from labooke_core.domain.models import Bookmark
from labooke_core.store._rowid import last_insert_id

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection

_BOOKMARK_COLUMNS = "id, book_id, page_no, label, note"


def _row_to_bookmark(row: sqlite3.Row | tuple) -> Bookmark:
    """Map a ``bookmarks`` row (in column order ``_BOOKMARK_COLUMNS``) to a Bookmark."""
    return Bookmark(id=row[0], book_id=row[1], page_no=row[2], label=row[3], note=row[4])


class BookmarkNotFound(LookupError):
    """Raised when a bookmark lookup by id fails."""


class BookmarksRepo:
    """Insert, list, update, and delete bookmarks.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> from labooke_core.store.books_repo import BooksRepo
        >>> conn = open_db(":memory:")
        >>> book = BooksRepo(conn).insert(
        ...     sha256="a", path="/tmp/a.pdf", title="A", format="pdf"
        ... )
        >>> repo = BookmarksRepo(conn)
        >>> bm = repo.insert(book_id=book.id, page_no=12, label="intro")
        >>> repo.get(bm.id).label
        'intro'
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def insert(
        self,
        *,
        book_id: int,
        page_no: int,
        label: str,
        note: str | None = None,
    ) -> Bookmark:
        """Insert a bookmark and return it.

        Raises:
            ValueError: if ``page_no < 1``.
        """
        if page_no < 1:
            raise ValueError(f"page_no must be >= 1, got {page_no}")
        cursor = self._conn.execute(
            "INSERT INTO bookmarks (book_id, page_no, label, note) VALUES (?, ?, ?, ?)",
            (book_id, page_no, label, note),
        )
        self._conn.commit()
        return self.get(last_insert_id(cursor))

    def get(self, bookmark_id: int) -> Bookmark:
        """Return the bookmark with ``bookmark_id`` or raise :class:`BookmarkNotFound`."""
        row = self._conn.execute(
            f"SELECT {_BOOKMARK_COLUMNS} FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        if row is None:
            raise BookmarkNotFound(f"no bookmark with id={bookmark_id}")
        return _row_to_bookmark(row)

    def list_for_book(self, book_id: int) -> list[Bookmark]:
        """Return bookmarks for a book ordered by page number, then id."""
        rows = self._conn.execute(
            f"SELECT {_BOOKMARK_COLUMNS} FROM bookmarks WHERE book_id = ? "
            "ORDER BY page_no, id",
            (book_id,),
        ).fetchall()
        return [_row_to_bookmark(r) for r in rows]

    def update_note(self, bookmark_id: int, note: str | None) -> Bookmark:
        """Replace the note on a bookmark. Returns the updated bookmark."""
        self._conn.execute(
            "UPDATE bookmarks SET note = ? WHERE id = ?", (note, bookmark_id)
        )
        self._conn.commit()
        return self.get(bookmark_id)

    def delete(self, bookmark_id: int) -> None:
        """Remove a bookmark. No-op if it doesn't exist."""
        self._conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        self._conn.commit()

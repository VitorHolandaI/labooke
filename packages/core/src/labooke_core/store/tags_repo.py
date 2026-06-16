"""Persistence for :class:`Tag` rows.

Tags are flat (no hierarchy in v1; see decisions/0002) and have no
``created_at`` or ``kind`` columns — the model is intentionally
minimal. Slug is unique and acts as the human-readable identifier.
"""

from __future__ import annotations

import contextlib
import sqlite3
from typing import TYPE_CHECKING

from labooke_core.domain.models import Tag
from labooke_core.store._rowid import last_insert_id

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection

_TAG_COLUMNS = "id, name, slug, color"


def _row_to_tag(row: sqlite3.Row | tuple) -> Tag:
    """Map a ``tags`` row (in column order ``_TAG_COLUMNS``) to a Tag."""
    if len(row) < 4:
        raise ValueError(f"malformed tag row (expected 4 columns, got {len(row)}): {tuple(row)}")
    return Tag(id=row[0], name=row[1], slug=row[2], color=row[3])


class TagNotFound(LookupError):
    """Raised when a tag lookup by id or slug fails."""


class TagsRepo:
    """Insert, fetch, rename, recolor, and delete tag rows.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> repo = TagsRepo(open_db(":memory:"))
        >>> tag = repo.insert(name="Linux", slug="linux")
        >>> repo.get_by_slug("linux").name
        'Linux'
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def insert(self, *, name: str, slug: str, color: str = "#888888") -> Tag:
        """Insert a tag and return it. Slug must be unique."""
        cursor = self._conn.execute(
            "INSERT INTO tags (name, slug, color) VALUES (?, ?, ?)",
            (name, slug, color),
        )
        self._conn.commit()
        return self.get(last_insert_id(cursor))

    def get(self, tag_id: int) -> Tag:
        """Return the tag with ``tag_id`` or raise :class:`TagNotFound`."""
        row = self._conn.execute(
            f"SELECT {_TAG_COLUMNS} FROM tags WHERE id = ?", (tag_id,)
        ).fetchone()
        if row is None:
            raise TagNotFound(f"no tag with id={tag_id}")
        return _row_to_tag(row)

    def get_by_slug(self, slug: str) -> Tag:
        """Return the tag with ``slug`` or raise :class:`TagNotFound`."""
        row = self._conn.execute(
            f"SELECT {_TAG_COLUMNS} FROM tags WHERE slug = ?", (slug,)
        ).fetchone()
        if row is None:
            raise TagNotFound(f"no tag with slug={slug!r}")
        return _row_to_tag(row)

    def list_all(self) -> list[Tag]:
        """Return every tag, ordered by name (case-insensitive)."""
        rows = self._conn.execute(
            f"SELECT {_TAG_COLUMNS} FROM tags ORDER BY LOWER(name)"
        ).fetchall()
        return [_row_to_tag(r) for r in rows]

    def rename(self, tag_id: int, new_name: str) -> Tag:
        """Update the tag's ``name`` (slug stays put). Returns the updated tag."""
        self._conn.execute("UPDATE tags SET name = ? WHERE id = ?", (new_name, tag_id))
        self._conn.commit()
        return self.get(tag_id)

    def recolor(self, tag_id: int, color: str) -> Tag:
        """Update the tag's ``color``. Returns the updated tag."""
        self._conn.execute("UPDATE tags SET color = ? WHERE id = ?", (color, tag_id))
        self._conn.commit()
        return self.get(tag_id)

    def delete(self, tag_id: int) -> None:
        """Remove a tag and cascade-clean its ``book_tags`` rows.

        No-op if the tag does not exist.
        """
        self._conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        self._conn.commit()

    # ---------- book ↔ tag attachments ----------

    def attach(self, book_id: int, tag_id: int) -> None:
        """Link a tag to a book. Re-attaching is a no-op (PK collision ignored)."""
        self._conn.execute(
            "INSERT OR IGNORE INTO book_tags (book_id, tag_id) VALUES (?, ?)",
            (book_id, tag_id),
        )
        self._conn.commit()

    def detach(self, book_id: int, tag_id: int) -> None:
        """Remove a tag from a book. No-op if the link doesn't exist."""
        self._conn.execute(
            "DELETE FROM book_tags WHERE book_id = ? AND tag_id = ?",
            (book_id, tag_id),
        )
        self._conn.commit()

    def for_book(self, book_id: int) -> list[Tag]:
        """Return tags currently attached to ``book_id``, sorted by name."""
        rows = self._conn.execute(
            f"SELECT t.{', t.'.join(_TAG_COLUMNS.split(', '))} "
            "FROM tags t "
            "JOIN book_tags bt ON bt.tag_id = t.id "
            "WHERE bt.book_id = ? "
            "ORDER BY LOWER(t.name)",
            (book_id,),
        ).fetchall()
        tags = []
        for r in rows:
            with contextlib.suppress(ValueError, IndexError):
                tags.append(_row_to_tag(r))
        return tags

    # ---------- maintenance ----------

    def merge(self, source_id: int, target_id: int) -> None:
        """Move every link from ``source_id`` to ``target_id`` and drop the source.

        Re-attaches use ``INSERT OR IGNORE`` so books already tagged
        with the target keep a single link. The operation runs in a
        single transaction.

        Raises:
            ValueError: if ``source_id == target_id``.
        """
        if source_id == target_id:
            raise ValueError(f"cannot merge tag id={source_id} into itself")
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO book_tags (book_id, tag_id) "
                "SELECT book_id, ? FROM book_tags WHERE tag_id = ?",
                (target_id, source_id),
            )
            self._conn.execute("DELETE FROM book_tags WHERE tag_id = ?", (source_id,))
            self._conn.execute("DELETE FROM tags WHERE id = ?", (source_id,))

    def counts(self) -> list[tuple[Tag, int]]:
        """Return ``(tag, book_count)`` for every tag, sorted by name.

        Tags with zero attached books are included with count 0.
        """
        rows = self._conn.execute(
            f"SELECT t.{', t.'.join(_TAG_COLUMNS.split(', '))}, "
            "COUNT(bt.book_id) AS cnt "
            "FROM tags t "
            "LEFT JOIN book_tags bt ON bt.tag_id = t.id "
            "GROUP BY t.id "
            "ORDER BY LOWER(t.name)"
        ).fetchall()
        return [(_row_to_tag(r[:4]), int(r[4])) for r in rows]

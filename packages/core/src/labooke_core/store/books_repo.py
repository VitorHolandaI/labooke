"""Persistence for :class:`Book` rows.

Repositories take a SQLite ``Connection`` via the constructor (no
globals, no module-level state) so callers can wire in test
connections, separate threads, or transaction scopes as they see fit.

Tags are not loaded in this module; callers compose with
``TagsRepo.for_books`` when they need them.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from labooke_core.domain.models import Book, BookStatus
from labooke_core.store._rowid import last_insert_id

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection

_BOOK_COLUMNS = (
    "id, sha256, path, title, author, description, format, page_count, status, ingest_error"
)


def _row_to_book(row: sqlite3.Row | tuple) -> Book:
    """Map a ``books`` row (in column order ``_BOOK_COLUMNS``) to a Book."""
    return Book(
        id=row[0],
        sha256=row[1],
        path=Path(row[2]) if row[2] is not None else None,
        title=row[3],
        author=row[4],
        description=row[5],
        format=row[6],
        page_count=row[7],
        status=BookStatus(row[8]),
        ingest_error=row[9],
        tags=[],
    )


class BookNotFound(LookupError):
    """Raised when a book lookup by id fails."""


def _normalize_query(q: str | None) -> str | None:
    """Return a trimmed case-insensitive query or ``None`` when blank."""
    if q is None:
        return None
    normalized = q.strip().lower()
    return normalized or None


def _unique_ids(values: Sequence[int]) -> tuple[int, ...]:
    """Drop duplicate ids while preserving the original order."""
    return tuple(dict.fromkeys(values))


def _placeholders(values: Sequence[object]) -> str:
    """Return a placeholder list sized for ``values``."""
    return ", ".join("?" for _ in values)


def _validate_tag_mode(tag_mode: str) -> None:
    """Reject unsupported tag-match modes."""
    if tag_mode not in {"all", "any"}:
        raise ValueError(f"invalid tag_mode={tag_mode!r}; expected 'all' or 'any'")


def _include_clause(tags: Sequence[int], tag_mode: str) -> tuple[str, list[object]]:
    """Build the SQL fragment for required tag matches."""
    _validate_tag_mode(tag_mode)
    if not tags:
        return "", []
    placeholders = _placeholders(tags)
    if tag_mode == "any":
        return (
            f"b.id IN (SELECT book_id FROM book_tags WHERE tag_id IN ({placeholders}))",
            list(tags),
        )
    if tag_mode == "all":
        return (
            "b.id IN (SELECT book_id FROM book_tags WHERE tag_id IN "
            f"({placeholders}) GROUP BY book_id HAVING COUNT(DISTINCT tag_id) = ?)",
            [*tags, len(tags)],
        )
    return "", []


def _exclude_clause(exclude: Sequence[int]) -> tuple[str, list[object]]:
    """Build the SQL fragment for tag exclusions."""
    if not exclude:
        return "", []
    placeholders = _placeholders(exclude)
    return (
        f"b.id NOT IN (SELECT book_id FROM book_tags WHERE tag_id IN ({placeholders}))",
        list(exclude),
    )


def _query_clause(q: str | None) -> tuple[str, list[object]]:
    """Build the SQL fragment for lexical title/path matching."""
    normalized = _normalize_query(q)
    if normalized is None:
        return "", []
    like = f"%{normalized}%"
    return "(LOWER(b.title) LIKE ? OR LOWER(b.path) LIKE ?)", [like, like]


def _find_statement(
    *, tags: Sequence[int], tag_mode: str, exclude: Sequence[int], q: str | None
) -> tuple[str, list[object]]:
    """Assemble the ``BooksRepo.find`` statement and bind parameters."""
    clauses: list[str] = []
    params: list[object] = []
    for clause, clause_params in (
        _include_clause(tags, tag_mode),
        _exclude_clause(exclude),
        _query_clause(q),
    ):
        if clause:
            clauses.append(clause)
            params.extend(clause_params)
    statement = f"SELECT {_BOOK_COLUMNS} FROM books b"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    return statement + " ORDER BY b.id", params


class BooksRepo:
    """Insert, fetch, and delete book metadata rows.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> repo = BooksRepo(open_db(":memory:"))
        >>> book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
        >>> repo.get(book.id).title
        'X'
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def insert(
        self,
        *,
        sha256: str,
        path: Path | str,
        title: str,
        format: str,
        author: str | None = None,
        description: str | None = None,
        page_count: int = 0,
        status: BookStatus = BookStatus.PENDING,
    ) -> Book:
        """Insert a new book row and return the persisted :class:`Book`.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf").id
            1
        """
        cursor = self._conn.execute(
            "INSERT INTO books "
            "(sha256, path, title, author, description, format, page_count, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                sha256,
                str(path),
                title,
                author,
                description,
                format,
                page_count,
                status.value,
            ),
        )
        self._conn.commit()
        return self.get(last_insert_id(cursor))

    def get(self, book_id: int) -> Book:
        """Fetch a book by id or raise :class:`BookNotFound`.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
            >>> repo.get(book.id).sha256
            'abc'
        """
        row = self._conn.execute(
            f"SELECT {_BOOK_COLUMNS} FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        if row is None:
            raise BookNotFound(f"no book with id={book_id}")
        return _row_to_book(row)

    def get_by_sha256(self, sha256: str) -> Book:
        """Fetch a book by sha256 or raise :class:`BookNotFound`.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> _ = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
            >>> repo.get_by_sha256("abc").title
            'X'
        """
        row = self._conn.execute(
            f"SELECT {_BOOK_COLUMNS} FROM books WHERE sha256 = ?", (sha256,)
        ).fetchone()
        if row is None:
            raise BookNotFound(f"no book with sha256={sha256!r}")
        return _row_to_book(row)

    def list_all(self) -> list[Book]:
        """List every stored book ordered by insertion id.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> _ = repo.insert(sha256="a", path="/tmp/a.pdf", title="A", format="pdf")
            >>> [book.title for book in repo.list_all()]
            ['A']
        """
        rows = self._conn.execute(f"SELECT {_BOOK_COLUMNS} FROM books ORDER BY id").fetchall()
        return [_row_to_book(r) for r in rows]

    def list_missing_description(self) -> list[Book]:
        """List books that have no LLM summary yet (empty ``description``).

        Used by the batch summarize flow to pick candidates without
        re-summarizing books that already have one.
        """
        rows = self._conn.execute(
            f"SELECT {_BOOK_COLUMNS} FROM books "
            "WHERE description IS NULL OR description = '' ORDER BY id"
        ).fetchall()
        return [_row_to_book(r) for r in rows]

    def find(
        self,
        *,
        tags: Sequence[int] = (),
        tag_mode: str = "all",
        exclude: Sequence[int] = (),
        q: str | None = None,
    ) -> list[Book]:
        """List books filtered by tags and optional lexical search.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> repo.find()
            []
        """
        statement, params = _find_statement(
            tags=_unique_ids(tags),
            tag_mode=tag_mode,
            exclude=_unique_ids(exclude),
            q=q,
        )
        rows = self._conn.execute(statement, params).fetchall()
        return [_row_to_book(r) for r in rows]

    def set_status(
        self,
        book_id: int,
        *,
        status: BookStatus,
        ingest_error: str | None = None,
        page_count: int | None = None,
    ) -> Book:
        """Update ingest status fields and return the refreshed book row.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
            >>> repo.set_status(book.id, status=BookStatus.READY).status
            <BookStatus.READY: 'ready'>
        """
        resolved_page_count = page_count if page_count is not None else self.get(book_id).page_count
        self._conn.execute(
            "UPDATE books SET status = ?, ingest_error = ?, page_count = ? WHERE id = ?",
            (status.value, ingest_error, resolved_page_count, book_id),
        )
        self._conn.commit()
        return self.get(book_id)

    def update_title(self, book_id: int, title: str) -> Book:
        """Rename a book and return the refreshed row.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
            >>> repo.update_title(book.id, "Y").title
            'Y'
        """
        normalized = title.strip()
        if not normalized:
            raise ValueError("title must be non-empty")
        self.get(book_id)
        self._conn.execute("UPDATE books SET title = ? WHERE id = ?", (normalized, book_id))
        self._conn.commit()
        return self.get(book_id)

    def update_author(self, book_id: int, author: str | None) -> Book:
        """Set or clear a book's author and return the refreshed row.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
            >>> repo.update_author(book.id, "Jane").author
            'Jane'
        """
        self.get(book_id)
        self._conn.execute("UPDATE books SET author = ? WHERE id = ?", (author, book_id))
        self._conn.commit()
        return self.get(book_id)

    def update_description(self, book_id: int, description: str | None) -> Book:
        """Set or clear a book's description and return the refreshed row.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
            >>> repo.update_description(book.id, "A summary").description
            'A summary'
        """
        self.get(book_id)
        self._conn.execute("UPDATE books SET description = ? WHERE id = ?", (description, book_id))
        self._conn.commit()
        return self.get(book_id)

    def delete(self, book_id: int) -> None:
        """Delete a book row and its FK-owned children when present.

        Cascades via the FK constraints to ``book_tags``, ``chunks``,
        ``bookmarks``, and ``reading_progress``.

        Example:
            >>> from labooke_core.store.db import open_db
            >>> repo = BooksRepo(open_db(":memory:", seed_tags=False))
            >>> book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
            >>> repo.delete(book.id)
            >>> repo.list_all()
            []
        """
        self._conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self._conn.commit()

    def search_fts(self, query: str, *, book_ids: Sequence[int] | None = None) -> list[int]:
        """FTS5 content search — returns book IDs ordered by relevance.

        Searches chunk text via chunks_fts (falling back to books_fts title
        search if chunks_fts is unavailable). Returns an empty list if FTS5
        is unavailable or query is blank.
        """
        if not query.strip():
            return []
        try:
            return self._search_chunks_fts(query, book_ids=book_ids)
        except Exception:
            pass
        try:
            return self._search_books_fts(query, book_ids=book_ids)
        except Exception:
            return []

    def _search_chunks_fts(self, query: str, *, book_ids: Sequence[int] | None) -> list[int]:
        if book_ids is None:
            rows = self._conn.execute(
                "SELECT DISTINCT c.book_id FROM chunks_fts f "
                "JOIN chunks c ON c.id = f.rowid "
                "WHERE chunks_fts MATCH ? ORDER BY rank",
                (query,),
            ).fetchall()
        else:
            ids = list(book_ids)
            if not ids:
                return []
            placeholders = ",".join("?" * len(ids))
            rows = self._conn.execute(
                "SELECT DISTINCT c.book_id FROM chunks_fts f "
                "JOIN chunks c ON c.id = f.rowid "
                f"WHERE chunks_fts MATCH ? AND c.book_id IN ({placeholders}) ORDER BY rank",
                (query, *ids),
            ).fetchall()
        seen: dict[int, None] = {}
        for r in rows:
            seen[int(r[0])] = None
        return list(seen)

    def _search_books_fts(self, query: str, *, book_ids: Sequence[int] | None) -> list[int]:
        if book_ids is None:
            rows = self._conn.execute(
                "SELECT rowid FROM books_fts WHERE books_fts MATCH ? ORDER BY rank",
                (query,),
            ).fetchall()
        else:
            ids = list(book_ids)
            if not ids:
                return []
            placeholders = ",".join("?" * len(ids))
            rows = self._conn.execute(
                f"SELECT rowid FROM books_fts WHERE books_fts MATCH ? "
                f"AND rowid IN ({placeholders}) ORDER BY rank",
                (query, *ids),
            ).fetchall()
        return [int(r[0]) for r in rows]

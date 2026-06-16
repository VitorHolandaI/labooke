"""SQLite connection helpers with sqlite-vec and foreign keys enabled.

``open_db(path)`` loads ``sqlite-vec``, enables FK enforcement, applies
pending migrations, and seeds the default tags unless disabled by the
caller.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import sqlite_vec

from labooke_core.store.migrator import migrate
from labooke_core.store.seed_tags import ensure_seed_tags

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


class LockedConnection:
    """Thread-safe wrapper around sqlite3.Connection.

    FastAPI dispatches endpoint handlers to a thread pool; sharing one
    connection across threads without serialization causes
    ``InterfaceError: bad parameter or other API misuse`` under
    concurrent requests.  This wrapper serializes every execute /
    commit / rollback through a reentrant lock so the same thread can
    nest calls inside a ``with conn:`` transaction block.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._lock = threading.RLock()

    @property
    def raw(self) -> sqlite3.Connection:
        """The underlying connection.

        Only safe to use single-threaded (e.g. during startup migrations,
        before the connection is shared across request threads).
        """
        return self._conn

    def execute(self, sql: str, parameters: Sequence[Any] = (), /) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, parameters)

    def executemany(
        self, sql: str, parameters: Iterable[Sequence[Any]], /
    ) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, parameters)

    def commit(self) -> None:
        with self._lock:
            self._conn.commit()

    def rollback(self) -> None:
        with self._lock:
            self._conn.rollback()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> sqlite3.Connection:
        self._lock.acquire()
        return self._conn.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return self._conn.__exit__(exc_type, exc_val, exc_tb)
        finally:
            self._lock.release()

    def __getattr__(self, name: str):
        return getattr(self._conn, name)


def _enable_extensions(conn: sqlite3.Connection) -> None:
    """Load the sqlite-vec extension into ``conn``.

    The extension must be loaded before any ``vec0`` virtual-table
    statements run, including the ones in migration ``0001``.
    """
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Set the pragmas labooke relies on (FK enforcement, WAL)."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")


def connect(path: Path | str) -> LockedConnection:
    """Open a SQLite connection wired for labooke (extensions + pragmas).

    Does **not** run migrations. Use :func:`open_db` for the full setup
    in normal application code. ``connect`` is useful when callers want
    full control over the schema lifecycle (e.g. tests).

    Returns a :class:`LockedConnection` that serializes concurrent access
    through a reentrant lock, making it safe to share across FastAPI's
    threadpool workers.

    Example:
        >>> conn = connect(":memory:")
        >>> conn.execute("SELECT 1").fetchone()
        (1,)
    """
    raw = sqlite3.connect(path, check_same_thread=False)
    _enable_extensions(raw)
    _apply_pragmas(raw)
    return LockedConnection(raw)


def open_db(path: Path | str, *, seed_tags: bool = True) -> LockedConnection:
    """Open a labooke DB and bring it up to the latest schema.

    Parent directories of ``path`` are created if missing (unless
    ``path`` is ``:memory:``). Seed tags are inserted by default;
    tests can pass ``seed_tags=False`` for a blank tag table.

    Example:
        >>> conn = open_db(":memory:")
        >>> tables = {
        ...     row[0]
        ...     for row in conn.execute(
        ...         "SELECT name FROM sqlite_master WHERE type='table'"
        ...     )
        ... }
        >>> {"books", "tags", "chunks"} <= tables
        True
    """
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    # Migrations/seeding run single-threaded at startup, before the
    # connection is shared across request threads, so the raw connection
    # is safe here and keeps migrate()/ensure_seed_tags() typed on sqlite3.
    migrate(conn.raw, MIGRATIONS_DIR)
    if seed_tags:
        ensure_seed_tags(conn.raw)
    return conn

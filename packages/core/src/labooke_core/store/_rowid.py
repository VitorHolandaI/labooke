"""Helper for reading the rowid produced by an INSERT."""

from __future__ import annotations

import sqlite3


def last_insert_id(cursor: sqlite3.Cursor) -> int:
    """Return the rowid of the row just inserted via ``cursor``.

    ``sqlite3.Cursor.lastrowid`` is typed ``int | None``; it is only None
    when the last statement was not a successful single-row INSERT. Repos
    call this right after such an INSERT, so a None here is a real bug
    worth surfacing rather than silently coercing.

    Example:
        >>> conn = sqlite3.connect(":memory:")
        >>> _ = conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        >>> cur = conn.execute("INSERT INTO t (v) VALUES ('x')")
        >>> last_insert_id(cur)
        1
    """
    rowid = cursor.lastrowid
    if rowid is None:
        raise RuntimeError(
            f"expected an INSERT rowid but cursor.lastrowid is None "
            f"(rowcount={cursor.rowcount})"
        )
    return rowid

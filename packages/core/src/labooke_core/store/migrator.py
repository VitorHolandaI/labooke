"""Hand-rolled SQL migrator.

Applies any `NNNN_*.sql` files in a directory whose version number is
greater than the highest applied version recorded in the
``schema_version`` table.

See decisions/0009-hand-rolled-migrations.md for rationale.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def parse_version(path: Path) -> int:
    """Return the integer version prefix of a migration file.

    Args:
        path: A migration file whose name starts with digits and an
            underscore, e.g. ``0001_initial_schema.sql``.

    Raises:
        ValueError: If the filename does not begin with an integer
            prefix followed by ``_``.

    Example:
        >>> parse_version(Path("0007_add_highlights.sql"))
        7
    """
    prefix = path.name.split("_", 1)[0]
    if not prefix.isdigit():
        raise ValueError(
            f"migration filename {path.name!r} must start with digits and '_', e.g. '0001_init.sql'"
        )
    return int(prefix)


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    """Create the ``schema_version`` table if it doesn't already exist."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")


def current_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied migration version, or 0 if none."""
    _ensure_schema_version_table(conn)
    row = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()
    return int(row[0])


def pending_migrations(directory: Path, applied: int) -> list[Path]:
    """List migration files whose version is greater than ``applied``.

    Returned in ascending version order.
    """
    candidates = sorted(directory.glob("*.sql"), key=parse_version)
    return [p for p in candidates if parse_version(p) > applied]


def apply_migration(conn: sqlite3.Connection, path: Path) -> int:
    """Run a single migration in its own transaction and record it.

    Returns the version number that was applied.
    """
    _ensure_schema_version_table(conn)
    version = parse_version(path)
    sql = path.read_text()
    with conn:
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    return version


def migrate(conn: sqlite3.Connection, directory: Path) -> list[int]:
    """Apply every pending migration in ``directory`` to ``conn``.

    Idempotent: running again after all migrations are applied is a
    no-op and returns an empty list.

    Args:
        conn: Open SQLite connection. Caller owns lifecycle.
        directory: Directory holding ``NNNN_*.sql`` files.

    Returns:
        The list of versions newly applied (empty if up to date).

    Example:
        >>> conn = sqlite3.connect(":memory:")
        >>> migrate(conn, Path("packages/core/src/labooke_core/store/migrations"))
        [1]
    """
    if not directory.is_dir():
        raise FileNotFoundError(
            f"migrations directory {directory!s} does not exist or is not a directory"
        )
    applied = current_version(conn)
    pending = pending_migrations(directory, applied)
    return [apply_migration(conn, path) for path in pending]

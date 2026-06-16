"""Default tag seeding for first-run databases.

Seed tags are plain tags with stable names/slugs. They carry no special
marker after insert, matching ADR 0002.
"""

from __future__ import annotations

import sqlite3

SEED_TAGS: tuple[tuple[str, str, str], ...] = (
    ("Historical", "historical", "#888888"),
    ("Fiction", "fiction", "#888888"),
    ("Non-Fiction", "non-fiction", "#888888"),
    ("Science", "science", "#888888"),
    ("Technology", "technology", "#888888"),
    ("Programming", "programming", "#888888"),
    ("Security", "security", "#888888"),
    ("Philosophy", "philosophy", "#888888"),
    ("Biography", "biography", "#888888"),
    ("Reference", "reference", "#888888"),
    ("Tutorial", "tutorial", "#888888"),
    ("Action", "action", "#888888"),
    ("Fantasy", "fantasy", "#888888"),
    ("Business", "business", "#888888"),
    ("Math", "math", "#888888"),
)


def ensure_seed_tags(conn: sqlite3.Connection) -> None:
    """Insert the default tags when each seed slug is absent.

    Existing rows are left untouched so user edits to a seeded tag are
    preserved on later startups.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> conn = open_db(":memory:", seed_tags=False)
        >>> ensure_seed_tags(conn)
        >>> conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        15
    """
    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO tags (name, slug, color) VALUES (?, ?, ?)",
            SEED_TAGS,
        )

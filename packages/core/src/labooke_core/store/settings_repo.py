"""Persistence for the runtime settings KV table.

Values here override ``LABOOKE_*`` env defaults at runtime (set from
the Admin page, e.g. how many pages the LLM reads per summary). Only
string values are stored; callers cast.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection


class SettingsRepo:
    """Read and write the ``settings`` key-value table.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> repo = SettingsRepo(open_db(":memory:"))
        >>> repo.set("summary_pages", "20")
        >>> repo.get("summary_pages")
        '20'
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return the value for ``key`` or ``default`` when unset."""
        row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return str(row[0]) if row is not None else default

    def set(self, key: str, value: str) -> None:
        """Insert or update the value for ``key``."""
        self._conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()

    def delete(self, key: str) -> None:
        """Remove a runtime override so its environment default applies."""
        self._conn.execute("DELETE FROM settings WHERE key = ?", (key,))
        self._conn.commit()

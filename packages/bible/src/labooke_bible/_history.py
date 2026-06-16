"""Persistent query history stored as a newline-delimited text file."""

from __future__ import annotations

from pathlib import Path

_MAX_ENTRIES = 200


class HistoryStore:
    """Read and write a flat text file of past queries, one per line.

    Example:
        >>> import tempfile, pathlib
        >>> p = pathlib.Path(tempfile.mktemp())
        >>> h = HistoryStore(p)
        >>> h.push("linux kernel")
        >>> h.entries()
        ['linux kernel']
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def push(self, query: str) -> None:
        """Append *query* and trim to the most recent entries."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        entries = self.entries()
        entries.append(query.strip())
        trimmed = entries[-_MAX_ENTRIES:]
        self._path.write_text("\n".join(trimmed) + "\n", encoding="utf-8")

    def entries(self) -> list[str]:
        """Return all entries, oldest first."""
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        return [line for line in lines if line.strip()]

    def last(self) -> str | None:
        """Return the most recent query, or None if history is empty."""
        entries = self.entries()
        return entries[-1] if entries else None

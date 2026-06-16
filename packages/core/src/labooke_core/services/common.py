"""Shared service helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from labooke_core.extract import for_format
from labooke_core.extract.base import PathLike

TaskRunner = Callable[[Callable[[], None]], None]


def inline_task_runner(task: Callable[[], None]) -> None:
    """Execute a scheduled task immediately.

    Example:
        >>> calls = []
        >>> inline_task_runner(lambda: calls.append("ran"))
        >>> calls
        ['ran']
    """
    task()


def file_sha256(path: PathLike) -> str:
    """Return the sha256 hex digest for the bytes at ``path``.

    Example:
        >>> path = Path('digest-demo.txt')
        >>> _ = path.write_text('demo', encoding='utf-8')
        >>> len(file_sha256(path))
        64
        >>> path.unlink()
    """
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_from_path(path: PathLike) -> str:
    """Validate and return the normalized extractor format for ``path``.

    Example:
        >>> format_from_path('demo.TXT')
        'txt'
    """
    fmt = Path(path).suffix.lower().lstrip(".")
    for_format(fmt)
    return fmt

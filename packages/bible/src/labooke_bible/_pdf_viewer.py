"""Open PDFs in ``tdf``, an external terminal PDF viewer.

``tdf`` is optional: the built-in text pager keeps working without it,
so the binary is looked up only when ``bible read --tdf`` asks for it.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Protocol


class PdfViewerError(RuntimeError):
    """Raised when the external viewer is missing or exits with an error."""


class PdfViewer(Protocol):
    """Anything that can show a local PDF file to the user."""

    def open(self, pdf: Path) -> None:
        """Block until the user closes ``pdf``."""
        ...


class TdfViewer:
    """Run ``tdf <file>`` in the current terminal.

    Example:
        >>> TdfViewer().open(Path("book.pdf"))  # doctest: +SKIP
    """

    def __init__(
        self,
        *,
        binary: str = "tdf",
        find_binary: Callable[[str], str | None] = shutil.which,
        run_command: Callable[[list[str]], int] = subprocess.call,
    ) -> None:
        self._binary = binary
        self._find_binary = find_binary
        self._run_command = run_command

    def open(self, pdf: Path) -> None:
        """Show ``pdf`` in tdf; raise ``PdfViewerError`` on failure."""
        executable = self._find_binary(self._binary)
        if executable is None:
            raise PdfViewerError(f"{self._binary!r} not found in PATH; install it to use --tdf")
        exit_code = self._run_command([executable, str(pdf)])
        if exit_code != 0:
            raise PdfViewerError(f"{self._binary!r} exited with code {exit_code} for {pdf}")

"""Tests for the external tdf PDF viewer wrapper."""

from __future__ import annotations

from pathlib import Path

import pytest
from labooke_bible._pdf_viewer import PdfViewerError, TdfViewer


class RecordingCommandRunner:
    """Records every argv it is asked to run and returns a fixed exit code."""

    def __init__(self, exit_code: int = 0) -> None:
        self.calls: list[list[str]] = []
        self._exit_code = exit_code

    def __call__(self, argv: list[str]) -> int:
        self.calls.append(argv)
        return self._exit_code


class FixedBinaryFinder:
    """Pretends a binary lives at ``location`` (or is missing when None)."""

    def __init__(self, location: str | None) -> None:
        self._location = location

    def __call__(self, name: str) -> str | None:
        return self._location


def test_open_runs_tdf_with_the_pdf_path(tmp_path: Path) -> None:
    runner = RecordingCommandRunner()
    viewer = TdfViewer(find_binary=FixedBinaryFinder("/usr/bin/tdf"), run_command=runner)

    viewer.open(tmp_path / "book.pdf")

    assert runner.calls == [["/usr/bin/tdf", str(tmp_path / "book.pdf")]]


def test_open_fails_clearly_when_tdf_is_not_installed(tmp_path: Path) -> None:
    viewer = TdfViewer(find_binary=FixedBinaryFinder(None), run_command=RecordingCommandRunner())

    with pytest.raises(PdfViewerError, match="'tdf' not found in PATH"):
        viewer.open(tmp_path / "book.pdf")


def test_open_reports_non_zero_exit_code(tmp_path: Path) -> None:
    viewer = TdfViewer(
        find_binary=FixedBinaryFinder("/usr/bin/tdf"), run_command=RecordingCommandRunner(3)
    )

    with pytest.raises(PdfViewerError, match="exited with code 3"):
        viewer.open(tmp_path / "book.pdf")

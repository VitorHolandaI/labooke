"""Tests for `bible read --tdf` (open PDFs in the external tdf viewer)."""

from __future__ import annotations

from pathlib import Path

import pytest
from labooke_bible._pdf_viewer import PdfViewerError
from labooke_bible.cli import app
from typer.testing import CliRunner

from tests.conftest import FakeApiClient  # type: ignore[import-not-found]

runner = CliRunner()


class RecordingPdfViewer:
    """Records opened paths instead of launching tdf."""

    def __init__(self, error: PdfViewerError | None = None) -> None:
        self.opened: list[Path] = []
        self._error = error

    def open(self, pdf: Path) -> None:
        self.opened.append(pdf)
        if self._error is not None:
            raise self._error


@pytest.fixture
def viewer(monkeypatch: pytest.MonkeyPatch) -> RecordingPdfViewer:
    recording = RecordingPdfViewer()
    monkeypatch.setattr("labooke_bible.cli._viewer_singleton", recording)
    return recording


@pytest.fixture(autouse=True)
def cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    return tmp_path / "labooke" / "books"


def test_read_tdf_downloads_pdf_and_opens_it(
    fake_client: FakeApiClient, viewer: RecordingPdfViewer, cache_dir: Path
) -> None:
    book = fake_client.add_book("Manual", fmt="pdf")

    result = runner.invoke(app, ["read", str(book["id"]), "--tdf"])

    assert result.exit_code == 0, result.output
    assert viewer.opened == [cache_dir / f"sha-{book['id']}.pdf"]
    assert viewer.opened[0].read_bytes().startswith(b"%PDF")


def test_read_tdf_rejects_non_pdf_books(
    fake_client: FakeApiClient, viewer: RecordingPdfViewer
) -> None:
    book = fake_client.add_book("Novel", fmt="epub")

    result = runner.invoke(app, ["read", str(book["id"]), "--tdf"])

    assert result.exit_code == 1
    assert "only opens PDF" in result.output
    assert "'epub'" in result.output
    assert viewer.opened == []


def test_read_tdf_reports_viewer_error(
    fake_client: FakeApiClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    failing = RecordingPdfViewer(PdfViewerError("'tdf' not found in PATH"))
    monkeypatch.setattr("labooke_bible.cli._viewer_singleton", failing)
    book = fake_client.add_book("Manual", fmt="pdf")

    result = runner.invoke(app, ["read", str(book["id"]), "--tdf"])

    assert result.exit_code == 1
    assert "'tdf' not found in PATH" in result.output

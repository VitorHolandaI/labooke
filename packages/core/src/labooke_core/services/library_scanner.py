"""Bulk ingest from an import folder."""

from __future__ import annotations

from dataclasses import dataclass

from labooke_core.config import Settings
from labooke_core.domain.models import BookStatus
from labooke_core.services.ingest_service import IngestService

SUPPORTED_SCAN_SUFFIXES = {".pdf", ".epub", ".txt", ".md"}


@dataclass(slots=True)
class ScanResult:
    """Aggregate counts from one import-folder scan."""

    ingested: int = 0
    skipped: int = 0
    failed: int = 0


class LibraryScanner:
    """Walk the import folder and feed supported files through ingest.

    Example:
        >>> type(LibraryScanner(None, None)).__name__
        'LibraryScanner'
    """

    def __init__(self, settings: Settings, ingest: IngestService) -> None:
        self._settings = settings
        self._ingest = ingest

    def scan(self) -> ScanResult:
        """Ingest supported files from ``settings.import_dir``.

        Example:
            >>> scanner = LibraryScanner(None, None)
            >>> scanner.scan.__name__
            'scan'
        """
        import_dir = self._settings.import_dir
        import_dir.mkdir(parents=True, exist_ok=True)
        result = ScanResult()
        for path in sorted(import_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_SCAN_SUFFIXES:
                result.skipped += 1
                continue
            book = self._ingest.ingest_book(path, move_source=True)
            if book.status is BookStatus.FAILED:
                result.failed += 1
                continue
            result.ingested += 1
        return result

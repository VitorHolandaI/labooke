from pathlib import Path

from labooke_core.config import Settings
from labooke_core.domain.models import Book, BookStatus
from labooke_core.services.library_scanner import LibraryScanner


class FakeIngestService:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def ingest_book(self, path: Path, tags=(), *, move_source: bool = False) -> Book:
        self.calls.append(path)
        if move_source:
            path.unlink()
        return Book(
            id=len(self.calls),
            sha256=str(len(self.calls)),
            path=Path("/tmp/managed.txt"),
            title=path.stem,
            format=path.suffix.lstrip("."),
            page_count=1,
            status=BookStatus.READY,
            tags=[],
        )


def test_scan_ingests_supported_files_and_skips_unsupported(tmp_path):
    settings = Settings(data_dir=tmp_path / "data", import_dir=tmp_path / "inbox")
    settings.import_dir.mkdir(parents=True, exist_ok=True)  # pylint: disable=no-member
    supported = settings.import_dir / "book.txt"
    skipped = settings.import_dir / "image.png"
    supported.write_text("hello", encoding="utf-8")
    skipped.write_bytes(b"png")
    fake = FakeIngestService()
    result = LibraryScanner(settings, fake).scan()
    assert result.ingested == 1
    assert result.skipped == 1
    assert result.failed == 0
    assert fake.calls == [supported]
    assert not supported.exists()

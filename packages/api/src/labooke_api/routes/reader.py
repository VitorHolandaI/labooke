"""HTTP routes for reading book content."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from labooke_core.config import Settings
from labooke_core.extract import for_format
from labooke_core.services import ReaderService
from labooke_core.store.books_repo import BooksRepo

from labooke_api.deps import get_books_repo, get_reader_service, get_settings
from labooke_api.schemas import PageTextOut

router = APIRouter(prefix="/api/books/{book_id}", tags=["reader"])

BooksDep = Annotated[BooksRepo, Depends(get_books_repo)]
ReaderDep = Annotated[ReaderService, Depends(get_reader_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _cover_path(settings: Settings, sha256: str) -> Path:
    """Return the on-disk cache path for a book's cover thumbnail."""
    return settings.covers_dir / f"{sha256}.webp"


def _ensure_cover(settings: Settings, books: BooksRepo, book_id: int) -> Path:
    """Generate the cover on first request and return its path."""
    book = books.get(book_id)
    if book.path is None:
        raise HTTPException(status_code=404, detail="Book file not found")
    settings.covers_dir.mkdir(parents=True, exist_ok=True)
    destination = _cover_path(settings, book.sha256)
    if not destination.exists():
        for_format(book.format).write_cover_thumbnail(book.path, destination)
    return destination


@router.get("/pages/{page_no}", response_model=PageTextOut)
def get_page(book_id: int, page_no: int, reader: ReaderDep) -> PageTextOut:
    """Return the extracted text for one logical page."""
    return PageTextOut.from_domain(reader.get_page(book_id, page_no))


@router.get("/file")
def get_book_file(book_id: int, books: BooksDep) -> FileResponse:
    """Stream the raw book file for viewers (pdf.js, epub.js, plain text)."""
    book = books.get(book_id)
    if book.path is None:
        raise HTTPException(status_code=404, detail="Book file not found")
    return FileResponse(book.path, filename=book.path.name)


@router.get("/cover")
def get_book_cover(
    book_id: int, books: BooksDep, settings: SettingsDep
) -> FileResponse:
    """Return the cached WEBP cover thumbnail, generating it on first hit."""
    destination = _ensure_cover(settings, books, book_id)
    return FileResponse(destination, media_type="image/webp")

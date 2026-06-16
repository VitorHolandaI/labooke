"""HTTP routes for admin maintenance operations."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from labooke_core.services import LibraryScanner, ReembedService

from labooke_api.deps import get_library_scanner, get_reembed_service
from labooke_api.schemas import BookCreateResponse, ScanResultOut

router = APIRouter(tags=["admin"])

ReembedDep = Annotated[ReembedService, Depends(get_reembed_service)]
ScannerDep = Annotated[LibraryScanner, Depends(get_library_scanner)]


@router.post("/api/admin/scan", response_model=ScanResultOut)
def scan_import_dir(scanner: ScannerDep) -> ScanResultOut:
    """Walk ``LABOOKE_IMPORT_DIR`` and ingest every supported file in it."""
    return ScanResultOut.from_domain(scanner.scan())


@router.post(
    "/api/admin/reembed-all",
    response_model=list[BookCreateResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
def reembed_all(reembed: ReembedDep) -> list[BookCreateResponse]:
    """Schedule reembedding for every stored book."""
    books = reembed.reembed_all()
    return [BookCreateResponse(book_id=book.id, status=book.status.value) for book in books]


@router.post(
    "/api/books/{book_id}/reembed",
    response_model=BookCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def reembed_book(book_id: int, reembed: ReembedDep) -> BookCreateResponse:
    """Schedule a single-book reembed and return its current state."""
    book = reembed.reembed_book(book_id)
    return BookCreateResponse(book_id=book.id, status=book.status.value)

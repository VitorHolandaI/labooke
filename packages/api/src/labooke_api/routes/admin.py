"""HTTP routes for admin maintenance operations."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from labooke_core.services import LibraryScanner, ReembedService, SummarizeService

from labooke_api.deps import (
    get_library_scanner,
    get_reembed_service,
    get_summarize_service,
)
from labooke_api.schemas import (
    BookCreateResponse,
    InvalidateSummariesOut,
    ScanResultOut,
    SummarizeBatchOut,
    SummarizeBatchRequest,
    SummarizeRandomRequest,
)

router = APIRouter(tags=["admin"])

ReembedDep = Annotated[ReembedService, Depends(get_reembed_service)]
ScannerDep = Annotated[LibraryScanner, Depends(get_library_scanner)]
SummarizeDep = Annotated[SummarizeService, Depends(get_summarize_service)]


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


@router.post("/api/admin/summaries/invalidate", response_model=InvalidateSummariesOut)
def invalidate_summaries(summarize: SummarizeDep) -> InvalidateSummariesOut:
    """Clear every book's summary texts and summary vectors."""
    return InvalidateSummariesOut(invalidated=summarize.invalidate_all())


@router.post(
    "/api/admin/summaries/random",
    response_model=SummarizeBatchOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def summarize_random(
    body: SummarizeRandomRequest,
    summarize: SummarizeDep,
    background_tasks: BackgroundTasks,
) -> SummarizeBatchOut:
    """Schedule LLM summaries for ``count`` random books without one."""
    book_ids = summarize.pick_random_candidates(body.count)
    if book_ids:
        background_tasks.add_task(summarize.summarize_many, book_ids, body.pages)
    return SummarizeBatchOut(book_ids=book_ids)


@router.post(
    "/api/admin/summaries/batch",
    response_model=SummarizeBatchOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def summarize_batch(
    body: SummarizeBatchRequest,
    summarize: SummarizeDep,
    background_tasks: BackgroundTasks,
) -> SummarizeBatchOut:
    """Schedule LLM summaries for the explicitly listed books."""
    background_tasks.add_task(summarize.summarize_many, body.book_ids, body.pages)
    return SummarizeBatchOut(book_ids=body.book_ids)

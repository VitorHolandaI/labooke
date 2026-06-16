"""HTTP route for uploading new book files."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from labooke_core.services import IngestService

from labooke_api.deps import get_ingest_service
from labooke_api.schemas import BookCreateResponse

router = APIRouter(prefix="/api/books", tags=["upload"])

IngestDep = Annotated[IngestService, Depends(get_ingest_service)]


def _spool_upload(upload: UploadFile) -> Path:
    """Persist the multipart payload to a temp file IngestService can hash."""
    suffix = Path(upload.filename or "uploaded").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        shutil.copyfileobj(upload.file, handle)
        return Path(handle.name)


@router.post(
    "",
    response_model=BookCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_book(
    ingest: IngestDep,
    file: UploadFile = File(...),  # noqa: B008
    tag_ids: list[int] = Form(default_factory=list),  # noqa: B008
    title: str | None = Form(None),
) -> BookCreateResponse:
    """Accept a book file, deduplicate, and schedule background ingest."""
    spooled = _spool_upload(file)
    book = ingest.ingest_book(spooled, tag_ids, title=title or None, move_source=True)
    return BookCreateResponse(book_id=book.id, status=book.status.value)

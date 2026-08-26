"""HTTP routes for LLM features (book summarization and ask-the-library)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from labooke_core.services import AskService, SummarizeService

from labooke_api.deps import get_ask_service, get_summarize_service
from labooke_api.schemas import AskRequest, AskResponse, BookOut

router = APIRouter(tags=["llm"])

SummarizeDep = Annotated[SummarizeService, Depends(get_summarize_service)]
AskDep = Annotated[AskService, Depends(get_ask_service)]


@router.post("/api/books/{book_id}/summarize", response_model=BookOut)
def summarize_book(book_id: int, summarize: SummarizeDep) -> BookOut:
    """Generate and persist an LLM summary for a book (synchronous)."""
    return BookOut.from_domain(summarize.summarize(book_id))


@router.post("/api/ask", response_model=AskResponse)
def ask_library(body: AskRequest, ask: AskDep) -> AskResponse:
    """Recommend library books matching a natural-language request."""
    result = ask.ask(body.question)
    return AskResponse.from_domain(result)

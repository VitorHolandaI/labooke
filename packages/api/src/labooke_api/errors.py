"""HTTP exception mapping for labooke domain errors.

Routes raise the bare domain exceptions (``BookNotFound``,
``TagNotFound``, etc.) and FastAPI converts them into a uniform
``{"code": "...", "message": "..."}`` JSON body via the handlers
registered here.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from labooke_core.llm import LlmUnavailable
from labooke_core.store.bookmarks_repo import BookmarkNotFound
from labooke_core.store.books_repo import BookNotFound
from labooke_core.store.chunks_repo import ChunkNotFound
from labooke_core.store.tags_repo import TagNotFound


def _error_payload(code: str, exc: Exception) -> dict[str, str]:
    """Build the JSON body returned for a mapped domain error."""
    return {"code": code, "message": str(exc)}


def _not_found_handler(code: str):
    async def handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content=_error_payload(code, exc))

    return handler


def _value_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Map plain ``ValueError`` (range/argument violations) to 400."""
    payload = _error_payload("invalid_argument", exc)
    return JSONResponse(status_code=400, content=payload)


def _llm_unavailable_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Map ``LlmUnavailable`` (not configured / unreachable) to 503."""
    payload = _error_payload("llm_unavailable", exc)
    return JSONResponse(status_code=503, content=payload)


def register_error_handlers(app: FastAPI) -> None:
    """Attach the domain-to-HTTP handlers to ``app``.

    Example:
        >>> from fastapi import FastAPI
        >>> register_error_handlers(FastAPI())
    """
    app.add_exception_handler(BookNotFound, _not_found_handler("book_not_found"))
    app.add_exception_handler(TagNotFound, _not_found_handler("tag_not_found"))
    app.add_exception_handler(
        ChunkNotFound, _not_found_handler("chunk_not_found")
    )
    app.add_exception_handler(
        BookmarkNotFound, _not_found_handler("bookmark_not_found")
    )
    app.add_exception_handler(ValueError, _value_error_handler)
    app.add_exception_handler(LlmUnavailable, _llm_unavailable_handler)

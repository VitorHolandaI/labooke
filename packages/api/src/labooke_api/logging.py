"""Structured JSON logging and request-id middleware.

Wires ``structlog`` to emit one-line JSON records and binds a
per-request id (incoming ``X-Request-ID`` header preferred, otherwise
a fresh UUID4) into every log entry produced inside the request.
"""

from __future__ import annotations

import logging
import sys
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import Response

REQUEST_ID_HEADER = "x-request-id"


def configure_logging() -> None:
    """Initialize root logging to forward to structlog's JSON renderer."""
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _resolve_request_id(request: Request) -> str:
    """Return the incoming request id header or mint a fresh UUID4."""
    return request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex


async def _request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach a stable id to logs and echo it back on the response."""
    request_id = _resolve_request_id(request)
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


def register_logging(app: FastAPI) -> None:
    """Configure structlog and install the request-id middleware on ``app``.

    Example:
        >>> from fastapi import FastAPI
        >>> register_logging(FastAPI())
    """
    configure_logging()
    app.middleware("http")(_request_id_middleware)

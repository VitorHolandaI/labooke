"""HTTP route modules grouped by resource.

Each submodule exposes an ``APIRouter`` registered against the app
via :func:`register_routes`.
"""

from __future__ import annotations

from fastapi import FastAPI

from labooke_api.routes import admin as admin_routes
from labooke_api.routes import bookmarks as bookmarks_routes
from labooke_api.routes import books as books_routes
from labooke_api.routes import progress as progress_routes
from labooke_api.routes import reader as reader_routes
from labooke_api.routes import search as search_routes
from labooke_api.routes import tags as tags_routes
from labooke_api.routes import upload as upload_routes


def register_routes(app: FastAPI) -> None:
    """Attach every resource router to the FastAPI app.

    Example:
        >>> from fastapi import FastAPI
        >>> register_routes(FastAPI())
    """
    app.include_router(tags_routes.router)
    app.include_router(books_routes.router)
    app.include_router(bookmarks_routes.router)
    app.include_router(progress_routes.router)
    app.include_router(reader_routes.router)
    app.include_router(search_routes.router)
    app.include_router(upload_routes.router)
    app.include_router(admin_routes.router)

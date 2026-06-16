"""FastAPI application factory with lifespan-managed container."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from labooke_core import __version__ as core_version
from labooke_core.config import Settings

from labooke_api.container import AppContainer, build_container
from labooke_api.errors import register_error_handlers
from labooke_api.logging import register_logging
from labooke_api.routes import register_routes


def _register_cors(app: FastAPI, settings: Settings) -> None:
    """Attach a CORS middleware when ``cors_origins`` is non-empty."""
    if not settings.cors_origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _lifespan_factory(settings: Settings, container: AppContainer | None):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Open shared resources before serving and release them after."""
        owns_container = container is None
        active = container if container is not None else build_container(settings)
        app.state.container = active
        try:
            yield
        finally:
            if owns_container:
                active.close()

    return lifespan


def create_app(
    *,
    settings: Settings | None = None,
    container: AppContainer | None = None,
) -> FastAPI:
    """Build a configured FastAPI app.

    Pass ``container`` to inject a pre-built object graph (used in
    tests with in-memory DBs and fakes). Otherwise the lifespan opens
    a fresh container from ``settings`` (or :class:`Settings()`).

    Example:
        >>> app = create_app()
        >>> app.title
        'labooke'
    """
    resolved_settings = settings if settings is not None else Settings()
    app = FastAPI(
        title="labooke",
        version="0.0.1",
        lifespan=_lifespan_factory(resolved_settings, container),
    )
    register_logging(app)
    _register_cors(app, resolved_settings)
    register_error_handlers(app)
    register_routes(app)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        """Return a liveness payload with the core library version."""
        return {"status": "ok", "core": core_version}

    @app.get("/api/config")
    def config() -> dict[str, str | int]:
        """Return runtime configuration so the frontend can display it."""
        return {
            "embed_model": resolved_settings.embed_model,
            "chunk_pages": resolved_settings.chunk_pages,
            "data_dir": str(resolved_settings.data_dir),
        }

    return app

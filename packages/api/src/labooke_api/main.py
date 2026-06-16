"""FastAPI application entry point.

The HTTP surface is assembled in :mod:`labooke_api.app`; this module
exposes the live ``app`` for ASGI servers and the ``run`` console
script.
"""

from labooke_core.config import Settings

from labooke_api.app import create_app

settings = Settings()
app = create_app(settings=settings)


def run() -> None:
    """Run the development server with host/port from ``Settings``.

    Used as the ``labooke-api`` console script.
    """
    import uvicorn

    uvicorn.run(
        "labooke_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )

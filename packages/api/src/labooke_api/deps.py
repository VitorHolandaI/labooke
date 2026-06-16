"""FastAPI dependency providers backed by the lifespan container.

Long-lived singletons (settings, repos, search/library/reader services)
come straight from ``app.state.container``. Services that need to
schedule background work are built per-request against the active
``BackgroundTasks`` queue so jobs run after the response is sent.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import BackgroundTasks, Depends, Request
from labooke_core.config import Settings
from labooke_core.services import (
    IngestService,
    LibraryScanner,
    LibraryService,
    ReaderService,
    ReembedService,
    SearchService,
    SnippetService,
)
from labooke_core.services.common import TaskRunner
from labooke_core.store.bookmarks_repo import BookmarksRepo
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.progress_repo import ProgressRepo
from labooke_core.store.tags_repo import TagsRepo

from labooke_api.container import AppContainer


def get_container(request: Request) -> AppContainer:
    """Return the lifespan-managed container for the current app."""
    container: AppContainer = request.app.state.container
    return container


ContainerDep = Annotated[AppContainer, Depends(get_container)]


def get_settings(container: ContainerDep) -> Settings:
    """Return the active ``Settings`` instance."""
    return container.settings


def get_books_repo(container: ContainerDep) -> BooksRepo:
    """Return the shared ``BooksRepo``."""
    return container.books


def get_tags_repo(container: ContainerDep) -> TagsRepo:
    """Return the shared ``TagsRepo``."""
    return container.tags


def get_bookmarks_repo(container: ContainerDep) -> BookmarksRepo:
    """Return the shared ``BookmarksRepo``."""
    return container.bookmarks


def get_progress_repo(container: ContainerDep) -> ProgressRepo:
    """Return the shared ``ProgressRepo``."""
    return container.progress


def get_library_service(container: ContainerDep) -> LibraryService:
    """Return the shared ``LibraryService``."""
    return container.library


def get_reader_service(container: ContainerDep) -> ReaderService:
    """Return the shared ``ReaderService``."""
    return container.reader


def get_snippet_service(container: ContainerDep) -> SnippetService:
    """Return the shared ``SnippetService``."""
    return container.snippets


def get_search_service(container: ContainerDep) -> SearchService:
    """Return the shared ``SearchService``."""
    return container.search


def _background_runner(tasks: BackgroundTasks) -> TaskRunner:
    """Adapt FastAPI ``BackgroundTasks`` to the core ``TaskRunner`` shape."""

    def runner(task):
        tasks.add_task(task)

    return runner


def get_ingest_service(
    container: ContainerDep,
    background_tasks: BackgroundTasks,
) -> IngestService:
    """Build a per-request ``IngestService`` bound to ``BackgroundTasks``."""
    return IngestService(
        container.settings,
        container.books,
        container.tags,
        container.library,
        container.pipeline,
        schedule_task=_background_runner(background_tasks),
    )


def get_reembed_service(
    container: ContainerDep,
    background_tasks: BackgroundTasks,
) -> ReembedService:
    """Build a per-request ``ReembedService`` bound to ``BackgroundTasks``."""
    return ReembedService(
        container.books,
        container.pipeline,
        schedule_task=_background_runner(background_tasks),
    )


def get_library_scanner(
    container: ContainerDep,
    ingest: Annotated[IngestService, Depends(get_ingest_service)],
) -> LibraryScanner:
    """Build a per-request ``LibraryScanner`` using the same ingest pipeline."""
    return LibraryScanner(container.settings, ingest)

"""HTTP request and response schemas for the labooke API."""

from labooke_api.schemas.admin import (
    AdminConfigUpdate,
    InvalidateSummariesOut,
    ScanResultOut,
    SummarizeBatchOut,
    SummarizeBatchRequest,
    SummarizeRandomRequest,
)
from labooke_api.schemas.ask import AskRequest, AskResponse
from labooke_api.schemas.bookmarks import BookmarkCreate, BookmarkOut, BookmarkUpdateNote
from labooke_api.schemas.books import (
    BookCreateResponse,
    BookListOut,
    BookOut,
    BookTagAttach,
    BookUpdate,
)
from labooke_api.schemas.errors import ErrorOut
from labooke_api.schemas.pages import PageTextOut
from labooke_api.schemas.progress import ProgressOut, ProgressUpdate
from labooke_api.schemas.search import SearchGroupOut, SearchHitOut, SearchResponse
from labooke_api.schemas.tags import (
    TagCountOut,
    TagCreate,
    TagMergeRequest,
    TagOut,
    TagUpdate,
)

__all__ = [
    "AdminConfigUpdate",
    "AskRequest",
    "AskResponse",
    "BookCreateResponse",
    "BookListOut",
    "BookOut",
    "BookTagAttach",
    "BookUpdate",
    "BookmarkCreate",
    "BookmarkOut",
    "BookmarkUpdateNote",
    "ErrorOut",
    "InvalidateSummariesOut",
    "PageTextOut",
    "ProgressOut",
    "ProgressUpdate",
    "ScanResultOut",
    "SearchGroupOut",
    "SearchHitOut",
    "SearchResponse",
    "SummarizeBatchOut",
    "SummarizeBatchRequest",
    "SummarizeRandomRequest",
    "TagCountOut",
    "TagCreate",
    "TagMergeRequest",
    "TagOut",
    "TagUpdate",
]

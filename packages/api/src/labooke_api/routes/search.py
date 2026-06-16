"""HTTP routes for library search."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from labooke_core.domain.models import SearchHit
from labooke_core.services import SearchService

from labooke_api.deps import get_search_service
from labooke_api.schemas import SearchGroupOut, SearchHitOut, SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])

SearchDep = Annotated[SearchService, Depends(get_search_service)]


def _group_hits(hits: list[SearchHit]) -> list[SearchGroupOut]:
    """Bucket hits by ``book_id`` preserving their ranking order."""
    by_book: dict[int, list[SearchHitOut]] = defaultdict(list)
    order: list[int] = []
    for hit in hits:
        if hit.book_id not in by_book:
            order.append(hit.book_id)
        by_book[hit.book_id].append(SearchHitOut.from_domain(hit))
    return [SearchGroupOut(book_id=book_id, hits=by_book[book_id]) for book_id in order]


@router.get("", response_model=SearchResponse)
def search_library(
    search: SearchDep,
    q: str,
    tags: Annotated[Sequence[int], Query()] = (),
    tag_mode: Literal["all", "any"] = "all",
    exclude: Annotated[Sequence[int], Query()] = (),
    k: int = 10,
    mode: Literal["semantic", "lexical", "hybrid"] = "hybrid",
    group_by_book: bool = False,
) -> SearchResponse:
    """Run a search query and optionally group hits by book."""
    hits = search.search(
        q, tags=tags, tag_mode=tag_mode, exclude=exclude, k=k, mode=mode
    )
    if group_by_book:
        return SearchResponse(groups=_group_hits(hits), grouped=True)
    return SearchResponse(items=[SearchHitOut.from_domain(hit) for hit in hits])

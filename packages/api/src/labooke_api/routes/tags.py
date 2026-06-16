"""HTTP routes for tag management."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from labooke_core.store.tags_repo import TagsRepo

from labooke_api.deps import get_tags_repo
from labooke_api.schemas import (
    TagCountOut,
    TagCreate,
    TagMergeRequest,
    TagOut,
    TagUpdate,
)

router = APIRouter(prefix="/api/tags", tags=["tags"])

TagsDep = Annotated[TagsRepo, Depends(get_tags_repo)]


@router.get("", response_model=list[TagCountOut])
def list_tags(tags: TagsDep) -> list[TagCountOut]:
    """Return every tag with the count of attached books."""
    return [
        TagCountOut(tag=TagOut.from_domain(tag), count=count)
        for tag, count in tags.counts()
    ]


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(body: TagCreate, tags: TagsDep) -> TagOut:
    """Insert a new tag and return it."""
    try:
        tag = tags.insert(name=body.name, slug=body.slug, color=body.color)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Tag name or slug already exists") from exc
    return TagOut.from_domain(tag)


@router.patch("/{tag_id}", response_model=TagOut)
def update_tag(tag_id: int, body: TagUpdate, tags: TagsDep) -> TagOut:
    """Rename and/or recolor a tag; missing fields are left unchanged."""
    current = tags.get(tag_id)
    if body.name is not None:
        current = tags.rename(tag_id, body.name)
    if body.color is not None:
        current = tags.recolor(tag_id, body.color)
    return TagOut.from_domain(current)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, tags: TagsDep) -> None:
    """Delete a tag and its book attachments."""
    tags.get(tag_id)
    tags.delete(tag_id)


@router.post("/merge", status_code=status.HTTP_204_NO_CONTENT)
def merge_tags(body: TagMergeRequest, tags: TagsDep) -> None:
    """Move attachments from ``source_id`` onto ``target_id`` and drop the source."""
    tags.get(body.source_id)
    tags.get(body.target_id)
    tags.merge(body.source_id, body.target_id)

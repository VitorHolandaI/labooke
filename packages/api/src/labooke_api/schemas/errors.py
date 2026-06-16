"""Shared error response schema."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorOut(BaseModel):
    """Uniform error body returned by the API."""

    code: str
    message: str

"""Ollama embedding client and task-specific query formatting."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Sequence
from typing import Protocol

import numpy as np

from labooke_core.config import Settings
from labooke_core.store.vectors_repo import VEC_DIM


class EmbeddingUnavailable(RuntimeError):
    """Raised when the configured Ollama embedding endpoint cannot respond."""


class EmbeddingTransport(Protocol):
    """HTTP boundary used by :class:`OllamaEmbedder`."""

    def post_json(
        self,
        url: str,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> object:
        """POST JSON and return the decoded response body."""
        ...


class UrllibEmbeddingTransport:
    """Send embedding requests with the Python standard library."""

    def post_json(
        self,
        url: str,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> object:
        """POST one JSON payload and decode the response."""
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read()[:500]
            raise EmbeddingUnavailable(
                f"Ollama embedding request to {url!r} returned HTTP {exc.code}: {body!r}"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise EmbeddingUnavailable(
                f"Ollama embedding request to {url!r} failed: {exc}"
            ) from exc


class OllamaEmbedder:
    """Generate normalized vectors through Ollama's native embed API.

    Example:
        >>> OllamaEmbedder.__name__
        'OllamaEmbedder'
    """

    def __init__(
        self,
        base_url: str,
        model_name: str,
        *,
        timeout_seconds: float = 120.0,
        transport: EmbeddingTransport | None = None,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/api/embed"
        self.model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._transport = transport or UrllibEmbeddingTransport()

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """Encode texts as a normalized 1024-dimensional float32 matrix."""
        if not texts:
            return _empty_matrix()
        body = self._transport.post_json(
            self._url,
            {
                "model": self.model_name,
                "input": list(texts),
                "truncate": True,
            },
            self._timeout_seconds,
        )
        if not isinstance(body, dict):
            raise EmbeddingUnavailable(
                f"Ollama returned body type={type(body).__name__}; expected JSON object"
            )
        return _normalized_matrix(body.get("embeddings"), expected_rows=len(texts))


def _empty_matrix() -> np.ndarray:
    return np.empty((0, VEC_DIM), dtype=np.float32)


def _normalized_matrix(raw_embeddings: object, *, expected_rows: int) -> np.ndarray:
    matrix = np.asarray(raw_embeddings, dtype=np.float32)
    expected_shape = (expected_rows, VEC_DIM)
    if matrix.shape != expected_shape:
        raise EmbeddingUnavailable(
            f"Ollama returned embedding shape={matrix.shape!r}; expected {expected_shape!r}"
        )
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise EmbeddingUnavailable(
            "Ollama returned a zero-length embedding; expected non-zero vectors"
        )
    return matrix / norms


def _settings_embedder(settings: Settings | None = None) -> OllamaEmbedder:
    resolved = settings or Settings()
    if not resolved.embed_base_url or not resolved.embed_model:
        raise EmbeddingUnavailable(
            "embedding not configured; expected LABOOKE_EMBED_BASE_URL and LABOOKE_EMBED_MODEL"
        )
    return OllamaEmbedder(
        resolved.embed_base_url,
        resolved.embed_model,
        timeout_seconds=resolved.embed_timeout_seconds,
    )


def encode(texts: Sequence[str]) -> np.ndarray:
    """Encode document texts with the configured Ollama model."""
    if not texts:
        return _empty_matrix()
    return _settings_embedder().encode(texts)


def encode_query(texts: Sequence[str]) -> np.ndarray:
    """Encode passage-search queries with BGE-M3."""
    return encode(texts)


def encode_catalog_queries(texts: Sequence[str]) -> np.ndarray:
    """Encode catalog queries with BGE-M3."""
    return encode(texts)


def encode_passages(texts: Sequence[str]) -> np.ndarray:
    """Encode passage or catalog documents without query instructions."""
    return encode(texts)

"""Lazy sentence-transformers wrapper for labooke embeddings."""

from __future__ import annotations

import gc
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from threading import Lock, Timer
from typing import Any

import numpy as np

from labooke_core.config import Settings
from labooke_core.store.vectors_repo import VEC_DIM

_EMBEDDERS: dict[str, SentenceTransformerEmbedder] = {}
_EMBED_WORKER: ProcessPoolExecutor | None = None
_EMBED_WORKER_DEADLINE = 0.0
_EMBED_WORKER_TIMER: Timer | None = None
_EMBED_WORKER_LOCK = Lock()


def _resolved_model_name(model_name: str | None) -> str:
    if model_name is not None:
        return model_name
    return Settings().embed_model


def _build_model(model_name: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, device="cpu")


def _empty_matrix() -> np.ndarray:
    return np.empty((0, VEC_DIM), dtype=np.float32)


def _normalized_matrix(raw_embeddings: Any) -> np.ndarray:
    matrix = np.asarray(raw_embeddings, dtype=np.float32)
    return np.atleast_2d(matrix)


def _encode_in_child_process(model_name: str, texts: list[str]) -> np.ndarray:
    return get_default_embedder(model_name).encode(texts)


def _get_embed_worker() -> ProcessPoolExecutor:
    global _EMBED_WORKER, _EMBED_WORKER_DEADLINE, _EMBED_WORKER_TIMER
    with _EMBED_WORKER_LOCK:
        _EMBED_WORKER_DEADLINE = 0.0
        if _EMBED_WORKER_TIMER is not None:
            _EMBED_WORKER_TIMER.cancel()
            _EMBED_WORKER_TIMER = None
        if _EMBED_WORKER is None:
            _EMBED_WORKER = ProcessPoolExecutor(max_workers=1)
        return _EMBED_WORKER


def _shutdown_embed_worker() -> None:
    global _EMBED_WORKER, _EMBED_WORKER_DEADLINE, _EMBED_WORKER_TIMER
    with _EMBED_WORKER_LOCK:
        worker, _EMBED_WORKER = _EMBED_WORKER, None
        _EMBED_WORKER_DEADLINE = 0.0
        timer, _EMBED_WORKER_TIMER = _EMBED_WORKER_TIMER, None
    if timer is not None:
        timer.cancel()
    if worker is not None:
        worker.shutdown(wait=False, cancel_futures=True)


def _shutdown_embed_worker_if_idle(deadline: float) -> None:
    global _EMBED_WORKER, _EMBED_WORKER_DEADLINE, _EMBED_WORKER_TIMER
    with _EMBED_WORKER_LOCK:
        if deadline != _EMBED_WORKER_DEADLINE or time.monotonic() < deadline:
            return
        worker, _EMBED_WORKER = _EMBED_WORKER, None
        _EMBED_WORKER_DEADLINE = 0.0
        _EMBED_WORKER_TIMER = None
    if worker is not None:
        worker.shutdown(wait=False, cancel_futures=True)


def _schedule_embed_worker_shutdown(idle_seconds: float) -> None:
    global _EMBED_WORKER_DEADLINE, _EMBED_WORKER_TIMER
    with _EMBED_WORKER_LOCK:
        if _EMBED_WORKER_TIMER is not None:
            _EMBED_WORKER_TIMER.cancel()
        _EMBED_WORKER_DEADLINE = time.monotonic() + idle_seconds
        _EMBED_WORKER_TIMER = Timer(
            idle_seconds,
            _shutdown_embed_worker_if_idle,
            args=(_EMBED_WORKER_DEADLINE,),
        )
        _EMBED_WORKER_TIMER.daemon = True
        _EMBED_WORKER_TIMER.start()


def _encode_without_model_cache(model_name: str, texts: Sequence[str]) -> np.ndarray:
    if not texts:
        return _empty_matrix()
    settings = Settings()
    worker = _get_embed_worker()
    matrix = worker.submit(_encode_in_child_process, model_name, list(texts)).result()
    _schedule_embed_worker_shutdown(settings.embed_worker_idle_seconds)
    return _normalized_matrix(matrix)


class SentenceTransformerEmbedder:
    """Thin project-owned wrapper around `sentence-transformers`.

    Example:
        >>> embedder = SentenceTransformerEmbedder("BAAI/bge-small-en-v1.5")
        >>> embedder.model_name
        'BAAI/bge-small-en-v1.5'
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def _loaded_model(self) -> Any:
        if self._model is None:
            self._model = _build_model(self.model_name)
        return self._model

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """Encode ``texts`` into a float32 matrix of normalized embeddings.

        Example:
            >>> SentenceTransformerEmbedder('BAAI/bge-small-en-v1.5').encode([]).shape
            (0, 384)
        """
        if not texts:
            return _empty_matrix()
        raw = self._loaded_model().encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return _normalized_matrix(raw)

    def unload(self) -> None:
        """Drop the loaded model reference so it can be garbage-collected."""
        self._model = None
        gc.collect()


def get_default_embedder(model_name: str | None = None) -> SentenceTransformerEmbedder:
    """Return the cached embedder for ``model_name`` or the configured default.

    Example:
        >>> get_default_embedder('demo') is get_default_embedder('demo')
        True
    """
    resolved = _resolved_model_name(model_name)
    if resolved not in _EMBEDDERS:
        _EMBEDDERS[resolved] = SentenceTransformerEmbedder(resolved)
    return _EMBEDDERS[resolved]


def encode(texts: Sequence[str], *, model_name: str | None = None) -> np.ndarray:
    """Encode ``texts`` through the cached default embedder."""
    resolved = _resolved_model_name(model_name)
    if not Settings().embed_cache_model:
        return _encode_without_model_cache(resolved, texts)
    return get_default_embedder(resolved).encode(texts)


def unload_default_embedder(model_name: str | None = None) -> None:
    """Unload and forget the cached embedder for ``model_name`` if present."""
    resolved = _resolved_model_name(model_name)
    embedder = _EMBEDDERS.pop(resolved, None)
    if embedder is not None:
        embedder.unload()


def _is_e5_model(model_name: str) -> bool:
    return "e5" in model_name.lower()


def encode_query(texts: Sequence[str], *, model_name: str | None = None) -> np.ndarray:
    """Encode search queries, adding 'query: ' prefix for E5 models."""
    resolved = _resolved_model_name(model_name)
    prefixed = [f"query: {t}" for t in texts] if _is_e5_model(resolved) else list(texts)
    return encode(prefixed, model_name=resolved)


def encode_passages(texts: Sequence[str], *, model_name: str | None = None) -> np.ndarray:
    """Encode document passages, adding 'passage: ' prefix for E5 models."""
    resolved = _resolved_model_name(model_name)
    prefixed = [f"passage: {t}" for t in texts] if _is_e5_model(resolved) else list(texts)
    return encode(prefixed, model_name=resolved)

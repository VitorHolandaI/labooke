"""Resolve environment defaults and the optional Admin Ollama override."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from labooke_core.config import Settings
from labooke_core.embed.encoder import (
    EmbeddingUnavailable,
    OllamaEmbedder,
)
from labooke_core.llm import ChatClient, OpenAICompatibleClient, build_chat_client
from labooke_core.store.settings_repo import SettingsRepo

OLLAMA_BASE_URL_KEY = "ollama_base_url"


class OllamaRuntime:
    """Build clients from the current Admin override or environment fallback.

    Example:
        >>> OllamaRuntime.__name__
        'OllamaRuntime'
    """

    def __init__(self, settings: Settings, settings_repo: SettingsRepo) -> None:
        self._settings = settings
        self._settings_repo = settings_repo

    def override_base_url(self) -> str | None:
        """Return the Admin override, or ``None`` when environment defaults apply."""
        return self._settings_repo.get(OLLAMA_BASE_URL_KEY)

    def active_base_url(self) -> str:
        """Return the effective native Ollama base URL for display in Admin."""
        override = self.override_base_url()
        if override:
            return override
        if self._settings.embed_base_url:
            return self._settings.embed_base_url.rstrip("/")
        return self._settings.llm_base_url.removesuffix("/v1").rstrip("/")

    def chat_client(self) -> ChatClient | None:
        """Return a chat client using the current runtime endpoint."""
        override = self.override_base_url()
        if not override:
            return build_chat_client(self._settings)
        if not self._settings.llm_model:
            return None
        return OpenAICompatibleClient(
            f"{override.rstrip('/')}/v1",
            self._settings.llm_model,
            self._settings.llm_api_key,
        )

    def encode_passages(self, texts: Sequence[str]) -> np.ndarray:
        """Encode chunk or catalog documents with the active endpoint."""
        return self._embedder().encode(texts)

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        """Encode content-search queries with the active endpoint."""
        return self._embedder().encode(texts)

    def encode_catalog_queries(self, texts: Sequence[str]) -> np.ndarray:
        """Encode book requests with the active endpoint."""
        return self._embedder().encode(texts)

    def _embedder(self) -> OllamaEmbedder:
        base_url = self.override_base_url() or self._settings.embed_base_url
        if not base_url or not self._settings.embed_model:
            raise EmbeddingUnavailable(
                "embedding not configured; expected an Ollama endpoint and embed model"
            )
        return OllamaEmbedder(
            base_url,
            self._settings.embed_model,
            timeout_seconds=self._settings.embed_timeout_seconds,
        )

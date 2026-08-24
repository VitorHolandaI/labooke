"""Thin OpenAI-compatible chat client backed by the standard library.

Ollama exposes an OpenAI-compatible ``/v1/chat/completions`` endpoint
with no authentication locally: the ``api_key`` field is required by
OpenAI clients but ignored by Ollama. Keeping the transport on stdlib
``urllib`` means the API can talk to Ollama, OpenAI, LM Studio, etc.
just by changing ``LABOOKE_LLM_BASE_URL`` / ``LABOOKE_LLM_MODEL``.

See decisions/0007-no-hardcoded-endpoints.md and the KISS rule in
AGENTS.md — a framework like LangChain would add a large dependency for
two chat-completion calls.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from labooke_core.config import Settings

_TIMEOUT_SECONDS = 300.0


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single chat turn with an OpenAI-style role."""

    role: str  # "system" | "user" | "assistant"
    content: str


class ChatClient(Protocol):
    """Minimal chat interface owned by this project (see AGENTS.md)."""

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Send ``messages`` and return the assistant's reply text."""
        ...


class LlmUnavailable(RuntimeError):
    """Raised when the LLM is not configured or the request fails."""


def _parse_choices(body: bytes) -> str:
    """Extract the assistant text from an OpenAI-compatible response."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise LlmUnavailable(f"non-JSON chat response: {body[:200]!r}") from exc
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmUnavailable(
            f"malformed chat response: {body[:200]!r} (expected choices[0].message.content)"
        ) from exc
    return str(content)


class OpenAICompatibleClient:
    """Call ``/v1/chat/completions`` via ``urllib``.

    Example:
        >>> client = OpenAICompatibleClient("http://localhost:11434/v1", "llama3.2")
        >>> client.model_name
        'llama3.2'
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key

    @property
    def model_name(self) -> str:
        """Return the configured model identifier."""
        return self._model

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Send a chat request and return the assistant reply.

        Raises:
            LlmUnavailable: on transport, HTTP, or parsing errors.
        """
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                return _parse_choices(response.read())
        except urllib.error.HTTPError as exc:
            raise LlmUnavailable(
                f"chat request failed with HTTP {exc.code}: {exc.read()[:200]!r}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise LlmUnavailable(f"chat request to {self._base_url!r} failed: {exc}") from exc


def build_chat_client(settings: Settings) -> OpenAICompatibleClient | None:
    """Return a configured chat client, or ``None`` when the LLM is off.

    Example:
        >>> from labooke_core.config import Settings
        >>> build_chat_client(Settings(llm_base_url="", llm_model="")) is None
        True
    """
    if not settings.llm_enabled:
        return None
    return OpenAICompatibleClient(
        settings.llm_base_url,
        settings.llm_model,
        settings.llm_api_key,
    )

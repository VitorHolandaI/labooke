import json

from labooke_core.config import Settings
from labooke_core.llm import (
    ChatMessage,
    LlmUnavailable,
    OpenAICompatibleClient,
    build_chat_client,
)
from labooke_core.llm.client import _parse_choices


def _response_bytes(content: str) -> bytes:
    return json.dumps({"choices": [{"message": {"content": content}}]}).encode()


def test_parse_choices_extracts_content():
    assert _parse_choices(_response_bytes("hello")) == "hello"


def test_parse_choices_rejects_malformed_shape():
    try:
        _parse_choices(b'{"no": "choices"}')
    except LlmUnavailable as exc:
        assert "malformed chat response" in str(exc)
    else:
        raise AssertionError("expected LlmUnavailable")


def test_parse_choices_rejects_non_json():
    try:
        _parse_choices(b"not json at all")
    except LlmUnavailable as exc:
        assert "non-JSON" in str(exc)
    else:
        raise AssertionError("expected LlmUnavailable")


def test_build_chat_client_returns_none_when_disabled():
    settings = Settings(llm_base_url="", llm_model="")
    assert build_chat_client(settings) is None


def test_build_chat_client_returns_client_when_enabled():
    settings = Settings(llm_base_url="http://x:11434/v1", llm_model="m", llm_api_key="")
    client = build_chat_client(settings)
    assert client is not None
    assert client.model_name == "m"


def test_client_model_name():
    client = OpenAICompatibleClient("http://x:11434/v1", "llama3.2")
    assert client.model_name == "llama3.2"


def test_chat_message_fields():
    message = ChatMessage(role="system", content="hi")
    assert (message.role, message.content) == ("system", "hi")

"""Helpers for structured LLM responses."""

from __future__ import annotations


def extract_json_object(text: str) -> str:
    """Return the first JSON object from a reply, ignoring markdown fences.

    Example:
        >>> extract_json_object('```json\n{"ok": true}\n```')
        '{"ok": true}'
    """
    cleaned = text.strip()
    for prefix in ("```json", "```"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[: -len("```")].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    return cleaned[start : end + 1] if start != -1 and end > start else cleaned

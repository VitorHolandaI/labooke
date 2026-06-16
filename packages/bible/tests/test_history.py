"""Tests for HistoryStore."""

from pathlib import Path

import pytest
from labooke_bible._history import HistoryStore


@pytest.fixture
def store(tmp_path: Path) -> HistoryStore:
    return HistoryStore(tmp_path / "history.txt")


def test_empty_history_returns_no_entries(store):
    assert store.entries() == []


def test_empty_history_last_is_none(store):
    assert store.last() is None


def test_push_adds_entry(store):
    store.push("linux kernel")
    assert store.entries() == ["linux kernel"]


def test_push_multiple_preserves_order(store):
    store.push("query one")
    store.push("query two")
    assert store.entries() == ["query one", "query two"]


def test_last_returns_most_recent(store):
    store.push("first")
    store.push("second")
    assert store.last() == "second"


def test_push_trims_whitespace(store):
    store.push("  trimmed  ")
    assert store.entries() == ["trimmed"]

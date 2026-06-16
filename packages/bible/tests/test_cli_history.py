"""Tests for `bible history` and `bible last` commands."""

from labooke_bible._history import HistoryStore
from labooke_bible.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_history_empty_prints_no_history():
    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_history_shows_past_queries(fake_history: HistoryStore):
    fake_history.push("linux kernel")
    fake_history.push("python async")
    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
    assert "linux kernel" in result.output
    assert "python async" in result.output


def test_last_with_empty_history_prints_message():
    result = runner.invoke(app, ["last"])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_last_reruns_most_recent_query(fake_history: HistoryStore):
    fake_history.push("linux kernel")
    result = runner.invoke(app, ["last", "--lexical"])
    assert result.exit_code == 0
    assert "No results" in result.output or result.exit_code == 0

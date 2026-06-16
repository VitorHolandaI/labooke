"""Tests for `bible search <query>` command."""

from labooke_bible.cli import app
from typer.testing import CliRunner

from tests.conftest import FakeApiClient  # type: ignore[import-not-found]

runner = CliRunner()


def test_search_empty_db_prints_no_results():
    result = runner.invoke(app, ["search", "linux", "--lexical"])
    assert result.exit_code == 0
    assert "No results" in result.output


def test_search_lexical_finds_matching_book(fake_client: FakeApiClient):
    fake_client.add_book("Linux Kernel Dev", fmt="pdf")
    fake_client.add_book("Python Cookbook", fmt="epub")

    result = runner.invoke(app, ["search", "linux", "--lexical"])
    assert result.exit_code == 0
    assert "Linux Kernel Dev" in result.output
    assert "Python Cookbook" not in result.output


def test_search_shows_numbered_results(fake_client: FakeApiClient):
    fake_client.add_book("Linux Admin", fmt="pdf")

    result = runner.invoke(app, ["search", "linux", "--lexical"])
    assert result.exit_code == 0
    assert "1." in result.output


def test_search_lexical_with_tag_filter(fake_client: FakeApiClient):
    tag = fake_client.add_tag("Linux", "linux")
    book_a = fake_client.add_book("Linux Admin", fmt="pdf")
    fake_client.add_book("Linux Mint Guide", fmt="txt")
    fake_client.attach_tag(book_a["id"], tag["id"])

    result = runner.invoke(app, ["search", "linux", "--lexical", "--tag", "linux"])
    assert result.exit_code == 0
    assert "Linux Admin" in result.output
    assert "Linux Mint Guide" not in result.output

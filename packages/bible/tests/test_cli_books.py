"""Tests for `bible books` command."""

from labooke_bible.cli import app
from typer.testing import CliRunner

from tests.conftest import FakeApiClient  # type: ignore[import-not-found]

runner = CliRunner()


def test_books_empty_db_prints_no_books():
    result = runner.invoke(app, ["books"])
    assert result.exit_code == 0
    assert "No books" in result.output


def test_books_shows_title_format_and_tags(fake_client: FakeApiClient):
    tag = fake_client.add_tag("Linux", "linux")
    book = fake_client.add_book("The Linux Book", fmt="pdf")
    fake_client.attach_tag(book["id"], tag["id"])
    fake_client.add_book("Plain Text", fmt="txt")

    result = runner.invoke(app, ["books"])
    assert result.exit_code == 0
    assert "The Linux Book" in result.output
    assert "[pdf]" in result.output
    assert "Linux" in result.output
    assert "Plain Text" in result.output
    assert "[txt]" in result.output


def test_books_filter_by_tag_slug(fake_client: FakeApiClient):
    tag = fake_client.add_tag("Linux", "linux")
    book_a = fake_client.add_book("Linux Admin", fmt="pdf")
    fake_client.add_book("Fiction Novel", fmt="epub")
    fake_client.attach_tag(book_a["id"], tag["id"])

    result = runner.invoke(app, ["books", "--tag", "linux"])
    assert result.exit_code == 0
    assert "Linux Admin" in result.output
    assert "Fiction Novel" not in result.output

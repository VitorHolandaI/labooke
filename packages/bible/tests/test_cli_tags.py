"""Tests for `bible tags` command."""

from labooke_bible.cli import app
from typer.testing import CliRunner

from tests.conftest import FakeApiClient  # type: ignore[import-not-found]

runner = CliRunner()


def test_tags_empty_db_prints_no_tags():
    result = runner.invoke(app, ["tags"])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_tags_lists_name_and_count(fake_client: FakeApiClient):
    tag_linux = fake_client.add_tag("Linux", "linux")
    fake_client.add_tag("Fiction", "fiction")
    book = fake_client.add_book("A Book", fmt="txt")
    fake_client.attach_tag(book["id"], tag_linux["id"])

    result = runner.invoke(app, ["tags"])
    assert result.exit_code == 0
    assert "Linux (1)" in result.output
    assert "Fiction (0)" in result.output

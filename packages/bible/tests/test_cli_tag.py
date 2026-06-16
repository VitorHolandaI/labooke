"""Tests for `bible tag <book_id> +slug -slug` command."""

from labooke_bible.cli import app
from typer.testing import CliRunner

from tests.conftest import FakeApiClient  # type: ignore[import-not-found]

runner = CliRunner()


def test_tag_attach_adds_tag_to_book(fake_client: FakeApiClient):
    fake_client.add_tag("Linux", "linux")
    book = fake_client.add_book("Kernel Hacking")

    result = runner.invoke(app, ["tag", str(book["id"]), "+linux"])
    assert result.exit_code == 0
    loaded = fake_client.get_book(book["id"])
    assert any(t["slug"] == "linux" for t in loaded["tags"])


def test_tag_detach_removes_tag_from_book(fake_client: FakeApiClient):
    tag = fake_client.add_tag("Linux", "linux")
    book = fake_client.add_book("Kernel Hacking")
    fake_client.attach_tag(book["id"], tag["id"])

    result = runner.invoke(app, ["tag", str(book["id"]), "-linux"])
    assert result.exit_code == 0
    loaded = fake_client.get_book(book["id"])
    assert not any(t["slug"] == "linux" for t in loaded["tags"])


def test_tag_mixed_attach_and_detach(fake_client: FakeApiClient):
    fake_client.add_tag("Linux", "linux")
    tag_fiction = fake_client.add_tag("Fiction", "fiction")
    book = fake_client.add_book("A Book")
    fake_client.attach_tag(book["id"], tag_fiction["id"])

    result = runner.invoke(app, ["tag", str(book["id"]), "+linux", "-fiction"])
    assert result.exit_code == 0
    loaded = fake_client.get_book(book["id"])
    slugs = {t["slug"] for t in loaded["tags"]}
    assert "linux" in slugs
    assert "fiction" not in slugs


def test_tag_unknown_book_id_prints_error():
    result = runner.invoke(app, ["tag", "9999", "+linux"])
    assert result.exit_code != 0


def test_tag_unknown_slug_is_ignored(fake_client: FakeApiClient):
    book = fake_client.add_book("A Book")
    result = runner.invoke(app, ["tag", str(book["id"]), "+nonexistent"])
    assert result.exit_code == 0

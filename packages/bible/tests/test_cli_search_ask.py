"""Tests for the LLM ask path of `bible search` (default, non-lexical)."""

from labooke_bible.cli import app
from typer.testing import CliRunner

from tests.conftest import FakeApiClient  # type: ignore[import-not-found]

runner = CliRunner()


def test_search_default_uses_ask_and_prints_answer(fake_client: FakeApiClient):
    fake_client.add_book("Astrofísica para Iniciantes", fmt="pdf")

    result = runner.invoke(app, ["search", "quero um livro sobre ciência"])

    assert result.exit_code == 0
    assert "Recomendo para: quero um livro sobre ciência" in result.output
    assert "Astrofísica para Iniciantes" in result.output
    assert "1." in result.output


def test_search_ask_prints_author_when_present(fake_client: FakeApiClient):
    fake_client.add_book("Linux Kernel", fmt="pdf")

    result = runner.invoke(app, ["search", "kernel"])

    assert result.exit_code == 0
    assert "[1] Linux Kernel" in result.output


def test_search_ask_with_tag_filter(fake_client: FakeApiClient):
    tag = fake_client.add_tag("Linux", "linux")
    book_a = fake_client.add_book("Linux Kernel", fmt="pdf")
    fake_client.add_book("Cooking", fmt="txt")
    fake_client.attach_tag(book_a["id"], tag["id"])

    result = runner.invoke(app, ["search", "kernel", "--tag", "linux"])

    assert result.exit_code == 0
    assert "Linux Kernel" in result.output
    assert "Cooking" not in result.output


def test_search_ask_empty_library_prints_no_results(fake_client: FakeApiClient):
    result = runner.invoke(app, ["search", "qualquer coisa"])
    assert result.exit_code == 0
    assert "No results" in result.output
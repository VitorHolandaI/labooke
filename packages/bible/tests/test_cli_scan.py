"""Tests for `bible scan` command."""

from labooke_bible.cli import app
from typer.testing import CliRunner

from tests.conftest import FakeApiClient  # type: ignore[import-not-found]

runner = CliRunner()


def test_scan_empty_import_dir():
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0
    assert "0 ingested" in result.output


def test_scan_ingests_supported_file(fake_client: FakeApiClient):
    fake_client.set_scan_result(ingested=1, skipped=0, failed=0)
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0
    assert "1 ingested" in result.output

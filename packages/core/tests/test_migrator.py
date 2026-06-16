import sqlite3
from pathlib import Path

import pytest
from labooke_core.store.migrator import (
    apply_migration,
    current_version,
    migrate,
    parse_version,
    pending_migrations,
)


@pytest.fixture
def empty_dir(tmp_path) -> Path:
    return tmp_path


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def write(path: Path, sql: str) -> Path:
    path.write_text(sql)
    return path


def test_parse_version_extracts_integer_prefix():
    assert parse_version(Path("0007_add_highlights.sql")) == 7


def test_parse_version_rejects_non_numeric_prefix():
    with pytest.raises(ValueError, match="must start with digits"):
        parse_version(Path("init.sql"))


def test_current_version_creates_table_if_missing(conn):
    assert current_version(conn) == 0
    # Table was created by current_version itself
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchall()
    assert rows == [("schema_version",)]


def test_pending_migrations_returns_only_newer(empty_dir):
    write(empty_dir / "0001_a.sql", "CREATE TABLE a (id INTEGER);")
    write(empty_dir / "0002_b.sql", "CREATE TABLE b (id INTEGER);")
    write(empty_dir / "0003_c.sql", "CREATE TABLE c (id INTEGER);")
    pending = pending_migrations(empty_dir, applied=1)
    assert [p.name for p in pending] == ["0002_b.sql", "0003_c.sql"]


def test_apply_migration_runs_sql_and_records_version(conn, empty_dir):
    path = write(empty_dir / "0001_make_t.sql", "CREATE TABLE t (id INTEGER);")
    assert apply_migration(conn, path) == 1
    assert current_version(conn) == 1
    conn.execute("INSERT INTO t (id) VALUES (1)")


def test_migrate_applies_all_in_order(conn, empty_dir):
    write(empty_dir / "0001_a.sql", "CREATE TABLE a (id INTEGER);")
    write(empty_dir / "0002_b.sql", "CREATE TABLE b (id INTEGER);")
    applied = migrate(conn, empty_dir)
    assert applied == [1, 2]
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"a", "b", "schema_version"} <= tables


def test_migrate_is_idempotent(conn, empty_dir):
    write(empty_dir / "0001_a.sql", "CREATE TABLE a (id INTEGER);")
    assert migrate(conn, empty_dir) == [1]
    assert migrate(conn, empty_dir) == []
    assert current_version(conn) == 1


def test_migrate_only_applies_newer_files(conn, empty_dir):
    write(empty_dir / "0001_a.sql", "CREATE TABLE a (id INTEGER);")
    migrate(conn, empty_dir)
    write(empty_dir / "0002_b.sql", "CREATE TABLE b (id INTEGER);")
    assert migrate(conn, empty_dir) == [2]


def test_migrate_raises_when_directory_missing(conn, tmp_path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError, match="migrations directory"):
        migrate(conn, missing)


def test_apply_migration_rolls_back_on_bad_sql(conn, empty_dir):
    write(empty_dir / "0001_bad.sql", "CREATE TABLE x (id INTEGER); GARBAGE SQL;")
    with pytest.raises(sqlite3.Error):
        apply_migration(conn, empty_dir / "0001_bad.sql")
    # version not recorded
    assert current_version(conn) == 0

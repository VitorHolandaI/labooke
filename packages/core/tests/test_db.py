from labooke_core.store.db import connect, open_db
from labooke_core.store.seed_tags import SEED_TAGS, ensure_seed_tags


def test_connect_enables_foreign_keys():
    conn = connect(":memory:")
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1


def test_connect_loads_sqlite_vec():
    conn = connect(":memory:")
    # vec_version() is provided by sqlite-vec
    row = conn.execute("SELECT vec_version()").fetchone()
    assert row[0]


def test_open_db_creates_schema_in_memory():
    conn = open_db(":memory:")
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    expected = {
        "books",
        "tags",
        "book_tags",
        "chunks",
        "bookmarks",
        "reading_progress",
        "schema_version",
    }
    assert expected <= tables


def test_open_db_creates_vec_chunks_virtual_table():
    conn = open_db(":memory:")
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_chunks'"
    ).fetchone()
    assert row is not None


def test_open_db_seeds_default_tags():
    conn = open_db(":memory:")
    rows = conn.execute("SELECT name, slug, color FROM tags ORDER BY id").fetchall()
    assert rows == list(SEED_TAGS)


def test_ensure_seed_tags_is_idempotent():
    conn = open_db(":memory:")
    ensure_seed_tags(conn)
    count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    assert count == len(SEED_TAGS)


def test_open_db_is_idempotent():
    conn = open_db(":memory:")
    version_before = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    # apply migrations again — should be a no-op
    from labooke_core.store.db import MIGRATIONS_DIR
    from labooke_core.store.migrator import migrate

    assert migrate(conn, MIGRATIONS_DIR) == []
    version_after = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version_before == version_after


def test_open_db_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "labooke.db"
    conn = open_db(nested)
    assert nested.exists()
    conn.close()


def test_open_db_enforces_foreign_keys():
    conn = open_db(":memory:")
    # inserting a book_tags row referencing a non-existent book should fail
    try:
        conn.execute("INSERT INTO book_tags (book_id, tag_id) VALUES (999, 999)")
        conn.commit()
        raised = False
    except Exception:
        raised = True
    assert raised


def test_open_db_can_skip_seed_tags():
    conn = open_db(":memory:", seed_tags=False)
    count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    assert count == 0

-- 0001 — Initial schema for labooke.
--
-- Storage philosophy: the original book file is the source of truth for
-- text. This schema stores metadata, tags, chunk page-ranges, and
-- vectors only. No table holds extracted page text.
--
-- See decisions/0001-storage-no-text-in-db.md.

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- ---------- Books ----------

CREATE TABLE IF NOT EXISTS books (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256       TEXT    NOT NULL UNIQUE,
    path         TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    author       TEXT,
    format       TEXT    NOT NULL,
    page_count   INTEGER NOT NULL DEFAULT 0,
    status       TEXT    NOT NULL DEFAULT 'pending',
    ingest_error TEXT,
    created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
CREATE INDEX IF NOT EXISTS idx_books_title  ON books(title);

-- ---------- Tags + junction ----------

CREATE TABLE IF NOT EXISTS tags (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT    NOT NULL,
    slug  TEXT    NOT NULL UNIQUE,
    color TEXT    NOT NULL DEFAULT '#888888'
);

CREATE TABLE IF NOT EXISTS book_tags (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES tags(id)  ON DELETE CASCADE,
    PRIMARY KEY (book_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_book_tags_tag ON book_tags(tag_id);

-- ---------- Chunks (page ranges, one per embedding) ----------

CREATE TABLE IF NOT EXISTS chunks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id    INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page_start INTEGER NOT NULL,
    page_end   INTEGER NOT NULL,
    UNIQUE(book_id, page_start, page_end)
);

CREATE INDEX IF NOT EXISTS idx_chunks_book ON chunks(book_id);

-- ---------- Bookmarks + reading progress ----------

CREATE TABLE IF NOT EXISTS bookmarks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id    INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page_no    INTEGER NOT NULL,
    label      TEXT    NOT NULL,
    note       TEXT,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bookmarks_book ON bookmarks(book_id);

CREATE TABLE IF NOT EXISTS reading_progress (
    book_id    INTEGER PRIMARY KEY REFERENCES books(id) ON DELETE CASCADE,
    page_no    INTEGER NOT NULL,
    updated_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Vectors (sqlite-vec virtual table) ----------
--
-- Dimension matches BAAI/bge-small-en-v1.5 (384). If the embedding
-- model is swapped for one of a different dimension, this table will
-- need a new migration (drop + create with new dim) and a full
-- re-embed of every book.

CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[384]
);

-- 0002 — FTS5 full-text index on book titles for hybrid search.

CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
    title,
    content='books',
    content_rowid='id'
);

INSERT OR IGNORE INTO books_fts(rowid, title) SELECT id, title FROM books;

CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON books BEGIN
    INSERT INTO books_fts(rowid, title) VALUES (new.id, new.title);
END;

CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON books BEGIN
    INSERT INTO books_fts(books_fts, rowid, title) VALUES ('delete', old.id, old.title);
END;

CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON books BEGIN
    INSERT INTO books_fts(books_fts, rowid, title) VALUES ('delete', old.id, old.title);
    INSERT INTO books_fts(rowid, title) VALUES (new.id, new.title);
END;

-- 0009 - Recreate vector indexes for BGE-M3 at 1024 dimensions.
--
-- Existing embeddings are model-specific and cannot be reused. The tables stay
-- empty until the operator explicitly runs "Re-embed all books" in Admin.

DROP TABLE IF EXISTS vec_chunks;
DROP TABLE IF EXISTS vec_summaries;

CREATE VIRTUAL TABLE vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[1024]
);

CREATE VIRTUAL TABLE vec_summaries USING vec0(
    book_id INTEGER PRIMARY KEY,
    embedding FLOAT[1024]
);

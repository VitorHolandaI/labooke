-- 0005 — Summary embedding vectors for the "ask" RAG retrieval.
--
-- One vector per book, embedding the book's generated summary
-- (see 0004 and SummarizeService). AskService runs KNN over this table
-- to pick candidate books, then hands those summaries to the LLM.

CREATE VIRTUAL TABLE IF NOT EXISTS vec_summaries USING vec0(
    book_id   INTEGER PRIMARY KEY,
    embedding FLOAT[384]
);

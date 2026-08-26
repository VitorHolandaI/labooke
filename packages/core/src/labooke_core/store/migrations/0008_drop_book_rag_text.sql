-- 0008 - Keep one generated book description as the catalog search source.
--
-- Passage retrieval continues to use vec_chunks. Book recommendation uses
-- title + description in vec_summaries, so the separate rag_text is redundant.

ALTER TABLE books DROP COLUMN rag_text;

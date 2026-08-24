-- 0007 — Retrieval-oriented summary text for semantic search.
--
-- The LLM enrichment now produces two texts per book: the readable
-- ``description`` (shown in the UI) and a keyword-rich ``rag_text``
-- (embedded into vec_summaries and used by AskService retrieval).
-- See decisions/0015-llm-summarize-ask.md.

ALTER TABLE books ADD COLUMN rag_text TEXT;
-- 0004 — Add a book description/summary column.
--
-- Populated by the LLM enrichment pipeline (SummarizeService), which
-- reads only the first N pages (LABOOKE_LLM_SUMMARY_PAGES) and writes a
-- short summary. Also indexed for the "ask" RAG retrieval over summaries.

ALTER TABLE books ADD COLUMN description TEXT;

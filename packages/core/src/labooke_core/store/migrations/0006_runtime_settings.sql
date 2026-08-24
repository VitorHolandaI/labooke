-- 0006 — Runtime settings KV table.
--
-- Values the Admin page can change at runtime (e.g. how many pages the
-- LLM reads per summary), overriding the LABOOKE_* env defaults.
-- See decisions/0004-chunk-pages-env-var.md for the same pattern.

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
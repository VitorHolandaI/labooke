# 0003 — Four combinable search modes (hybrid default)

**Status:** amended

## Context

"Search" in a book app means several different things. Users want all of
them, sometimes combined. Pure semantic search conflated semantically
similar but distinct topics (e.g. Java vs Python books) — hybrid search
was added to fix this.

## Decision

Four orthogonal modes, all combinable in one request:

1. **Tag filter** — pure SQL filter on `book_tags`. AND / OR / exclude.
   No semantics.
2. **Lexical** — `LIKE` on book title and source filename. Cheap, instant.
3. **Semantic** — vector KNN on `vec_chunks` using `intfloat/multilingual-e5-small`.
   Query encoded with `"query: "` prefix; passages with `"passage: "` prefix
   (E5 asymmetric retrieval).
4. **Hybrid** (default) — combines semantic KNN and BM25 (`chunks_fts` via
   FTS5) using Reciprocal Rank Fusion (RRF, k=60). BM25 uses full chunk
   text, not just titles. Books that rank well in both signals rise; books
   that appear only in one signal are demoted.

API:

```
GET /api/search?q=&tags=&tag_mode=all|any&exclude=&k=10&mode=hybrid&group_by_book=false
GET /api/books?tags=&tag_mode=&exclude=&q=&search=lexical
```

`mode` accepts `hybrid` (default), `semantic`, or `lexical`.
Search response is flat `SearchHit[]`; `?group_by_book=true` groups in
the response. Frontend uses grouped display by default.

## Consequences

- Hybrid mode requires both `vec_chunks` (vectors) and `chunks_fts` (BM25)
  to be populated — reembed-all must run after any model change.
- Tag filter still narrows the candidate book set before KNN and BM25 run.
- Lexical mode answers "where is my Linux Bible PDF?" without invoking
  the embedding model.
- BM25 falls back gracefully to title search (`books_fts`) if `chunks_fts`
  is unavailable (e.g. pre-migration DB).
- Sub-page pinpoint inside large chunks (when `CHUNK_PAGES > 1`) is
  deferred; hits return the full chunk range with a snippet.

## Related

- [0001 — Storage](0001-storage-no-text-in-db.md) — chunk text is now
  stored in the DB specifically to enable BM25 without file I/O.
- [0002 — Tags](0002-tags-flat-with-junction-table.md) — the tag-filter
  mode rides on the junction table.
- [0004 — `CHUNK_PAGES`](0004-chunk-pages-env-var.md) — defines what a
  semantic/BM25 hit's page range actually covers.

# 0016 — LLM auto-tagging uses descriptions and existing tags

**Status:** accepted

## Context

The library now has generated book descriptions and a real controlled tag
vocabulary. Automatic classification is useful, but allowing the model to
invent tags would fragment that vocabulary and overwrite manual organization.

## Decision

- `AutoTagService` receives only the book title, generated `description`, and
  the current tag IDs/names.
- The LLM returns tag IDs in structured JSON. The service validates every ID
  against `TagsRepo.list_all()` before attaching it.
- Automatic classification only adds valid tags. It never creates, renames,
  removes, or replaces manually assigned tags.
- Admin batches run in background and isolate failures per book.
- Prompt text lives in `labooke_core/prompts/book_auto_tag.py`.

## Consequences

- A book needs a generated description before it can be auto-tagged.
- Classification follows the user's established vocabulary.
- Existing manual tags remain authoritative and reversible through the normal
  tag editor.

## Related

- [0002 — Tags flat](0002-tags-flat-with-junction-table.md)
- [0011 — Deferred auto-suggest](0011-defer-auto-suggest-and-highlights.md)
- [0015 — LLM descriptions and recommendations](0015-llm-summarize-ask.md)
- Docs: [ask.md](../docs/ask.md)

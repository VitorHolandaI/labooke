# 0002 — Flat tags; junction table hidden behind domain

**Status:** accepted

## Context

Tags are the killer organizing feature. Users want multi-tag AND/OR
filtering ("books tagged both `linux` AND `security`"). Two questions:

1. Flat or hierarchical (`tech/linux`)?
2. Tag as a real entity (junction table) or a JSON list on the book row?

## Decision

Flat tags for v1. Hierarchy deferred to v2.

Storage uses a junction table:

```
tags(id, name, slug, color)
book_tags(book_id, tag_id)
```

Domain exposes `Book.tags: list[Tag]` — code never touches the junction
table. The repository layer maps SQL ⟷ domain.

## Consequences

- Multi-tag filtering uses indexed JOIN + `GROUP BY HAVING COUNT` for AND
  mode; fast and idiomatic SQL.
- Tag rename is one row; cascade delete is automatic.
- Tag counts come from `GROUP BY`.
- Domain code reads as if tags were a property of the book — matches the
  user's mental model.
- Migration to hierarchy later requires only adding `parent_id`; no data
  reshape.
- No `kind` discriminator on tags (seed vs user); seeds are simply
  pre-inserted on first run, indistinguishable thereafter.
- No `created_at` on tags; keeps the model minimal.

## Related

- [0003 — Search modes](0003-search-modes.md) — the tag-filter mode
  builds on the junction table.
- [0011 — Auto-suggest deferred](0011-defer-auto-suggest-and-highlights.md)
  — would later embed tag names against book chunks.

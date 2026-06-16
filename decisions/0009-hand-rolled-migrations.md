# 0009 — Numbered SQL migrations; no Alembic

**Status:** accepted

## Context

Schema will evolve. Dropping and recreating the DB on every change
destroys the user's library. Alembic is the standard, but it's designed
around SQLAlchemy + Postgres and is heavy for SQLite.

## Decision

Hand-rolled migrator. Migrations are numbered SQL files in
`packages/core/.../store/migrations/`:

```
0001_initial_schema.sql
0002_add_book_description.sql
0003_add_highlights.sql
```

A `schema_version` table tracks the highest applied version. On API
startup, the migrator applies any newer files in order, in a single
transaction each.

Skeleton:

```python
def migrate(db):
    db.execute("CREATE TABLE IF NOT EXISTS schema_version (version INT PRIMARY KEY)")
    current = db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = int(path.name.split("_", 1)[0])
        if version > current:
            db.executescript(path.read_text())
            db.execute("INSERT INTO schema_version VALUES (?)", (version,))
```

## Consequences

- ~50 lines of code; no extra dependency.
- Migrations are plain SQL — easy to review, easy to run by hand if
  needed.
- No rollback support; not worth the complexity at this scale.
- Schema changes are append-only files; old files never edited.

## Related

- [0001 — No text in DB](0001-storage-no-text-in-db.md) — the initial
  schema is small precisely because text isn't persisted.

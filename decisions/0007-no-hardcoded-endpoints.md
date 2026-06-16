# 0007 — All hosts/ports/URLs come from env vars

**Status:** accepted

## Context

The project runs across multiple machines (laptop, server, container).
Hardcoded `localhost:8000` literals force code edits when the
deployment changes.

## Decision

Every host, port, and URL is sourced from environment variables.
Defaults live in:

- `packages/core/.../config.py` — `Settings` (prefix `LABOOKE_`)
- `frontend/vite.config.ts` — via `loadEnv` from `VITE_*` vars
- `.env.example` (root) and `frontend/.env.example` are the canonical
  reference

Backend reads `LABOOKE_API_HOST`, `LABOOKE_API_PORT`,
`LABOOKE_API_RELOAD`, `LABOOKE_CORS_ORIGINS`. Frontend dev reads
`VITE_API_URL` and `VITE_DEV_PORT`. The `gen-types` script uses
`dotenv-cli` so the same `.env` drives it.

## Consequences

- Moving the API to another host requires a single env change, no code
  edit.
- New code MUST follow suit; this is enforced by review, not a linter.
- A literal default in `Settings` is acceptable (clearly overridable) but
  no literal hosts/ports may appear in regular modules.

## Related

- [0008 — Vite proxy](0008-vite-proxy-no-cors.md) — the proxy target
  comes from `VITE_API_URL`.

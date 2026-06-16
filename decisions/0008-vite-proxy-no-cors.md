# 0008 — Vite proxy `/api/*` in dev; no CORS

**Status:** accepted

## Context

Frontend on `5173`, API on `8000`. Either configure CORS on the API or
proxy in the dev server so both look same-origin to the browser.

## Decision

Vite dev server proxies `/api/*` to `${VITE_API_URL}` (default
`http://127.0.0.1:8000`). In production the same path is served by the
frontend `nginx` container, which proxies `/api/` to the api container.

CORS is left configurable via `LABOOKE_CORS_ORIGINS` for the unusual
case where the dev frontend runs on a different machine than the API.

## Consequences

- Frontend code always calls `/api/...` — never an absolute URL — so it
  is identical in dev and prod.
- No `OPTIONS` preflight noise during normal dev.
- The CORS env exists but is empty by default; only set it if you
  actually need cross-origin.

## Related

- [0007 — Env vars](0007-no-hardcoded-endpoints.md) — the proxy target
  and dev port both come from `VITE_*` envs.

# Chowkidar — API

**Base URL:** `https://chowkidar-api.onrender.com` (hosted production pilot) or
`http://localhost:8000` (local)

The hosted service is a single-workspace production pilot with Supabase
email/password auth and durable Postgres reports. Its data and LLM modes are
reported by `/healthz` and `/api/v1/meta`; do not assume live ingestion or live
inference without checking those fields. See [`LIMITATIONS.md`](LIMITATIONS.md).

OpenAPI: `/openapi.json` · Interactive docs: `/docs`

The web client's TypeScript schema is generated from this OpenAPI document.

---

## 1. Authentication

Two adapters are selected by `AUTH_MODE`:

| Mode | Client flow | API behavior |
|---|---|---|
| `dev` | `POST /api/v1/auth/demo-login` with a role | Returns a short-lived demo JWT. Only available when `DEMO_MODE=true`. |
| `supabase` | `POST /api/v1/auth/login`, `/refresh`, `/logout` | Proxies Supabase Auth; verifies JWTs against the project JWKS; maps the identity to the local `users` table for role/name. |

Send the token as:

```http
Authorization: Bearer <access_token>
```

The local `users` table is authoritative for authorization. Supabase
`app_metadata.role` is not trusted. An authenticated Supabase user who is not
provisioned receives `403`.

### Auth endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/auth/config` | public | `auth_mode`, `demo_mode`, `password_auth`, demo users (demo only) |
| `POST` | `/api/v1/auth/login` | public | Email/password login via Supabase |
| `POST` | `/api/v1/auth/refresh` | public | Refresh a Supabase session |
| `POST` | `/api/v1/auth/logout` | bearer | Best-effort Supabase revoke; the client always clears local state |
| `POST` | `/api/v1/auth/demo-login` | public | Demo role login; `403` outside demo mode |
| `GET` | `/api/v1/auth/demo-users` | public | Demo accounts; `404` outside demo mode |
| `GET` | `/api/v1/auth/me` | bearer | Current workspace identity |
| `GET` | `/api/v1/auth/roles` | public | Role names |

Login example:

```bash
curl -sS -X POST "$API/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"analyst@chowkidar.app","password":"..."}'
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "refresh_token": "...",
  "expires_in": 3600,
  "expires_at": 1792825963,
  "user": {
    "id": "00000000-0000-0000-0000-000000000002",
    "email": "analyst@chowkidar.app",
    "name": "Rafiq Hasan",
    "role": "analyst",
    "is_demo": false
  }
}
```

---

## 2. Core endpoints

`GET /healthz` is public. Everything under `/api/v1` requires a bearer token
unless noted.

| Method | Path | Roles | Notes |
|---|---|---|---|
| `GET` | `/healthz` | public | DB, auth, demo, LLM, data mode, connector/scheduler readiness, deployed revision |
| `GET` | `/api/v1/meta` | any | Company, five streams with connector/mode, live readiness, storage backend |
| `GET` | `/api/v1/dashboard/summary` | any | Counts, posture, sources, recent runs |
| `GET` | `/api/v1/signals` | any | Filters: source, severity, status, search |
| `GET` | `/api/v1/signals/{id}` | any | Signal detail |
| `GET` | `/api/v1/sources` | any | Source health, `last_sync_mode`, `last_signal_count`, sanitized `last_error` |
| `POST` | `/api/v1/sources/{id}/sync` | analyst/admin | Sync one source; `fixture`, `hybrid`, or `live` per `DATA_MODE`; rate-limited |
| `GET` | `/api/v1/risks` | any | Filters: priority, status, search |
| `POST` | `/api/v1/risks` | analyst/admin | Create a manual risk |
| `GET` | `/api/v1/risks/{id}` | any | Score breakdown, evidence, actions |
| `POST` | `/api/v1/risks/{id}/actions` | analyst/admin | Add a remediation action |
| `GET` | `/api/v1/risks/{id}/approvals` | any | Approval history |
| `GET` | `/api/v1/actions/{id}` | any | Action detail |
| `PATCH` | `/api/v1/actions/{id}` | analyst/admin | Update status/owner/due date |
| `GET` | `/api/v1/approvals` | any | Queue; filters by status |
| `GET` | `/api/v1/approvals/pending-count` | any | Badge count |
| `POST` | `/api/v1/approvals/{id}/decision` | approver/admin | Approve/reject; rationale required; rate-limited |
| `GET` | `/api/v1/audit` | any | Filtered audit events |
| `GET` | `/api/v1/audit/verify` | admin | Recompute the hash chain |
| `POST` | `/api/v1/pipeline/run` | analyst/admin | Run LangGraph pipeline; rate-limited |
| `GET` | `/api/v1/pipeline/runs` | analyst/admin | Recent runs |
| `GET` | `/api/v1/search?q=` | any | Hybrid cited evidence search |
| `GET` | `/api/v1/graph` | any | Supply-chain graph nodes/edges |
| `GET` | `/api/v1/suppliers` | any | Supplier list |
| `GET` | `/api/v1/evals/summary` | analyst/admin | Latest eval metrics |
| `POST` | `/api/v1/evals/run` | analyst/admin | Re-run golden set; rate-limited |
| `GET` | `/api/v1/reports` | any | Report metadata |
| `POST` | `/api/v1/reports` | analyst/admin | Generate PDF/JSON/Markdown; rate-limited |
| `GET` | `/api/v1/reports/{id}` | any | Report metadata |
| `GET` | `/api/v1/reports/{id}/download` | any | JSON metadata/download descriptor |
| `GET` | `/api/v1/reports/{id}/file` | any | Authenticated bytes; ETag, checksum, `no-store` |

---

## 3. Reports

`POST /api/v1/reports` accepts:

```json
{ "format": "pdf" }
```

Formats: `pdf`, `json`, `markdown`.

The API renders bytes in memory, computes SHA-256, and stores them via
`STORAGE_BACKEND`:

- `local` — API filesystem (`REPORT_STORAGE_DIR`).
- `database` — `report_runs.content` in Postgres.
- `supabase` — private Supabase Storage bucket; falls back to Postgres.

Downloads always pass through the API; storage paths and bucket credentials are
never returned. Response headers include `Content-Disposition`,
`Content-Length`, `Cache-Control: private, no-store`, `X-Content-Type-Options:
nosniff`, and an ETag derived from the checksum.

---

## 4. Errors and limits

FastAPI error shape:

```json
{ "detail": "Human-readable message" }
```

Common statuses:

| Status | Meaning |
|---|---|
| `401` | Missing/expired token or invalid credentials |
| `403` | Authenticated but not provisioned/authorized |
| `404` | Resource not found, or demo endpoint disabled |
| `409` | Report bytes unavailable |
| `422` | Validation error |
| `429` | Rate limit; honor `Retry-After` |
| `502`/`503` | Supabase Auth/Storage or database dependency unavailable; a hard `DATA_MODE=live` source failure returns `502` after persisting the failed run |

Rate limits are process-local:

- Auth endpoints: `AUTH_RATE_LIMIT_PER_MINUTE` per client IP (default 10).
- Mutating/report endpoints: `MUTATION_RATE_LIMIT_PER_MINUTE` (default 30).
- Disable with `RATE_LIMIT_ENABLED=false` only in local tests.

---

## 5. MCP

The read-only FastMCP server is separate from the REST API. See
[`MCP.md`](MCP.md). It exposes evidence, risks, approvals, and the graph; it has
no mutation tools.

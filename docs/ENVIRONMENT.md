# Environment reference

Chowkidar is fixture-first. The default local demo uses deterministic agents and
seeded data, so it does **not** need external AI, Supabase, Neo4j, n8n, Sentry,
or PostHog credentials.

The production pilot path is documented in [`PRODUCTION.md`](PRODUCTION.md).
This file is the variable-level reference.

## Minimum local demo

Copy the reference file once:

```bash
cp .env.example .env
```

The defaults work with `infra/docker-compose.yml`. The values that matter are:

| Variable              | Demo value                                                          | Why                                                          |
| --------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------ |
| `DATABASE_URL`        | `postgresql+psycopg://chowkidar:chowkidar@localhost:5432/chowkidar` | API database; must match Compose                             |
| `AUTH_MODE`           | `dev`                                                               | Enables the seeded demo accounts                             |
| `DEMO_MODE`           | `true`                                                              | Keeps the UI in demo mode                                    |
| `DEV_JWT_SECRET`      | a random value                                                      | Signs demo tokens; replace `change-me`                       |
| `LLM_MODE`            | `mock`                                                              | Deterministic LangGraph path; fastest and most reliable demo |
| `DATA_MODE`           | `fixture`                                                           | Reports fixture-backed data in `/healthz`                    |
| `CORS_ORIGINS`        | `http://localhost:3000`                                             | Browser origin allowed by the API                            |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000`                                             | Web app API base URL                                         |
| `STORAGE_BACKEND`     | `local`                                                             | Local report files; use `database` for durable reports       |

Generate a demo secret with:

```bash
openssl rand -hex 32
```

`TEST_DATABASE_URL` is only for pytest. No other variables are required for the
normal demo.

### Frontend environment

The web client reads only `NEXT_PUBLIC_API_URL`
(`apps/web/src/lib/api/client.ts`). Next.js loads environment files from
`apps/web/`, not the repository root. The localhost default means no web env file
is needed. If the API is on another origin, set it in the shell or in
`apps/web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://api.example.com pnpm --filter @chowkidar/web dev
```

Use **`localhost`**, not `127.0.0.1`, in the browser so the origin matches the
default `CORS_ORIGINS`. The Next.js dev server also blocks some cross-origin dev
resources when the browser host differs from the server host; `next.config.ts`
allows `localhost` and `127.0.0.1`, but matching origins is still simpler.
`NEXT_PUBLIC_AUTH_MODE` and `NEXT_PUBLIC_DEMO_MODE` were removed because the
login page now asks the API for `/api/v1/auth/config`.

## Authentication modes

| Mode | `AUTH_MODE` | `DEMO_MODE` | Behavior |
|---|---|---|---|
| Local demo | `dev` | `true` | One-click seeded role cards; demo tokens signed with `DEV_JWT_SECRET`. |
| Production pilot | `supabase` | `false` | Email/password login through the API's Supabase Auth proxy. Demo endpoints return `403`/`404`; the local `users` table authorizes roles. |
| Misconfigured | `dev` | `false` | No login method; protected endpoints reject requests. Do not deploy this state. |

`DEMO_MODE=true` with `AUTH_MODE=supabase` does not enable demo access; both
conditions are required. `/auth/config` is public so the login page can choose
the correct form without exposing keys.

### Production auth variables

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_URL` | yes | Project URL; used for the Auth proxy, JWKS verification, and Storage |
| `SUPABASE_ANON_KEY` | yes | Public Auth key used only server-side for password/refresh grants |
| `SUPABASE_SERVICE_ROLE_KEY` | for provisioning/Storage | Admin user provisioning and private bucket uploads; never send to the browser |
| `SUPABASE_JWT_AUDIENCE` | no | Default `authenticated` |
| `SUPABASE_AUTH_TIMEOUT_SECONDS` | no | Default `15`; upstream Auth timeout |
| `DEV_JWT_SECRET` | no in Supabase mode | Still set a random value to avoid an unsafe dev fallback |

The API verifies Supabase access tokens against the project JWKS and then maps
the verified `sub` (or email) to the local `users` row. The local row is the
source of truth for `role`, `name`, and `is_active`.

## Report storage

| `STORAGE_BACKEND` | Where bytes live | Use |
|---|---|---|
| `local` | `REPORT_STORAGE_DIR` on the API filesystem | Default offline demo; ephemeral on Render Free |
| `database` | `report_runs.content` (Postgres `bytea`) | Durable without object storage; recommended first hosted cutover |
| `supabase` | Private Supabase Storage bucket | Durable object storage; falls back to Postgres if upload/bucket creation fails |

Optional `REPORT_STORAGE_BUCKET` defaults to `chowkidar-reports` for the API's
Supabase Storage backend. `SUPABASE_STORAGE_BUCKET` is reserved for the
document-ingestion path and is not the report bucket. Downloads always go through
the authenticated API; buckets should remain private.

Report rows record `storage_backend`, `content_sha256`, and `size_bytes`. The
download response includes an ETag and `Cache-Control: private, no-store`.

## Rate limits

| Variable | Default | Applies to |
|---|---|---|
| `RATE_LIMIT_ENABLED` | `true` | All configured limits |
| `AUTH_RATE_LIMIT_PER_MINUTE` | `10` | Login, refresh, demo login (per client IP) |
| `MUTATION_RATE_LIMIT_PER_MINUTE` | `30` | Pipeline, source sync, approvals, evals, report generation/download |

Limits are process-local. Render Free runs one API instance; a multi-instance
deployment needs a shared store. Clients receive `429` with `Retry-After`.

## Live model mode (optional)

Set `LLM_MODE=live` to make the pipeline call a real model through LiteLLM. In
this mode the two keys below are the only external credentials the agents use:

| Variable                          | Required             | Purpose                                       |
| --------------------------------- | -------------------- | --------------------------------------------- |
| `GROQ_API_KEY`                    | yes for Groq calls   | Classification and fallback                   |
| `GEMINI_API_KEY`                  | yes for Gemini calls | Default extraction, verification, and reports |
| `GEMINI_FLASH_MODEL`              | no                   | Default `gemini/gemini-3.8-flash`             |
| `GEMINI_PRO_MODEL`                | no                   | Default `gemini/gemini-pro-latest`            |
| `GROQ_MODEL`                      | no                   | Default `groq/openai/gpt-oss-120b`            |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | no                   | Local fallback when Ollama is running         |
| `LLM_TIMEOUT_SECONDS`             | no                   | Per-provider timeout; default `45`            |

The default chain tries Gemini Flash, then Groq, then Ollama. Verification and
report calls try Gemini Pro first. If a provider is slow or quota-limited, lower
`LLM_TIMEOUT_SECONDS` or make Groq the primary model for every purpose:

```dotenv
LLM_MODE=live
GROQ_API_KEY=<your-key>
GEMINI_FLASH_MODEL=groq/openai/gpt-oss-120b
GEMINI_PRO_MODEL=groq/openai/gpt-oss-120b
GROQ_MODEL=groq/openai/gpt-oss-120b
LLM_TIMEOUT_SECONDS=20
```

Model routing is prefix-based, so a `groq/...` value uses `GROQ_API_KEY` even
when it is assigned to a `GEMINI_*` variable. The model's output still passes
through the deterministic verifier and human approval flow.

For the stage, `LLM_MODE=mock` remains the recommended path: it is fast, has no
network dependency, and produces the same seeded result every time.

**`DATA_MODE=live` is not implemented.** Source sync replays the fixture signal
set. Use `DATA_MODE=fixture` even on the production pilot, and disclose that the
signals are synthetic.

## Optional integrations

None of these are needed for the demo:

| Variables | Status |
|---|---|
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE` | Compose service only; the current graph endpoint reads Postgres |
| `INTERNAL_API_KEY`, `ENABLE_SCHEDULER`, `N8N_API_URL` | Automation scaffolding; not part of the demo path |
| `SENTRY_DSN` | Optional API error reporting |
| `POSTHOG_KEY`, `POSTHOG_HOST` | Reserved; no current web/API client |
| `PHOENIX_ENABLED`, `PHOENIX_COLLECTOR_ENDPOINT` | Optional tracing; dependencies are not installed by default |
| `EMBEDDING_MODE`, `EMBEDDING_DIM`, `EMBEDDING_MODEL`, `RERANKER_MODEL` | Mock embeddings by default; live embedding dependencies are not installed |
| `LOCAL_STORAGE_DIR`, `REPORT_STORAGE_DIR`, `UPLOAD_STORAGE_DIR` | Optional paths; `REPORT_STORAGE_DIR` is used only by `STORAGE_BACKEND=local` |
| `CHOWKIDAR_API_URL`, `CHOWKIDAR_DEMO_ROLE`, `CHOWKIDAR_MCP_TOKEN` | Read-only MCP server only |

## Quick check

```bash
curl -s http://localhost:8000/healthz
```

The demo response should report `"auth_mode":"dev"`, `"demo_mode":true`,
`"llm_mode":"mock"`, `"data_mode":"fixture"`, and `"database":"ok"`. A production
pilot should report `"auth_mode":"supabase"` and `"demo_mode":false`.

## Secrets

`.env` is gitignored. `.env.example` is tracked and must contain only
placeholders. The Supabase service-role key, database password, provider keys,
and generated pilot passwords must never be committed, pasted into the
submission form, or included in screenshots. Generated pilot credentials are
written to `docs/private/supabase-credentials.local.md`, which is gitignored.

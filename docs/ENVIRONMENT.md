# Environment reference

Chowkidar is fixture-first. The default local demo uses deterministic agents and
seeded data, so it does **not** need any external AI, Supabase, Neo4j, n8n,
Sentry, or PostHog credentials.

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

Generate a demo secret with:

```bash
openssl rand -hex 32
```

No other variables are required for the normal demo. `TEST_DATABASE_URL` is only
for pytest.

### Frontend environment

The web client currently reads only `NEXT_PUBLIC_API_URL`
(`apps/web/src/lib/api/client.ts`). Next.js loads environment files from
`apps/web/`, not the repository root. The localhost default means no web env file
is needed. If the API is on another origin, set it in the shell or in
`apps/web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://api.example.com pnpm --filter @chowkidar/web dev
```

`NEXT_PUBLIC_AUTH_MODE`, `NEXT_PUBLIC_DEMO_MODE`, `NEXT_PUBLIC_SENTRY_DSN`, and
`NEXT_PUBLIC_POSTHOG_KEY` are present in `.env.example` but are not read by the
current web app.

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
when it is assigned to a `GEMINI_*` variable. This Groq-only setup is useful for
a live stage demo when Gemini free-tier quota is unavailable. The model's output
still passes through the deterministic verifier and human approval flow.

For the stage, `LLM_MODE=mock` remains the recommended path: it is fast, has no
network dependency, and produces the same seeded result every time.

`DATA_MODE=live` is not an implemented ingestion mode. Source sync replays the
fixture signal set, so use `DATA_MODE=fixture` for the demo.

## Optional integrations

None of these are needed for the demo:

| Variables                                                                                                            | Status                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_AUDIENCE`, `SUPABASE_STORAGE_BUCKET` | Reserved for hosted Supabase Auth/Storage; the demo UI uses seeded accounts and reports use local disk |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`                                                        | Compose service only; the current graph endpoint reads Postgres                                        |
| `INTERNAL_API_KEY`, `ENABLE_SCHEDULER`, `N8N_API_URL`                                                                | Automation scaffolding; not part of the demo path                                                      |
| `SENTRY_DSN`                                                                                                         | Optional API error reporting                                                                           |
| `POSTHOG_KEY`, `POSTHOG_HOST`                                                                                        | Reserved; no current web/API client                                                                    |
| `PHOENIX_ENABLED`, `PHOENIX_COLLECTOR_ENDPOINT`                                                                      | Optional tracing; dependencies are not installed by default                                            |
| `EMBEDDING_MODE`, `EMBEDDING_DIM`, `EMBEDDING_MODEL`, `RERANKER_MODEL`                                               | Mock embeddings by default; live embedding dependencies are not installed                              |
| `LOCAL_STORAGE_DIR`, `REPORT_STORAGE_DIR`, `UPLOAD_STORAGE_DIR`                                                      | Optional paths; `REPORT_STORAGE_DIR` is the one used by report generation                              |
| `CHOWKIDAR_API_URL`, `CHOWKIDAR_DEMO_ROLE`, `CHOWKIDAR_MCP_TOKEN`                                                    | Read-only MCP server only                                                                              |

## Quick check

```bash
curl -s http://localhost:8000/healthz
```

The response should report `"llm_mode":"mock"`, `"data_mode":"fixture"`, and
`"database":"ok"`. Use `localhost`, not `127.0.0.1`, in the browser so the
origin matches `CORS_ORIGINS`.

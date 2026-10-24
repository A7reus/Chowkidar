# Chowkidar — Local setup

**Supported local path:** Linux/macOS, Node.js 22+ (Node 26 works), pnpm 12+,
Python 3.12+ with `uv`, Docker with Compose.

---

## 1. One-time setup

```bash
git clone https://github.com/A7reus/Chowkidar.git
cd Chowkidar
cp .env.example .env
make setup
```

`make setup` installs the pnpm workspace and the API's `dev` extras with `uv`.

Optional: replace `DEV_JWT_SECRET` and `INTERNAL_API_KEY` in `.env` with random
values:

```bash
openssl rand -hex 32
```

For the default demo you do **not** need Supabase, Neo4j, Gemini, Groq, Sentry,
PostHog, or n8n credentials.

---

## 2. Start the demo

```bash
make demo
```

This starts Postgres, runs migrations, reseeds the demo data, and launches the API
and web app. Open <http://localhost:3000> and choose a demo role.

Equivalent manual path:

```bash
make services-up     # Postgres + optional Neo4j
make migrate
make seed
make api             # terminal 1: http://localhost:8000
make web             # terminal 2: http://localhost:3000
```

Use `make dev` to restart the apps without reseeding. `make seed` resets the
synthetic data to the baseline.

### Seed baseline

```
1 company · 4 users · 8 suppliers · 4 sources · 12 signals
11 obligations · 8 risks (3 critical, 3 high, 1 medium, 1 low)
21 actions · 5 approvals (4 pending) · 11 audit events · 12 evidence chunks
```

### Demo accounts

| Role | Email |
|---|---|
| Admin | `admin@chowkidar.demo` |
| Analyst | `analyst@chowkidar.demo` |
| Approver | `approver@chowkidar.demo` |
| Viewer | `viewer@chowkidar.demo` |

The login page uses one-click role cards when `AUTH_MODE=dev` and
`DEMO_MODE=true`.

---

## 3. Commands

| Command | Purpose |
|---|---|
| `make demo` | Fresh seeded demo (Postgres + migrations + seed + apps) |
| `make dev` | Start API + web without reseeding |
| `make api` / `make web` | Start one app |
| `make migrate` | Apply Alembic migrations |
| `make seed` | Reset synthetic demo data |
| `make test` | API pytest + web Vitest |
| `make e2e` | Playwright smoke (API + web must be running) |
| `make lint` | Ruff + ESLint |
| `make typecheck` | Pyright + `tsc` |
| `make check` | Lint + typecheck + unit tests |
| `make evals` | Run the golden set through the database |
| `make api-types` | Regenerate the web OpenAPI types |
| `make docker` | Build the API image |
| `make reset` | Destroy local volumes and rebuild the database |
| `make mcp` | Run the read-only MCP server over stdio |

---

## 4. Environment

The default `.env.example` values target Docker Compose:

```dotenv
DATABASE_URL=postgresql+psycopg://chowkidar:chowkidar@localhost:5432/chowkidar
AUTH_MODE=dev
DEMO_MODE=true
LLM_MODE=mock
DATA_MODE=fixture
STORAGE_BACKEND=local
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`NEXT_PUBLIC_API_URL` is read by the web app at build/start time. If you change
it, restart the web server. The full variable reference is in
[`ENVIRONMENT.md`](ENVIRONMENT.md).

---

## 5. Troubleshooting

### API is not reachable / health check fails

```bash
docker compose -f infra/docker-compose.yml ps
curl -s http://localhost:8000/healthz
```

If the database is unavailable, run `make services-up` and `make migrate`.
Postgres must be healthy before the API starts.

### Login page spins or never hydrates

Use **`http://localhost:3000`**, not `http://127.0.0.1:3000`, so the browser
origin matches `CORS_ORIGINS`. Next.js 16 also blocks some cross-origin dev
resources by default; `apps/web/next.config.ts` allows `localhost` and
`127.0.0.1`, but matching origins remains simplest.

If it persists, restart the web server to clear a stale dev cache:

```bash
# stop the web process, then
rm -rf apps/web/.next
pnpm --filter @chowkidar/web dev
```

### CORS error

`CORS_ORIGINS` must match the browser origin exactly: scheme, host, and port, no
trailing slash. Add multiple origins comma-separated. Restart the API after
changing it.

### Database migration fails

```bash
cd apps/api
uv run alembic current
uv run alembic upgrade head
```

If a local volume is half-initialized, `make reset` destroys and recreates it.
Never run `make reset` against a database with data you need.

### Reports download as 409

The report row exists but the bytes are unavailable. This happens when a local
report was written to `/tmp` and the container restarted. Use
`STORAGE_BACKEND=database` for durable reports, or regenerate the report.

### Demo login returns 403 or 404

The deployment is not in demo mode. Confirm `AUTH_MODE=dev` and
`DEMO_MODE=true` in the API environment. Production deployments should use
`AUTH_MODE=supabase` and `DEMO_MODE=false`; see [`PRODUCTION.md`](PRODUCTION.md).

### Production login says “not provisioned”

The Supabase user is authenticated but has no matching row in the local `users`
table, or the row is inactive. Run
`uv run python -m scripts.provision_supabase_users` with the production database
and service-role key, or map the Supabase UUID/email manually.

### `make e2e` fails because the API is down

Playwright starts only the web server. Start Postgres and the API first:

```bash
make services-up
make migrate
make api
# terminal 2
make web
# terminal 3
make e2e
```

---

## 6. Production setup

Do not use the local demo defaults for a production pilot. Follow
[`PRODUCTION.md`](PRODUCTION.md) for Supabase Auth, account provisioning,
durable report storage, rate limits, and the hosted QA matrix.

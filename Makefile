.PHONY: setup services-up services-down migrate seed api web dev demo test e2e lint typecheck fmt evals api-types mcp mcp-http mcp-risk mcp-risk-http mcp-evidence mcp-evidence-http mcp-tunnel ollama-pull ollama-pull-all test-local-models scrape-bulletins docker check reset

setup:
	pnpm install
	cd apps/api && uv sync --extra dev

services-up:
	docker compose -f infra/docker-compose.yml up -d postgres neo4j

services-all:
	docker compose -f infra/docker-compose.yml up -d

services-down:
	docker compose -f infra/docker-compose.yml down

migrate:
	cd apps/api && uv run alembic upgrade head

seed:
	cd apps/api && uv run python -m app.db.seed

api:
	cd apps/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	pnpm --filter @chowkidar/web dev

dev:
	./scripts/dev.sh

demo:
	docker compose -f infra/docker-compose.yml up -d --wait postgres
	$(MAKE) migrate
	$(MAKE) seed
	./scripts/dev.sh

test:
	cd apps/api && uv run pytest
	pnpm --filter @chowkidar/web test

e2e:
	pnpm --filter @chowkidar/web test:e2e

check: lint typecheck test

lint:
	cd apps/api && uv run ruff check .
	pnpm --filter @chowkidar/web lint

typecheck:
	cd apps/api && uv run pyright
	pnpm --filter @chowkidar/web typecheck

fmt:
	cd apps/api && uv run ruff format .
	pnpm exec prettier --write "**/*.{ts,tsx,js,jsx,json,md,css}"

evals:
	cd apps/api && uv run python -m scripts.run_evals

api-types:
	pnpm --filter @chowkidar/web api:types

mcp:
	cd apps/api && uv run python -m app.mcp.server

# Streamable HTTP transport on http://127.0.0.1:8765/mcp (requires CHOWKIDAR_MCP_HTTP_TOKEN)
mcp-http:
	@test -n "$$CHOWKIDAR_MCP_HTTP_TOKEN" || (echo "Set CHOWKIDAR_MCP_HTTP_TOKEN before starting the HTTP transport" >&2; exit 1)
	cd apps/api && uv run python -m app.mcp.server --transport http

mcp-risk: ; cd apps/api && uv run python -m app.mcp.server
mcp-risk-http: ; cd apps/api && uv run python -m app.mcp.server --transport http --port 8765
mcp-evidence: ; cd apps/api && uv run python -m app.mcp.evidence_server
mcp-evidence-http: ; cd apps/api && uv run python -m app.mcp.evidence_server --transport http --port 8766

# Publish the local MCP endpoint through a Cloudflare quick tunnel (run `make mcp-http` first)
mcp-tunnel:
	cloudflared tunnel --url http://127.0.0.1:8765

# Pull the local model used when OLLAMA_ENABLED=true (see docs/ENVIRONMENT.md)
OLLAMA_PULL_MODEL ?= qwen2.5:7b
ollama-pull:
	ollama pull $(OLLAMA_PULL_MODEL)

# The four-model local suite (~5 GB total): extraction, structured JSON,
# reasoning/verification and triage. See docs/ENVIRONMENT.md.
OLLAMA_SUITE ?= qwen2.5:3b llama3.2:3b deepseek-r1:1.5b gemma2:2b
ollama-pull-all:
	@for model in $(OLLAMA_SUITE); do ollama pull $$model || exit 1; done

# Smoke-test every suite model against a running `ollama serve` and write a
# benchmark log to docs/benchmarks/. Needs only python3.
test-local-models:
	python3 scripts/smoke_local_models.py --models "$(shell echo $(OLLAMA_SUITE) | tr ' ' ',')"

# Scrape regulatory circulars and compliance bulletins via the web scraper connector
scrape-bulletins:
	python3 scripts/scrape_regulatory_bulletins.py --sample

docker:
	docker build -f apps/api/Dockerfile -t chowkidar-api .

reset:
	docker compose -f infra/docker-compose.yml down -v
	docker compose -f infra/docker-compose.yml up -d postgres neo4j
	$(MAKE) migrate
	$(MAKE) seed

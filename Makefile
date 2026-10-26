.PHONY: setup services-up services-down migrate seed api web dev demo test e2e lint typecheck fmt evals api-types mcp mcp-http mcp-tunnel ollama-pull docker check reset

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

# Streamable HTTP transport on http://127.0.0.1:8765/mcp (set CHOWKIDAR_MCP_HTTP_TOKEN to require a bearer token)
mcp-http:
	cd apps/api && uv run python -m app.mcp.server --transport http

# Publish the local MCP endpoint through a Cloudflare quick tunnel (run `make mcp-http` first)
mcp-tunnel:
	cloudflared tunnel --url http://127.0.0.1:8765

# Pull the local model used when OLLAMA_ENABLED=true (see docs/ENVIRONMENT.md)
OLLAMA_PULL_MODEL ?= qwen2.5:7b
ollama-pull:
	ollama pull $(OLLAMA_PULL_MODEL)

docker:
	docker build -f apps/api/Dockerfile -t chowkidar-api .

reset:
	docker compose -f infra/docker-compose.yml down -v
	docker compose -f infra/docker-compose.yml up -d postgres neo4j
	$(MAKE) migrate
	$(MAKE) seed

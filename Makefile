.PHONY: setup services-up services-down migrate seed api web dev test lint typecheck fmt evals api-types reset

setup:
	pnpm install
	cd apps/api && ~/.local/bin/uv sync --extra dev

services-up:
	docker compose -f infra/docker-compose.yml up -d postgres neo4j

services-all:
	docker compose -f infra/docker-compose.yml up -d

services-down:
	docker compose -f infra/docker-compose.yml down

migrate:
	cd apps/api && ~/.local/bin/uv run alembic upgrade head

seed:
	cd apps/api && ~/.local/bin/uv run python -m app.db.seed

api:
	cd apps/api && ~/.local/bin/uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	pnpm --filter @chowkidar/web dev

dev:
	./scripts/dev.sh

test:
	cd apps/api && ~/.local/bin/uv run pytest
	pnpm --filter @chowkidar/web test

lint:
	cd apps/api && ~/.local/bin/uv run ruff check .
	pnpm --filter @chowkidar/web lint

typecheck:
	cd apps/api && ~/.local/bin/uv run pyright
	pnpm --filter @chowkidar/web typecheck

fmt:
	cd apps/api && ~/.local/bin/uv run ruff format .
	pnpm exec prettier --write "**/*.{ts,tsx,js,jsx,json,md,css}"

evals:
	~/.local/bin/uv run --project apps/api python evals/run_evals.py

api-types:
	pnpm --filter @chowkidar/web api:types

reset:
	docker compose -f infra/docker-compose.yml down -v
	docker compose -f infra/docker-compose.yml up -d postgres neo4j
	$(MAKE) migrate
	$(MAKE) seed

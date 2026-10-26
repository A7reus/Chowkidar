from __future__ import annotations

import httpx
import pytest
from app.main import app


@pytest.mark.asyncio
async def test_healthz() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}


@pytest.mark.asyncio
async def test_root_identifies_product_and_disclaimer() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "Chowkidar"
    assert payload["tagline"] == "See the risk. Approve the fix."
    assert "not legal advice" in payload["disclaimer"]


@pytest.mark.asyncio
async def test_meta_exposes_streams_and_scheduler_state() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/meta")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["streams"]) == 5
    assert isinstance(payload["scheduler_enabled"], bool)
    assert isinstance(payload["scheduler_running"], bool)
    assert payload["scheduler_next_run_at"] is None or isinstance(
        payload["scheduler_next_run_at"], str
    )


@pytest.mark.asyncio
async def test_openapi_exposes_required_workflow_endpoints() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in (
        "/api/v1/dashboard/summary",
        "/api/v1/signals",
        "/api/v1/risks",
        "/api/v1/approvals",
        "/api/v1/audit/verify",
        "/api/v1/search",
        "/api/v1/graph",
        "/api/v1/reports",
        "/api/v1/evals/summary",
        "/api/v1/pipeline/run",
    ):
        assert path in paths, path

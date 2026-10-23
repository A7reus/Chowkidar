from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import check_database

settings = get_settings()
logger = logging.getLogger("chowkidar")
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        database_ok = await check_database()
        logger.info("database connection: %s", "ok" if database_ok else "unavailable")
    except Exception as exc:
        logger.warning("database check failed: %s", type(exc).__name__)
    logger.info(
        "starting %s env=%s auth=%s llm=%s data=%s",
        settings.app_name,
        settings.app_env,
        settings.auth_mode,
        settings.llm_mode,
        settings.data_mode,
    )
    yield
    logger.info("stopping %s", settings.app_name)


app = FastAPI(
    title="Chowkidar API",
    description=(
        "Compliance risk intelligence for export supply chains. "
        "See the risk. Approve the fix. This API provides evidence-first risk signals, "
        "deterministic prioritization, remediation drafts, human approval, and an "
        "append-only audit trail. It is not legal advice."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Demo and Supabase authentication"},
        {"name": "meta", "description": "Demo metadata and stream catalog"},
        {"name": "dashboard", "description": "Executive risk overview"},
        {"name": "sources", "description": "Monitored regulatory, sanctions, and news streams"},
        {"name": "signals", "description": "Raw source signals with citations"},
        {"name": "suppliers", "description": "Supply-chain entities"},
        {"name": "risks", "description": "Prioritized risk register and remediation"},
        {"name": "approvals", "description": "Human-in-the-loop decisions"},
        {"name": "audit", "description": "Append-only hash-chained audit trail"},
        {"name": "search", "description": "Hybrid evidence retrieval"},
        {"name": "graph", "description": "Supply-chain and obligation graph"},
        {"name": "reports", "description": "PDF, JSON, and Markdown audit reports"},
        {"name": "pipeline", "description": "LangGraph risk-intelligence pipeline"},
        {"name": "evals", "description": "Golden-set quality evaluation"},
        {"name": "health", "description": "Service health"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Content-Disposition"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


app.include_router(health.router)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "app": settings.app_name,
        "tagline": "See the risk. Approve the fix.",
        "docs": "/docs",
        "health": "/healthz",
        "api": "/api/v1",
        "disclaimer": "Compliance risk intelligence, not legal advice.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104

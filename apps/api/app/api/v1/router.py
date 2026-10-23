from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    approvals,
    audit,
    auth,
    dashboard,
    evals,
    graph,
    meta,
    pipeline,
    reports,
    risks,
    search,
    signals,
    sources,
    suppliers,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(meta.router)
api_router.include_router(dashboard.router)
api_router.include_router(sources.router)
api_router.include_router(signals.router)
api_router.include_router(suppliers.router)
api_router.include_router(risks.router)
api_router.include_router(approvals.router)
api_router.include_router(audit.router)
api_router.include_router(search.router)
api_router.include_router(graph.router)
api_router.include_router(reports.router)
api_router.include_router(pipeline.router)
api_router.include_router(evals.router)

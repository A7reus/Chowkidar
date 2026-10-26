from __future__ import annotations

from fastapi import APIRouter

from app.connectors import live_connector_keys
from app.core.config import get_settings
from app.services.scheduler import scheduler_next_run_at, scheduler_running

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("")
async def meta() -> dict:
    settings = get_settings()
    live_capable = settings.live_connectors_enabled
    streams = [
        {
            "key": "bd_bank",
            "name": "Bangladesh Bank",
            "role": "primary",
            "jurisdiction": "BD",
            "connector": "fixture",
            "mode": "fixture",
        },
        {
            "key": "eu_eurlex",
            "name": "EUR-Lex",
            "role": "primary",
            "jurisdiction": "EU",
            "connector": "fixture",
            "mode": "fixture",
        },
        {
            "key": "us_uflpa",
            "name": "DHS UFLPA Entity List",
            "role": "supporting",
            "jurisdiction": "US",
            "connector": "fixture",
            "mode": "fixture",
        },
        {
            "key": "gdelt",
            "name": "GDELT news",
            "role": "signals",
            "jurisdiction": "GLOBAL",
            "connector": "gdelt",
            "mode": settings.data_mode if live_capable else "fixture",
        },
        {
            "key": "us_federal_register",
            "name": "US Federal Register",
            "role": "supporting",
            "jurisdiction": "US",
            "connector": "federal_register",
            "mode": settings.data_mode if live_capable else "fixture",
        },
    ]
    return {
        "app": settings.app_name,
        "tagline": "See the risk. Approve the fix.",
        "version": "0.1.0",
        "demo": settings.demo_enabled,
        "company": {
            "name": "Padma Apparel Ltd.",
            "country": "Bangladesh",
            "sector": "Ready-made garments",
            "location": "Gazipur, Bangladesh",
            "note": "Fictional pilot company used to evaluate Chowkidar.",
        },
        "buyers": [
            {"name": "Nordwear EU", "country": "Germany", "market": "EU"},
            {"name": "Liberty Threads", "country": "United States", "market": "US"},
        ],
        "streams": streams,
        "capabilities": [
            "Live GDELT and Federal Register ingestion with fixture fallback",
            "Evidence-first risk extraction and scoring",
            "Conditional LangGraph evidence-repair loop",
            "Automated remediation drafting",
            "Human-in-the-loop approval",
            "Append-only audit trail with hash chain",
        ],
        "disclaimer": (
            "Compliance risk intelligence, not legal advice. Every finding is a reviewable "
            "signal, not a determination of legal liability."
        ),
        "llm_mode": settings.llm_mode,
        "llm_live_ready": settings.llm_live_ready,
        "llm_local_enabled": settings.ollama_enabled,
        "llm_prefer_local": settings.llm_prefer_local,
        "embedding_mode": settings.embedding_mode,
        "auth_mode": settings.auth_mode,
        "data_mode": settings.data_mode,
        "live_connectors": live_connector_keys(),
        "live_connectors_enabled": live_capable,
        "scheduler_enabled": settings.enable_scheduler,
        "scheduler_running": scheduler_running(),
        "scheduler_next_run_at": scheduler_next_run_at(),
        "storage_backend": settings.storage_backend,
        "roles": ["admin", "analyst", "approver", "viewer"],
    }

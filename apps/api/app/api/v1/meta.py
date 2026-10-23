from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("")
async def meta() -> dict:
    settings = get_settings()
    return {
        "app": settings.app_name,
        "tagline": "See the risk. Approve the fix.",
        "version": "0.1.0",
        "demo": settings.demo_mode,
        "company": {
            "name": "Padma Apparel Ltd.",
            "country": "Bangladesh",
            "sector": "Ready-made garments",
            "location": "Gazipur, Bangladesh",
            "note": "Fictional company for the Chowkidar demo.",
        },
        "buyers": [
            {"name": "Nordwear EU", "country": "Germany", "market": "EU"},
            {"name": "Liberty Threads", "country": "United States", "market": "US"},
        ],
        "streams": [
            {
                "key": "bd_bank",
                "name": "Bangladesh Bank",
                "role": "primary",
                "jurisdiction": "BD",
            },
            {
                "key": "eu_eurlex",
                "name": "EUR-Lex",
                "role": "primary",
                "jurisdiction": "EU",
            },
            {
                "key": "us_uflpa",
                "name": "DHS UFLPA Entity List",
                "role": "supporting",
                "jurisdiction": "US",
            },
            {
                "key": "gdelt",
                "name": "GDELT news",
                "role": "signals",
                "jurisdiction": "GLOBAL",
            },
        ],
        "capabilities": [
            "Regulatory and supplier risk monitoring",
            "Evidence-first risk extraction and scoring",
            "Automated remediation drafting",
            "Human-in-the-loop approval",
            "Append-only audit trail with hash chain",
        ],
        "disclaimer": (
            "Compliance risk intelligence, not legal advice. Every finding is a reviewable "
            "signal, not a determination of legal liability."
        ),
        "llm_mode": settings.llm_mode,
        "embedding_mode": settings.embedding_mode,
        "auth_mode": settings.auth_mode,
        "roles": ["admin", "analyst", "approver", "viewer"],
    }

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.session import check_database
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthOut)
async def healthz() -> HealthOut:
    settings = get_settings()
    try:
        database_ok = await check_database()
    except Exception:
        database_ok = False
    return HealthOut(
        status="ok" if database_ok else "degraded",
        app=settings.app_name,
        version="0.1.0",
        database="ok" if database_ok else "unavailable",
        auth_mode=settings.auth_mode,
        demo_mode=settings.demo_enabled,
        llm_mode=settings.llm_mode,
        data_mode=settings.data_mode,
        timestamp=datetime.now(UTC),
    )

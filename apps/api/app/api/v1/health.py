from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import APIRouter

from app.connectors import live_connector_keys
from app.core.config import get_settings
from app.db.session import check_database
from app.schemas import HealthOut
from app.services.scheduler import scheduler_running

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
        llm_live_ready=settings.llm_live_ready,
        data_mode=settings.data_mode,
        live_connectors=live_connector_keys(),
        live_connectors_enabled=settings.live_connectors_enabled,
        scheduler_enabled=settings.enable_scheduler,
        scheduler_running=scheduler_running(),
        revision=(os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT") or "")[:12]
        or None,
        timestamp=datetime.now(UTC),
    )

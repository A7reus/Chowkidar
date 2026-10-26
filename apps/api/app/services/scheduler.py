from __future__ import annotations

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.connectors import live_connector_keys
from app.core.config import get_settings
from app.db.models import Source
from app.db.session import AsyncSessionLocal
from app.services.sources import SYSTEM_ACTOR, sync_source

logger = logging.getLogger("chowkidar.scheduler")

_scheduler: AsyncIOScheduler | None = None


async def run_scheduled_sync() -> dict[str, int]:
    """Sync every source that has a registered connector.

    The same service path is used by the HTTP route, so scheduled and manual
    runs produce identical audit entries and source-mode labels.
    """
    settings = get_settings()
    if not settings.live_connectors_enabled:
        logger.info("scheduler skipped: DATA_MODE=%s", settings.data_mode)
        return {"sources": 0, "signals": 0, "failed": 0}

    keys = live_connector_keys()
    totals = {"sources": 0, "signals": 0, "failed": 0}
    async with AsyncSessionLocal() as session:
        sources = list(
            (
                await session.execute(
                    select(Source)
                    .where(Source.connector_key.in_(keys))
                    .order_by(Source.name)
                )
            )
            .scalars()
            .all()
        )
        for source in sources:
            try:
                result = await sync_source(session, source, SYSTEM_ACTOR)
                await session.commit()
                totals["sources"] += 1
                totals["signals"] += result.signals_created
                if result.mode == "live_failed":
                    totals["failed"] += 1
            except Exception:
                await session.rollback()
                totals["failed"] += 1
                logger.exception("scheduled sync failed for %s", source.stream_key)
    logger.info(
        "scheduled sync complete: sources=%s signals=%s failed=%s",
        totals["sources"],
        totals["signals"],
        totals["failed"],
    )
    return totals


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.enable_scheduler:
        logger.info("scheduler disabled (ENABLE_SCHEDULER=false)")
        return
    if _scheduler is not None:
        return
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_scheduled_sync,
        trigger="interval",
        minutes=max(1, settings.scheduler_interval_minutes),
        id="source-sync",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        next_run_time=datetime.now(UTC) if settings.scheduler_run_on_start else None,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "scheduler started: every %s minute(s), run_on_start=%s",
        settings.scheduler_interval_minutes,
        settings.scheduler_run_on_start,
    )


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("scheduler stopped")


def scheduler_running() -> bool:
    return _scheduler is not None and _scheduler.running

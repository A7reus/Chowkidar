from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.services import scheduler as scheduler_service


@pytest.mark.asyncio
@pytest.mark.parametrize("run_on_start", [False, True])
async def test_scheduler_arms_interval_job(
    monkeypatch: pytest.MonkeyPatch, run_on_start: bool
) -> None:
    async def noop_sync() -> dict[str, int]:
        return {"sources": 0, "signals": 0, "failed": 0}

    settings = SimpleNamespace(
        enable_scheduler=True,
        scheduler_interval_minutes=60,
        scheduler_run_on_start=run_on_start,
    )
    scheduler_service.shutdown_scheduler()
    monkeypatch.setattr(scheduler_service, "get_settings", lambda: settings)
    monkeypatch.setattr(scheduler_service, "run_scheduled_sync", noop_sync)

    scheduler_service.start_scheduler()
    try:
        scheduler = scheduler_service._scheduler
        assert scheduler is not None
        assert scheduler.running
        job = scheduler.get_job("source-sync")
        assert job is not None
        assert job.next_run_time is not None
        assert scheduler_service.scheduler_next_run_at() is not None
    finally:
        scheduler_service.shutdown_scheduler()

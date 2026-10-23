from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas import DashboardSummary
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def summary(session: SessionDep, _user: CurrentUser) -> DashboardSummary:
    return await get_dashboard_summary(session)

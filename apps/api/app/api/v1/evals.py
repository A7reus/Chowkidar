from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import AnalystUser, SessionDep
from app.core.ratelimit import rate_limit
from app.db.models import EvalRun
from app.schemas import EvalSummary
from app.services.evals import run_evals

router = APIRouter(prefix="/evals", tags=["evals"])


@router.get("/summary", response_model=EvalSummary)
async def summary(session: SessionDep, _user: AnalystUser) -> EvalSummary:
    latest = (
        await session.execute(select(EvalRun).order_by(EvalRun.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    if latest is not None:
        return EvalSummary.model_validate(latest.metrics)
    result = await run_evals(session)
    await session.commit()
    return result


@router.post(
    "/run",
    response_model=EvalSummary,
    dependencies=[Depends(rate_limit("evals-run", "mutation"))],
)
async def run(session: SessionDep, _user: AnalystUser) -> EvalSummary:
    result = await run_evals(session)
    await session.commit()
    return result

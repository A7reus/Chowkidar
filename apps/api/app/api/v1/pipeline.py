from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AnalystUser, SessionDep
from app.core.ratelimit import rate_limit
from app.schemas import AgentRunOut, PipelineRunRequest, PipelineRunResponse
from app.services.pipeline import list_pipeline_runs, run_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post(
    "/run",
    response_model=PipelineRunResponse,
    dependencies=[Depends(rate_limit("pipeline-run", "mutation"))],
)
async def run(
    payload: PipelineRunRequest,
    session: SessionDep,
    user: AnalystUser,
) -> PipelineRunResponse:
    try:
        result = await run_pipeline(
            session,
            user,
            source_ids=payload.source_ids,
            mode=payload.mode,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {type(exc).__name__}",
        ) from exc
    await session.commit()
    return result


@router.get("/runs", response_model=list[AgentRunOut])
async def runs(session: SessionDep, _user: AnalystUser) -> list[AgentRunOut]:
    return await list_pipeline_runs(session)

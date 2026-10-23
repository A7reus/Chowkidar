from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline import PipelineRunner
from app.core.audit import record_audit
from app.core.auth import UserContext
from app.db.models import AgentRun
from app.schemas import AgentRunOut, PipelineRunResponse
from app.services.serializers import agent_run_out

WORKFLOW = "ingest_extract_map_score_remediate_verify"


async def run_pipeline(
    session: AsyncSession,
    actor: UserContext,
    *,
    source_ids: list[uuid.UUID] | None,
    mode: str,
) -> PipelineRunResponse:
    trace_id = f"run-{uuid.uuid4().hex[:12]}"
    started_at = datetime.now(UTC)
    run = AgentRun(
        workflow=WORKFLOW,
        status="running",
        input={
            "source_ids": [str(source_id) for source_id in source_ids] if source_ids else [],
            "mode": mode,
            "actor": actor.email,
        },
        output={},
        started_at=started_at,
        trace_id=trace_id,
    )
    session.add(run)
    await session.flush()

    runner = PipelineRunner(session, actor, mode=mode)
    try:
        state = await runner.run(source_ids=source_ids, trace_id=trace_id)
    except Exception as exc:
        run.status = "failed"
        run.error = f"{type(exc).__name__}: {exc}"
        run.finished_at = datetime.now(UTC)
        await record_audit(
            session,
            actor=actor,
            action="pipeline.failed",
            entity_type="agent_run",
            entity_id=str(run.id),
            payload={"trace_id": trace_id, "error": run.error, "demo": True},
        )
        await session.flush()
        raise

    persisted = state.get("persisted", [])
    counts = state.get("counts", {})
    errors = state.get("errors", [])
    message = state.get("message", "Pipeline completed.")
    run.status = "completed"
    run.finished_at = datetime.now(UTC)
    run.output = {
        "message": message,
        "counts": counts,
        "created_risk_ids": persisted,
        "errors": errors,
        "mode": runner.mode,
        "verification": [
            {
                "title": item.get("title"),
                "priority": item.get("priority"),
                "status": item.get("verification_status"),
            }
            for item in state.get("verified", [])
        ],
    }
    await session.flush()
    return PipelineRunResponse(
        run=agent_run_out(run),
        message=message,
        counts=counts,
        created_risk_ids=[uuid.UUID(value) for value in persisted],
        errors=errors,
    )


async def list_pipeline_runs(session: AsyncSession, limit: int = 20) -> list[AgentRunOut]:
    runs = list(
        (
            await session.execute(
                select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [agent_run_out(run) for run in runs]

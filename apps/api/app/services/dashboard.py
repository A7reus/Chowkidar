from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Approval, Company, Risk, Signal, Source
from app.schemas import (
    DashboardSummary,
    SourceHealth,
    TopRisk,
    TrendPoint,
)
from app.services.serializers import signal_out


async def get_dashboard_summary(session: AsyncSession) -> DashboardSummary:
    now = datetime.now(UTC)
    company = (await session.execute(select(Company).limit(1))).scalar_one_or_none()

    risks = list(
        (
            await session.execute(
                select(Risk)
                .options(selectinload(Risk.supplier))
                .order_by(Risk.score.desc())
            )
        )
        .scalars()
        .all()
    )
    open_risks = [risk for risk in risks if risk.status != "closed"]
    critical_risks = [risk for risk in open_risks if risk.priority == "critical"]
    high_risks = [risk for risk in open_risks if risk.priority == "high"]

    pending_approvals = (
        await session.execute(
            select(func.count()).select_from(Approval).where(Approval.status == "pending")
        )
    ).scalar_one()
    signals_last_7_days = (
        await session.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.ingested_at >= now - timedelta(days=7))
        )
    ).scalar_one()

    verified = sum(1 for risk in risks if risk.verification_status == "verified")
    verified_rate = round((verified / len(risks)) * 100, 1) if risks else 0.0

    today = now.date()
    trend: list[TrendPoint] = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        cutoff = datetime.combine(day, time.max, tzinfo=UTC)
        open_count = sum(
            1 for risk in risks if risk.status != "closed" and risk.created_at <= cutoff
        )
        high_count = sum(
            1
            for risk in risks
            if risk.priority in {"critical", "high"} and risk.created_at <= cutoff
        )
        trend.append(TrendPoint(date=day.isoformat(), open=open_count, high=high_count))

    top_risks = [
        TopRisk(
            id=risk.id,
            title=risk.title,
            priority=risk.priority,
            score=risk.score,
            supplier_name=risk.supplier.name if risk.supplier else None,
            status=risk.status,
        )
        for risk in open_risks[:5]
    ]

    signal_counts = dict(
        (
            await session.execute(
                select(Signal.source_id, func.count(Signal.id)).group_by(Signal.source_id)
            )
        ).all()
    )
    sources = list((await session.execute(select(Source).order_by(Source.name))).scalars().all())
    source_health = [
        SourceHealth(
            id=source.id,
            name=source.name,
            stream_key=source.stream_key,
            jurisdiction=source.jurisdiction,
            status=source.status,
            connector_key=source.connector_key,
            last_sync_mode=source.last_sync_mode,
            last_synced_at=source.last_synced_at,
            signal_count=int(signal_counts.get(source.id, 0)),
        )
        for source in sources
    ]

    recent_signals = list(
        (
            await session.execute(
                select(Signal)
                .options(selectinload(Signal.source), selectinload(Signal.supplier))
                .order_by(Signal.ingested_at.desc())
                .limit(5)
            )
        )
        .scalars()
        .all()
    )

    return DashboardSummary(
        company_name=company.name if company else "Padma Apparel Ltd.",
        total_risks=len(risks),
        open_risks=len(open_risks),
        critical_risks=len(critical_risks),
        high_risks=len(high_risks),
        pending_approvals=int(pending_approvals),
        signals_last_7_days=int(signals_last_7_days),
        verified_evidence_rate=verified_rate,
        trend=trend,
        top_risks=top_risks,
        source_health=source_health,
        recent_signals=[signal_out(signal) for signal in recent_signals],
    )

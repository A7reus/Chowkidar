from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Signal
from app.schemas import SignalDetail, SignalOut
from app.services.serializers import signal_out


async def list_signals(
    session: AsyncSession,
    *,
    source_id: uuid.UUID | None = None,
    jurisdiction: str | None = None,
    severity: str | None = None,
    signal_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SignalOut], int]:
    conditions = []
    if source_id:
        conditions.append(Signal.source_id == source_id)
    if jurisdiction:
        conditions.append(Signal.jurisdiction == jurisdiction)
    if severity:
        conditions.append(Signal.severity == severity)
    if signal_type:
        conditions.append(Signal.signal_type == signal_type)
    if status:
        conditions.append(Signal.status == status)
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(or_(Signal.title.ilike(pattern), Signal.summary.ilike(pattern)))

    total = (
        await session.execute(
            select(func.count()).select_from(Signal).where(*conditions)
        )
    ).scalar_one()
    signals = list(
        (
            await session.execute(
                select(Signal)
                .options(selectinload(Signal.source), selectinload(Signal.supplier))
                .where(*conditions)
                .order_by(Signal.ingested_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return [signal_out(signal) for signal in signals], int(total)


async def get_signal(session: AsyncSession, signal_id: uuid.UUID) -> SignalDetail | None:
    signal = (
        await session.execute(
            select(Signal)
            .options(selectinload(Signal.source), selectinload(Signal.supplier))
            .where(Signal.id == signal_id)
        )
    ).scalar_one_or_none()
    if signal is None:
        return None
    base = signal_out(signal)
    return SignalDetail(
        **base.model_dump(),
        raw_text=signal.raw_text,
        metadata=signal.extra or {},
    )

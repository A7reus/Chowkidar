from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.auth import UserContext
from app.core.config import ROOT_DIR
from app.db.models import EvidenceChunk, Signal, Source, Supplier
from app.rag.chunking import build_signal_chunks
from app.schemas import SourceOut, SourceSyncResponse
from app.services.serializers import source_out

FIXTURE_PATH = ROOT_DIR / "data" / "fixtures" / "demo.json"


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


async def list_sources(session: AsyncSession) -> list[SourceOut]:
    sources = list((await session.execute(select(Source).order_by(Source.name))).scalars().all())
    return [source_out(source) for source in sources]


async def sync_source(
    session: AsyncSession, source: Source, actor: UserContext
) -> SourceSyncResponse:
    now = datetime.now(UTC)
    fixture = _load_fixture()
    source_config = next(
        (item for item in fixture["sources"] if item["stream_key"] == source.stream_key),
        None,
    )
    signals_created = 0
    if source_config:
        existing_ids = set(
            (
                await session.execute(
                    select(Signal.external_id).where(Signal.source_id == source.id)
                )
            )
            .scalars()
            .all()
        )
        fixture_suppliers = {item["key"]: item["name"] for item in fixture["suppliers"]}
        db_suppliers = {
            supplier.name: supplier.id
            for supplier in (await session.execute(select(Supplier))).scalars().all()
        }
        fixture_signals = [
            item for item in fixture["signals"] if item["source_key"] == source_config["key"]
        ]
        for signal_data in fixture_signals:
            if signal_data["external_id"] in existing_ids:
                continue
            supplier_key = signal_data.get("supplier_key")
            supplier_name = fixture_suppliers.get(supplier_key) if supplier_key else None
            signal = Signal(
                source_id=source.id,
                supplier_id=db_suppliers.get(supplier_name) if supplier_name else None,
                external_id=signal_data["external_id"],
                title=signal_data["title"],
                summary=signal_data["summary"],
                raw_text=signal_data["raw_text"],
                url=signal_data["url"],
                jurisdiction=signal_data["jurisdiction"],
                signal_type=signal_data["signal_type"],
                severity=signal_data["severity"],
                published_at=datetime.fromisoformat(signal_data["published_at"]),
                ingested_at=now,
                status=signal_data.get("status", "new"),
                extra=signal_data.get("metadata", {}),
            )
            session.add(signal)
            await session.flush()
            chunks = build_signal_chunks(
                title=signal.title,
                raw_text=signal.raw_text,
                jurisdiction=signal.jurisdiction,
                citation_url=signal.url,
                citation_label=f"{source.name} — {signal.title}",
                section_path="Signal body",
                extra={"signal_key": signal_data["key"], "demo": True},
            )
            for chunk in chunks:
                session.add(
                    EvidenceChunk(
                        signal_id=signal.id,
                        content=chunk.content,
                        citation_label=chunk.citation_label,
                        citation_url=chunk.citation_url,
                        section_path=chunk.section_path,
                        embedding=chunk.embedding,
                        search_vector=func.to_tsvector("english", chunk.content),
                        extra=chunk.metadata,
                    )
                )
            signals_created += 1

    source.last_synced_at = now
    source.status = "healthy"
    source.last_error = None
    await record_audit(
        session,
        actor=actor,
        action="source.sync",
        entity_type="source",
        entity_id=str(source.id),
        payload={
            "stream_key": source.stream_key,
            "signals_created": signals_created,
            "mode": "fixture",
            "demo": True,
        },
    )
    await session.flush()
    message = (
        f"Synced {source.name}: {signals_created} new signal(s)."
        if signals_created
        else f"Synced {source.name}: no new signals."
    )
    return SourceSyncResponse(
        source=source_out(source),
        signals_created=signals_created,
        message=message,
    )

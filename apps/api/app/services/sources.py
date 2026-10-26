from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors import ConnectorError, get_connector
from app.connectors.base import ConnectorSignal
from app.core.audit import record_audit
from app.core.auth import Role, UserContext
from app.core.config import ROOT_DIR, get_settings
from app.db.models import EvidenceChunk, Signal, Source, Supplier
from app.rag.chunking import build_signal_chunks
from app.schemas import SourceOut, SourceSyncResponse
from app.services.serializers import source_out

FIXTURE_PATH = ROOT_DIR / "data" / "fixtures" / "demo.json"

SYSTEM_ACTOR = UserContext(
    id="system:scheduler",
    email="scheduler@chowkidar.local",
    name="Ingestion scheduler",
    role=Role.ADMIN,
    is_demo=False,
)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _safe_error(exc: Exception) -> str:
    """Return a short operator-facing error without credentials or stack traces."""
    message = str(exc).replace("\n", " ").strip()
    return f"{type(exc).__name__}: {message[:300]}" if message else type(exc).__name__


async def list_sources(session: AsyncSession) -> list[SourceOut]:
    sources = list((await session.execute(select(Source).order_by(Source.name))).scalars().all())
    return [source_out(source) for source in sources]


async def _existing_external_ids(session: AsyncSession, source_id: Any) -> set[str]:
    return set(
        (
            await session.execute(select(Signal.external_id).where(Signal.source_id == source_id))
        )
        .scalars()
        .all()
    )


def _match_supplier_id(text: str, suppliers: list[Supplier]) -> Any:
    """Attach a known supplier only on an exact name mention, never on a guess."""
    lower = text.lower()
    for supplier in suppliers:
        if supplier.name.lower() in lower:
            return supplier.id
    return None


async def _store_signal(
    session: AsyncSession,
    *,
    source: Source,
    external_id: str,
    title: str,
    summary: str,
    raw_text: str,
    url: str,
    jurisdiction: str,
    signal_type: str,
    severity: str,
    published_at: datetime,
    metadata: dict[str, Any],
    supplier_id: Any,
    ingested_at: datetime,
    chunk_extra: dict[str, Any],
) -> None:
    signal = Signal(
        source_id=source.id,
        supplier_id=supplier_id,
        external_id=external_id,
        title=title,
        summary=summary,
        raw_text=raw_text,
        url=url,
        jurisdiction=jurisdiction,
        signal_type=signal_type,
        severity=severity,
        published_at=published_at,
        ingested_at=ingested_at,
        status="new",
        extra=metadata,
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
        extra=chunk_extra,
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


async def _insert_live_signals(
    session: AsyncSession,
    source: Source,
    signals: list[ConnectorSignal],
    *,
    ingested_at: datetime,
) -> int:
    if not signals:
        return 0
    existing = await _existing_external_ids(session, source.id)
    suppliers = list((await session.execute(select(Supplier))).scalars().all())
    created = 0
    for item in signals:
        if item.external_id in existing:
            continue
        existing.add(item.external_id)
        supplier_id = _match_supplier_id(f"{item.title} {item.summary} {item.raw_text}", suppliers)
        await _store_signal(
            session,
            source=source,
            external_id=item.external_id,
            title=item.title,
            summary=item.summary,
            raw_text=item.raw_text,
            url=item.url,
            jurisdiction=item.jurisdiction,
            signal_type=item.signal_type,
            severity=item.severity,
            published_at=item.published_at,
            metadata=item.metadata,
            supplier_id=supplier_id,
            ingested_at=ingested_at,
            chunk_extra={"connector": source.connector_key, "live": True},
        )
        created += 1
    return created


async def _replay_fixture(
    session: AsyncSession,
    source: Source,
    *,
    ingested_at: datetime,
) -> int:
    fixture = _load_fixture()
    source_config = next(
        (item for item in fixture["sources"] if item["stream_key"] == source.stream_key),
        None,
    )
    if source_config is None:
        return 0

    existing = await _existing_external_ids(session, source.id)
    fixture_suppliers = {item["key"]: item["name"] for item in fixture["suppliers"]}
    db_suppliers = {
        supplier.name: supplier.id
        for supplier in (await session.execute(select(Supplier))).scalars().all()
    }
    created = 0
    for signal_data in fixture["signals"]:
        if signal_data["source_key"] != source_config["key"]:
            continue
        if signal_data["external_id"] in existing:
            continue
        existing.add(signal_data["external_id"])
        supplier_key = signal_data.get("supplier_key")
        supplier_name = fixture_suppliers.get(supplier_key) if supplier_key else None
        await _store_signal(
            session,
            source=source,
            external_id=signal_data["external_id"],
            title=signal_data["title"],
            summary=signal_data["summary"],
            raw_text=signal_data["raw_text"],
            url=signal_data["url"],
            jurisdiction=signal_data["jurisdiction"],
            signal_type=signal_data["signal_type"],
            severity=signal_data["severity"],
            published_at=datetime.fromisoformat(signal_data["published_at"]),
            metadata=signal_data.get("metadata", {}),
            supplier_id=db_suppliers.get(supplier_name) if supplier_name else None,
            ingested_at=ingested_at,
            chunk_extra={"signal_key": signal_data["key"], "demo": True, "fixture": True},
        )
        created += 1
    return created


def _mark_source(
    source: Source,
    *,
    status: str,
    mode: str,
    count: int,
    synced_at: datetime,
    error: str | None = None,
) -> None:
    source.last_synced_at = synced_at
    source.last_sync_mode = mode
    source.last_signal_count = count
    source.status = status
    source.last_error = error


async def sync_source(
    session: AsyncSession,
    source: Source,
    actor: UserContext,
) -> SourceSyncResponse:
    """Sync one source using a real connector when enabled, otherwise fixtures.

    Modes:
    - ``fixture``: replay the local fixture and label the run as fixture.
    - ``hybrid``: try the live connector, fall back to the fixture on failure.
    - ``live``: try the live connector; surface a failed run as an error.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    connector = get_connector(source.connector_key)
    live_allowed = settings.live_connectors_enabled and connector is not None
    mode = "fixture"
    status = "healthy"
    error: str | None = None
    signals_created = 0

    if live_allowed and connector is not None:
        try:
            live_signals = await connector.fetch(source)
            signals_created = await _insert_live_signals(
                session, source, live_signals, ingested_at=now
            )
            mode = "live"
            status = "healthy"
        except ConnectorError as exc:
            error = _safe_error(exc)
            if settings.data_mode == "live":
                mode = "live_failed"
                status = "error"
            else:
                signals_created = await _replay_fixture(session, source, ingested_at=now)
                mode = "fixture_fallback"
                status = "degraded"
        except Exception as exc:  # defensive: a connector bug must not fake success
            error = _safe_error(exc)
            if settings.data_mode == "live":
                mode = "live_failed"
                status = "error"
            else:
                signals_created = await _replay_fixture(session, source, ingested_at=now)
                mode = "fixture_fallback"
                status = "degraded"
    else:
        signals_created = await _replay_fixture(session, source, ingested_at=now)
        mode = "fixture"
        if settings.live_connectors_enabled:
            status = "degraded"
            error = (
                "No live connector is configured for this stream; fixture replay was used."
            )

    _mark_source(
        source,
        status=status,
        mode=mode,
        count=signals_created,
        synced_at=now,
        error=error,
    )
    await record_audit(
        session,
        actor=actor,
        action="source.sync",
        entity_type="source",
        entity_id=str(source.id),
        payload={
            "stream_key": source.stream_key,
            "connector": source.connector_key,
            "signals_created": signals_created,
            "mode": mode,
            "status": status,
            "error": error,
            "live": mode == "live",
        },
    )
    await session.flush()

    if mode == "live":
        message = f"Synced {source.name}: {signals_created} new live signal(s)."
    elif mode == "fixture_fallback":
        message = (
            f"Live connector failed for {source.name}; fixture fallback created "
            f"{signals_created} new signal(s). {error}"
        )
    elif mode == "live_failed":
        message = f"Live connector failed for {source.name}: {error}"
    elif status == "degraded":
        message = (
            f"Replayed fixture for {source.name}: {signals_created} new signal(s). "
            f"{error or ''}".strip()
        )
    else:
        message = (
            f"Replayed fixture for {source.name}: {signals_created} new signal(s)."
            if signals_created
            else f"Replayed fixture for {source.name}: no new signals."
        )

    return SourceSyncResponse(
        source=source_out(source),
        signals_created=signals_created,
        message=message,
        mode=mode,
        connector=source.connector_key,
    )

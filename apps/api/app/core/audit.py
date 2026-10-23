from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext
from app.db.models import AuditEvent

GENESIS_HASH = "GENESIS"
AUDIT_LOCK_ID = 918273


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash_payload(
    *,
    prev_hash: str,
    actor_id: str,
    actor_email: str,
    action: str,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any],
    created_at: datetime,
) -> str:
    body = {
        "prev_hash": prev_hash,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload,
        "created_at": created_at.isoformat(),
    }
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


async def record_audit(
    session: AsyncSession,
    *,
    actor: UserContext,
    action: str,
    entity_type: str,
    entity_id: str = "",
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    """Append an audit event and link it to the previous hash.

    A transaction-scoped advisory lock serializes appends so two concurrent
    approvals cannot fork the chain.
    """
    await session.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": AUDIT_LOCK_ID})
    last = (
        await session.execute(select(AuditEvent).order_by(AuditEvent.seq.desc()).limit(1))
    ).scalar_one_or_none()
    prev_hash = last.hash if last else GENESIS_HASH
    created_at = datetime.now(UTC)
    safe_payload = payload or {}
    event_hash = _hash_payload(
        prev_hash=prev_hash,
        actor_id=actor.id,
        actor_email=actor.email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=safe_payload,
        created_at=created_at,
    )
    event = AuditEvent(
        actor_id=actor.id,
        actor_email=actor.email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=safe_payload,
        prev_hash=prev_hash,
        hash=event_hash,
        created_at=created_at,
    )
    session.add(event)
    await session.flush()
    return event


def verify_audit_events(events: list[AuditEvent]) -> dict[str, Any]:
    """Verify a complete, ordered audit chain."""
    expected_prev = GENESIS_HASH
    for index, event in enumerate(events):
        if event.prev_hash != expected_prev:
            return {
                "valid": False,
                "events": len(events),
                "broken_at": index,
                "reason": "prev_hash mismatch",
            }
        expected_hash = _hash_payload(
            prev_hash=event.prev_hash,
            actor_id=event.actor_id,
            actor_email=event.actor_email,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            payload=event.payload or {},
            created_at=event.created_at,
        )
        if event.hash != expected_hash:
            return {
                "valid": False,
                "events": len(events),
                "broken_at": index,
                "reason": "hash mismatch",
            }
        expected_prev = event.hash
    return {
        "valid": True,
        "events": len(events),
        "head": expected_prev,
    }

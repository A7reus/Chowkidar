from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx


class ConnectorError(RuntimeError):
    """A live source could not be fetched or parsed."""


@dataclass(frozen=True)
class ConnectorSignal:
    external_id: str
    title: str
    summary: str
    raw_text: str
    url: str
    jurisdiction: str
    signal_type: str
    severity: str
    published_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceConnector(Protocol):
    key: str

    async def fetch(
        self,
        source: Any,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> list[ConnectorSignal]: ...


def stable_external_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


def clean_text(value: Any, *, limit: int = 8000) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def severity_for(text: str, *, default: str = "medium") -> str:
    lower = text.lower()
    critical_terms = (
        "forced labour",
        "forced labor",
        "child labour",
        "child labor",
        "human trafficking",
        "sanction",
        "uflpa",
        "entity list",
        "embargo",
    )
    high_terms = (
        "export control",
        "export controls",
        "tariff",
        "customs",
        "import ban",
        "supply chain",
        "port strike",
        "factory fire",
        "flood",
        "investigation",
        "outbound investment",
    )
    if any(term in lower for term in critical_terms):
        return "critical"
    if any(term in lower for term in high_terms):
        return "high"
    return default


def now_utc() -> datetime:
    return datetime.now(UTC)


def parse_datetime(value: Any, formats: tuple[str, ...]) -> datetime:
    text = str(value or "").strip()
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return now_utc()

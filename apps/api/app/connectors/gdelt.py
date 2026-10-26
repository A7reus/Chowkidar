from __future__ import annotations

import asyncio
import html
from typing import Any

import httpx

from app.connectors.base import (
    ConnectorError,
    ConnectorSignal,
    clean_text,
    now_utc,
    parse_datetime,
    severity_for,
    stable_external_id,
)
from app.core.config import get_settings

GDELT_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


class GDELTConnector:
    key = "gdelt"

    def _query(self, source: Any) -> str:
        config = getattr(source, "connector_config", None) or {}
        query = str(config.get("query") or "").strip()
        if query:
            return query
        url = str(getattr(source, "url", "") or "")
        if "query=" in url:
            from urllib.parse import parse_qs, urlparse

            values = parse_qs(urlparse(url).query).get("query") or []
            if values:
                return values[0]
        return '"forced labour" OR "supply chain" OR "export controls"'

    async def fetch(
        self,
        source: Any,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> list[ConnectorSignal]:
        settings = get_settings()
        config = getattr(source, "connector_config", None) or {}
        query = self._query(source)
        max_records = int(config.get("max_records") or settings.live_connector_max_records)
        max_records = max(1, min(max_records, 50))
        timespan = str(config.get("timespan") or "7d")
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_records,
            "timespan": timespan,
            "sort": "datedesc",
        }
        owns_client = client is None
        http = client or httpx.AsyncClient(
            timeout=settings.live_connector_timeout_seconds,
            headers={"User-Agent": settings.live_connector_user_agent},
            follow_redirects=True,
        )
        try:
            response = await http.get(GDELT_ENDPOINT, params=params)
            if response.status_code == 429:
                # GDELT asks for at least five seconds between requests.
                await asyncio.sleep(5)
                response = await http.get(GDELT_ENDPOINT, params=params)
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise ConnectorError(
                    "GDELT returned a non-JSON response; the query may be rate-limited"
                ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ConnectorError(
                    "GDELT rate limit reached; retry after five seconds or use fixture fallback"
                ) from exc
            raise ConnectorError(f"GDELT request failed: {type(exc).__name__}") from exc
        except httpx.HTTPError as exc:
            raise ConnectorError(f"GDELT request failed: {type(exc).__name__}") from exc
        finally:
            if owns_client:
                await http.aclose()

        articles = payload.get("articles") or []
        if not isinstance(articles, list):
            raise ConnectorError("GDELT response did not contain an article list")

        signals: list[ConnectorSignal] = []
        seen: set[str] = set()
        retrieved_at = now_utc().isoformat()
        for article in articles:
            if not isinstance(article, dict):
                continue
            url = str(article.get("url") or "").strip()
            title = clean_text(html.unescape(str(article.get("title") or "")), limit=500)
            if not url.startswith("http") or not title:
                continue
            external_id = stable_external_id("gdelt", url)
            if external_id in seen:
                continue
            seen.add(external_id)
            domain = clean_text(article.get("domain"), limit=160)
            country = clean_text(article.get("sourcecountry"), limit=80)
            language = clean_text(article.get("language"), limit=80)
            published_at = parse_datetime(
                article.get("seendate"),
                ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S"),
            )
            raw_text = (
                f"{title}. Reported by {domain or 'an unknown outlet'}"
                f"{f' ({country})' if country else ''}. "
                f"Retrieved from GDELT DOC 2.0 for the query: {query}."
            )
            summary = " · ".join(
                item for item in (domain, country, language) if item
            ) or "GDELT news signal"
            signals.append(
                ConnectorSignal(
                    external_id=external_id,
                    title=title,
                    summary=summary,
                    raw_text=raw_text,
                    url=url,
                    jurisdiction="GLOBAL",
                    signal_type="news",
                    severity=severity_for(f"{title} {summary}"),
                    published_at=published_at,
                    metadata={
                        "connector": self.key,
                        "query": query,
                        "domain": domain,
                        "source_country": country,
                        "language": language,
                        "retrieved_at": retrieved_at,
                        "quote": title,
                    },
                )
            )
        return signals

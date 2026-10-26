from __future__ import annotations

import re
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

FEDERAL_REGISTER_ENDPOINT = "https://www.federalregister.gov/api/v1/documents.json"
DEFAULT_FILTER_TERMS = (
    "export",
    "import",
    "customs",
    "tariff",
    "sanction",
    "forced labor",
    "forced labour",
    "supply chain",
    "entity list",
    "uflpa",
    "embargo",
    "outbound investment",
)


def _matches_filter(text: str, term: str) -> bool:
    """Match a term at a word boundary so 'import' does not match 'important'."""
    return re.search(rf"\b{re.escape(term)}\w*", text) is not None


class FederalRegisterConnector:
    key = "federal_register"

    async def fetch(
        self,
        source: Any,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> list[ConnectorSignal]:
        settings = get_settings()
        config = getattr(source, "connector_config", None) or {}
        term = str(config.get("term") or "export controls")
        per_page = int(config.get("per_page") or settings.live_connector_max_records)
        per_page = max(1, min(per_page, 50))
        document_type = str(config.get("document_type") or "RULE")
        filter_terms = tuple(
            str(item).lower()
            for item in (config.get("filter_terms") or DEFAULT_FILTER_TERMS)
        )

        params: dict[str, str | list[str]] = {
            "conditions[term]": term,
            "per_page": str(per_page),
            "order": "newest",
            "fields[]": [
                "document_number",
                "title",
                "abstract",
                "publication_date",
                "html_url",
                "type",
                "agencies",
            ],
        }
        if document_type:
            params["conditions[type][]"] = [document_type]

        owns_client = client is None
        http = client or httpx.AsyncClient(
            timeout=settings.live_connector_timeout_seconds,
            headers={"User-Agent": settings.live_connector_user_agent},
            follow_redirects=True,
        )
        try:
            response = await http.get(FEDERAL_REGISTER_ENDPOINT, params=params)
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise ConnectorError("Federal Register returned a non-JSON response") from exc
        except httpx.HTTPError as exc:
            raise ConnectorError(
                f"Federal Register request failed: {type(exc).__name__}"
            ) from exc
        finally:
            if owns_client:
                await http.aclose()

        results = payload.get("results") or []
        if not isinstance(results, list):
            raise ConnectorError("Federal Register response did not contain a results list")

        signals: list[ConnectorSignal] = []
        seen: set[str] = set()
        retrieved_at = now_utc().isoformat()
        for item in results:
            if not isinstance(item, dict):
                continue
            document_number = str(item.get("document_number") or "").strip()
            title = clean_text(item.get("title"), limit=500)
            abstract = clean_text(item.get("abstract"), limit=4000)
            if not document_number or not title:
                continue
            searchable = f"{title} {abstract}".lower()
            if filter_terms and not any(
                _matches_filter(searchable, term) for term in filter_terms
            ):
                continue
            url = str(item.get("html_url") or "").strip()
            if not url.startswith("http"):
                url = f"https://www.federalregister.gov/documents/{document_number}"
            external_id = stable_external_id("fr", document_number)
            if external_id in seen:
                continue
            seen.add(external_id)
            agencies = item.get("agencies") or []
            agency_names = [
                clean_text(agency.get("name"), limit=160)
                for agency in agencies
                if isinstance(agency, dict) and agency.get("name")
            ]
            agency_text = ", ".join(agency_names[:3]) or "Federal Register"
            raw_text = (
                f"{title}. {abstract} "
                f"Published by {agency_text}. "
                f"Retrieved from the Federal Register API for the term: {term}."
            ).strip()
            summary = abstract[:600] if abstract else agency_text
            published_at = parse_datetime(
                item.get("publication_date"),
                ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"),
            )
            signals.append(
                ConnectorSignal(
                    external_id=external_id,
                    title=title,
                    summary=summary,
                    raw_text=raw_text,
                    url=url,
                    jurisdiction="US",
                    signal_type="regulatory",
                    severity=severity_for(f"{title} {abstract}"),
                    published_at=published_at,
                    metadata={
                        "connector": self.key,
                        "term": term,
                        "document_number": document_number,
                        "document_type": item.get("type") or document_type,
                        "agencies": agency_names,
                        "retrieved_at": retrieved_at,
                        "quote": title,
                    },
                )
            )
        return signals

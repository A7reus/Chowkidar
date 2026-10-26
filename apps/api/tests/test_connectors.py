from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import respx
from app.connectors.base import ConnectorError, stable_external_id
from app.connectors.federal_register import FEDERAL_REGISTER_ENDPOINT, FederalRegisterConnector
from app.connectors.gdelt import GDELT_ENDPOINT, GDELTConnector

GDELT_PAYLOAD: dict[str, Any] = {
    "articles": [
        {
            "url": "https://example.com/forced-labour-story",
            "title": "Port workers challenge forced labour audit",
            "seendate": "20261024T101500Z",
            "domain": "example.com",
            "sourcecountry": "Bangladesh",
            "language": "English",
        },
        {
            "url": "https://example.com/forced-labour-story",
            "title": "Duplicate result",
            "seendate": "20261024T101500Z",
            "domain": "example.com",
            "sourcecountry": "Bangladesh",
            "language": "English",
        },
        {
            "url": "https://example.com/port-strike",
            "title": "Chattogram port strike enters second day",
            "seendate": "20261024T111500Z",
            "domain": "example.com",
            "sourcecountry": "Bangladesh",
            "language": "English",
        },
    ]
}

FEDERAL_REGISTER_PAYLOAD: dict[str, Any] = {
    "results": [
        {
            "document_number": "2026-17231",
            "title": "Revisions to the Entity List",
            "abstract": "BIS revises the Export Administration Regulations for listed entities.",
            "publication_date": "2026-08-24",
            "html_url": "https://www.federalregister.gov/documents/2026/17231",
            "type": "RULE",
            "agencies": [{"name": "Industry and Security Bureau"}],
        },
        {
            "document_number": "2026-99999",
            "title": "Marine Mammals; Incidental Take",
            "abstract": "A rule unrelated to the Chowkidar demo scope.",
            "publication_date": "2026-08-25",
            "html_url": "https://www.federalregister.gov/documents/2026/99999",
            "type": "RULE",
            "agencies": [{"name": "Fish and Wildlife Service"}],
        },
    ]
}


def _source(**config: Any) -> SimpleNamespace:
    return SimpleNamespace(
        url="https://example.com/source",
        connector_config=config,
    )


@pytest.mark.asyncio
async def test_gdelt_connector_normalizes_and_deduplicates_articles() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(GDELT_ENDPOINT).mock(
            return_value=httpx.Response(200, json=GDELT_PAYLOAD)
        )
        signals = await GDELTConnector().fetch(
            _source(query="forced labour", timespan="7d", max_records=5)
        )

    assert route.called
    assert len(signals) == 2
    first = signals[0]
    assert first.external_id == stable_external_id("gdelt", "https://example.com/forced-labour-story")
    assert first.title == "Port workers challenge forced labour audit"
    assert first.jurisdiction == "GLOBAL"
    assert first.signal_type == "news"
    assert first.severity == "critical"
    assert first.metadata["connector"] == "gdelt"
    assert first.metadata["quote"] == first.title
    assert first.published_at.year == 2026


@pytest.mark.asyncio
async def test_gdelt_connector_reports_non_json_responses() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(GDELT_ENDPOINT).mock(
            return_value=httpx.Response(200, text="rate limited")
        )
        with pytest.raises(ConnectorError, match="non-JSON"):
            await GDELTConnector().fetch(_source(query="forced labour"))


@pytest.mark.asyncio
async def test_federal_register_filters_unrelated_documents() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(FEDERAL_REGISTER_ENDPOINT).mock(
            return_value=httpx.Response(200, json=FEDERAL_REGISTER_PAYLOAD)
        )
        signals = await FederalRegisterConnector().fetch(
            _source(term="export controls", per_page=10, document_type="RULE")
        )

    assert route.called
    assert len(signals) == 1
    signal = signals[0]
    assert signal.external_id == stable_external_id("fr", "2026-17231")
    assert signal.title == "Revisions to the Entity List"
    assert signal.jurisdiction == "US"
    assert signal.signal_type == "regulatory"
    assert signal.metadata["document_number"] == "2026-17231"
    assert signal.metadata["quote"] == signal.title
    assert signal.metadata["agencies"] == ["Industry and Security Bureau"]


@pytest.mark.asyncio
async def test_federal_register_returns_empty_list_for_no_results() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(FEDERAL_REGISTER_ENDPOINT).mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        signals = await FederalRegisterConnector().fetch(_source(term="export controls"))

    assert signals == []


@pytest.mark.asyncio
async def test_connector_http_failures_are_wrapped() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(GDELT_ENDPOINT).mock(return_value=httpx.Response(503))
        with pytest.raises(ConnectorError, match="GDELT request failed"):
            await GDELTConnector().fetch(_source(query="forced labour"))


def test_external_ids_are_stable_and_prefixed() -> None:
    first = stable_external_id("gdelt", "https://example.com/story")
    second = stable_external_id("gdelt", "https://example.com/story")
    other = stable_external_id("gdelt", "https://example.com/other")
    assert first == second
    assert first != other
    assert first.startswith("gdelt:")
    assert len(first) == len("gdelt:") + 24

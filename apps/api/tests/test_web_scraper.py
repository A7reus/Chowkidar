from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import respx
from app.connectors import get_connector, live_connector_keys
from app.connectors.web_scraper import (
    SAMPLE_BULLETINS_HTML,
    WebScraperConnector,
    _classify_severity,
    _detect_jurisdiction,
    parse_regulatory_html,
)

SAMPLE_CARD_HTML = """
<!DOCTYPE html>
<html>
<body>
  <div class="bulletin-list">
    <div class="notice-card">
      <h3 class="title"><a href="/notices/eu-customs-2026-44">EU Trade Advisory on Forced Labor and Textile Due Diligence</a></h3>
      <p class="summary">Mandatory supply chain traceability requirements for all RMG consignments entering EU ports.</p>
      <span class="date">12 November 2026</span>
    </div>
    <div class="circular-item">
      <h4><a href="/circulars/tariff-update">Advisory on Chattogram Port Customs Clearance Tariffs</a></h4>
      <p class="text">Updated export duty and tariff schedules for cotton yarn imports.</p>
      <span class="date">2026-10-18</span>
    </div>
  </div>
</body>
</html>
"""


def _source(**config: Any) -> SimpleNamespace:
    return SimpleNamespace(
        url="https://example.gov/circulars",
        jurisdiction="BD",
        connector_config=config,
    )


def test_connector_registry_registration() -> None:
    connector = get_connector("web_scraper")
    assert connector is not None
    assert isinstance(connector, WebScraperConnector)
    assert "web_scraper" in live_connector_keys()


def test_parse_regulatory_html_table() -> None:
    signals = parse_regulatory_html(
        SAMPLE_BULLETINS_HTML,
        base_url="https://www.bb.org.bd",
        default_jurisdiction="BD",
    )
    assert len(signals) == 5

    s1 = signals[0]
    assert "FEPD Circular No. 18" in s1.title
    assert "Mandatory Repatriation" in s1.title
    assert s1.jurisdiction == "BD"
    assert s1.severity == "critical"
    assert s1.published_at.year == 2026
    assert s1.published_at.month == 11
    assert s1.published_at.day == 15
    assert s1.url == "https://www.bb.org.bd/mediaroom/circulars/fepd/2026/fepd18.pdf"
    assert s1.external_id.startswith("scrape:")
    assert s1.metadata["circular_no"] == "FEPD Circular No. 18"


def test_parse_regulatory_html_cards() -> None:
    signals = parse_regulatory_html(
        SAMPLE_CARD_HTML,
        base_url="https://europa.eu",
        default_jurisdiction="EU",
    )
    assert len(signals) == 2

    eu_signal = next(s for s in signals if "EU Trade Advisory" in s.title)
    assert eu_signal.jurisdiction == "EU"
    assert eu_signal.severity == "critical"  # Contains "forced labor"
    assert eu_signal.url == "https://europa.eu/notices/eu-customs-2026-44"
    assert eu_signal.published_at.year == 2026
    assert eu_signal.published_at.month == 11
    assert eu_signal.published_at.day == 12

    tariff_signal = next(s for s in signals if "Customs Clearance Tariffs" in s.title)
    assert tariff_signal.jurisdiction == "BD"  # Contains "chattogram"
    assert tariff_signal.severity == "high"  # Contains "tariff"


def test_severity_classification_rules() -> None:
    assert _classify_severity("Mandatory repatriation of export proceeds within 120 days") == "critical"
    assert _classify_severity("Notice of entity list trade sanctions against supplier") == "critical"
    assert _classify_severity("Export control and tariff updates on RMG accessories") == "high"
    assert _classify_severity("Due diligence and port strike investigation") == "high"
    assert _classify_severity("General guidelines on trade exhibition visas") == "medium"


def test_jurisdiction_detection() -> None:
    assert _detect_jurisdiction("Bangladesh Bank Foreign Exchange Guidelines") == "BD"
    assert _detect_jurisdiction("Chattogram Port Authority circular on freight") == "BD"
    assert _detect_jurisdiction("EU Customs and CSDDD due diligence rules") == "EU"
    assert _detect_jurisdiction("Federal Register BIS Export Administration") == "US"
    assert _detect_jurisdiction("General International Maritime Safety Advisory") == "GLOBAL"


@pytest.mark.asyncio
async def test_fetch_sample_fixture() -> None:
    connector = WebScraperConnector()
    source = _source(sample=True, max_records=3)
    signals = await connector.fetch(source)
    assert len(signals) == 3
    assert all(s.external_id.startswith("scrape:") for s in signals)


@pytest.mark.asyncio
async def test_fetch_http_dom_success() -> None:
    connector = WebScraperConnector()
    source = _source(engine="dom", sample=False, sample_fallback=False)

    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://example.gov/circulars").mock(
            return_value=httpx.Response(200, text=SAMPLE_BULLETINS_HTML)
        )
        signals = await connector.fetch(source)
        assert len(signals) > 0
        assert "FEPD Circular No. 18" in signals[0].title


@pytest.mark.asyncio
async def test_fetch_http_failure_sample_fallback() -> None:
    connector = WebScraperConnector()
    source = _source(engine="dom", sample=False, sample_fallback=True)

    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://example.gov/circulars").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        signals = await connector.fetch(source)
        # Should gracefully return sample signals instead of crashing
        assert len(signals) == 5


@pytest.mark.asyncio
async def test_fetch_playwright_engine_fallback_on_error() -> None:
    connector = WebScraperConnector()
    source = _source(engine="playwright", sample=False, sample_fallback=True)

    with (
        patch.object(connector, "_fetch_with_playwright", side_effect=RuntimeError("Browser launch failed")),
        respx.mock(assert_all_called=True) as mock,
    ):
        mock.get("https://example.gov/circulars").mock(
            return_value=httpx.Response(200, text=SAMPLE_BULLETINS_HTML)
        )
        signals = await connector.fetch(source)
        assert len(signals) == 5

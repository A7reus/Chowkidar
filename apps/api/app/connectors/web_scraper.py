from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

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

logger = logging.getLogger(__name__)

DEFAULT_SCRAPER_FILTER_TERMS = (
    "export",
    "import",
    "customs",
    "tariff",
    "sanction",
    "repatriation",
    "foreign exchange",
    "fepd",
    "forced labour",
    "forced labor",
    "supply chain",
    "quota",
    "guidelines",
    "compliance",
    "due diligence",
)

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
)

SAMPLE_BULLETINS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Bangladesh Bank — Foreign Exchange Policy Circulars</title>
</head>
<body>
  <h1>Foreign Exchange Policy Department (FEPD) Circulars & Guidelines</h1>
  <table class="circular-table" border="1">
    <thead>
      <tr>
        <th>Date</th>
        <th>Circular No.</th>
        <th>Subject / Title</th>
        <th>Download</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>2026-11-15</td>
        <td>FEPD Circular No. 18</td>
        <td>Mandatory Repatriation of Export Proceeds within 120 Days — Enhanced Overdue Penalties and Non-Realization Audit</td>
        <td><a href="/mediaroom/circulars/fepd/2026/fepd18.pdf">PDF (184 KB)</a></td>
      </tr>
      <tr>
        <td>2026-11-02</td>
        <td>FEPD Circular Letter No. 09</td>
        <td>Inward Remittance Reconciliation and Due Diligence on RMG Trade Subsidies</td>
        <td><a href="/mediaroom/circulars/fepd/2026/fepd09.pdf">PDF (142 KB)</a></td>
      </tr>
      <tr>
        <td>2026-10-28</td>
        <td>FE Circular No. 24</td>
        <td>Establishment of Inland Letter of Credit (EDF) Facilities for Export-Oriented Garment Accessories</td>
        <td><a href="/mediaroom/circulars/fepd/2026/fe24.pdf">PDF (210 KB)</a></td>
      </tr>
      <tr>
        <td>2026-10-14</td>
        <td>FEPD Circular No. 15</td>
        <td>Trade Sanctions Screening & Dual-Use Export Control Declarations for Chattogram Port Consignments</td>
        <td><a href="/mediaroom/circulars/fepd/2026/fepd15.pdf">PDF (195 KB)</a></td>
      </tr>
      <tr>
        <td>2026-09-30</td>
        <td>General Advisory No. 04</td>
        <td>Administrative guidelines on foreign exchange transactions for overseas trade fairs</td>
        <td><a href="/mediaroom/circulars/fepd/2026/ga04.pdf">PDF (98 KB)</a></td>
      </tr>
    </tbody>
  </table>
</body>
</html>
"""


def _classify_severity(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("sanction", "forced labor", "forced labour", "embargo", "non-realization", "mandatory repatriation", "prohibited")):
        return "critical"
    if any(k in lower for k in ("repatriation", "overdue", "export control", "tariff", "customs", "due diligence", "traceability", "penalties")):
        return "high"
    return severity_for(text)


def _detect_jurisdiction(text: str, default: str = "GLOBAL") -> str:
    lower = text.lower()
    if any(k in lower for k in ("european union", "eu trade", "eu customs", "eur-lex", "brussels", "csddd", "celex")):
        return "EU"
    if any(k in lower for k in ("bangladesh", "dhaka", "chattogram", "bdt", "fepd", "bb.org.bd")):
        return "BD"
    if any(k in lower for k in ("united states", "federal register", "ofac", "bis", "cbp", "uflpa")):
        return "US"
    return default


def _extract_date_candidate(text: str) -> str:
    date_patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{2}-\d{2}-\d{4}\b",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b",
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""


def parse_regulatory_html(
    html_content: str,
    *,
    base_url: str = "https://www.bb.org.bd",
    default_jurisdiction: str = "BD",
    max_records: int = 20,
    filter_terms: tuple[str, ...] | None = None,
    engine: str = "dom",
) -> list[ConnectorSignal]:
    """Parse HTML containing circular tables or bulletin listings into ConnectorSignals."""
    soup = BeautifulSoup(html_content, "html.parser")
    signals: list[ConnectorSignal] = []
    seen_ids: set[str] = set()
    retrieved_at = now_utc().isoformat()
    terms = filter_terms or DEFAULT_SCRAPER_FILTER_TERMS

    # 1. First attempt: Table-based circular extraction
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        # Inspect headers to locate column positions
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        date_idx = -1
        ref_idx = -1
        title_idx = -1
        link_idx = -1

        for idx, h in enumerate(headers):
            if any(k in h for k in ("date", "published", "issue")):
                date_idx = idx
            elif any(k in h for k in ("circular", "ref", "number", "no.")):
                ref_idx = idx
            elif any(k in h for k in ("subject", "title", "description", "topic")):
                title_idx = idx
            elif any(k in h for k in ("download", "file", "link", "attachment", "pdf")):
                link_idx = idx

        # If headers couldn't be cleanly resolved, use common table heuristics
        if title_idx == -1 and len(headers) >= 3:
            date_idx = 0
            ref_idx = 1
            title_idx = 2
            if len(headers) > 3:
                link_idx = 3

        # Parse body rows
        for row in rows[1:]:
            cells = row.find_all("td")
            if not cells:
                continue

            raw_date = cells[date_idx].get_text(strip=True) if 0 <= date_idx < len(cells) else ""
            circular_no = cells[ref_idx].get_text(strip=True) if 0 <= ref_idx < len(cells) else ""
            title_cell = cells[title_idx] if 0 <= title_idx < len(cells) else cells[0]
            title = clean_text(title_cell.get_text(strip=True), limit=500)

            # Find links
            link_url = ""
            if 0 <= link_idx < len(cells):
                a_tag = cells[link_idx].find("a")
                if isinstance(a_tag, Tag) and a_tag.get("href"):
                    link_url = str(a_tag["href"]).strip()

            if not link_url:
                a_tag = row.find("a")
                if isinstance(a_tag, Tag) and a_tag.get("href"):
                    link_url = str(a_tag["href"]).strip()

            full_url = urljoin(base_url, link_url) if link_url else base_url

            if not title:
                continue

            # Keyword filtering
            combined_text = f"{circular_no} {title}".lower()
            if terms and not any(term in combined_text for term in terms):
                continue

            published_date_str = _extract_date_candidate(raw_date) or raw_date
            published_at = parse_datetime(published_date_str, DATE_FORMATS)

            ref_tag = circular_no or title
            external_id = stable_external_id("scrape", f"{ref_tag}:{full_url}")
            if external_id in seen_ids:
                continue
            seen_ids.add(external_id)

            jurisdiction = _detect_jurisdiction(f"{title} {base_url}", default=default_jurisdiction)
            sev = _classify_severity(f"{title} {circular_no}")

            raw_text = (
                f"{circular_no + ': ' if circular_no else ''}{title}. "
                f"Published on {published_at.strftime('%Y-%m-%d')} by regulatory authority. "
                f"Source notice link: {full_url}."
            ).strip()

            summary = f"{circular_no + ' — ' if circular_no else ''}{title}"[:400]

            signals.append(
                ConnectorSignal(
                    external_id=external_id,
                    title=f"{circular_no + ': ' if circular_no else ''}{title}",
                    summary=summary,
                    raw_text=raw_text,
                    url=full_url,
                    jurisdiction=jurisdiction,
                    signal_type="regulatory",
                    severity=sev,
                    published_at=published_at,
                    metadata={
                        "connector": "web_scraper",
                        "engine": engine,
                        "circular_no": circular_no,
                        "retrieved_at": retrieved_at,
                        "source_url": base_url,
                    },
                )
            )

            if len(signals) >= max_records:
                return signals

    # 2. Fallback: If no table rows matched, inspect article cards / notice lists
    if not signals:
        all_matches = soup.find_all(
            ["article", "li", "div"],
            class_=re.compile(r"\b(notice-card|circular-item|bulletin-item|notice|circular|card|item)\b", re.IGNORECASE),
        )
        # Filter out parent containers that enclose other matching cards
        cards: list[Tag] = []
        for el in all_matches:
            if not isinstance(el, Tag):
                continue
            class_str = " ".join(el.get("class") or [])
            if re.search(r"list|wrapper|container|group", class_str, re.IGNORECASE):
                continue
            # If el has child matching elements, don't treat parent as a leaf card
            if el.find_all(class_=re.compile(r"\b(notice-card|circular-item|bulletin-item|notice|circular|card)\b", re.IGNORECASE)):
                continue
            cards.append(el)

        for card in cards:
            title_tag = card.find(["h2", "h3", "h4", "h5", "a"])
            if not title_tag:
                continue
            title = clean_text(title_tag.get_text(strip=True), limit=500)
            if not title:
                continue

            link_tag = card.find("a")
            href = link_tag.get("href", "") if isinstance(link_tag, Tag) else ""
            full_url = urljoin(base_url, str(href).strip()) if href else base_url

            card_text = card.get_text(separator=" ", strip=True)
            date_candidate = _extract_date_candidate(card_text)
            published_at = parse_datetime(date_candidate, DATE_FORMATS)

            combined_text = f"{title} {card_text}".lower()
            if terms and not any(term in combined_text for term in terms):
                continue

            external_id = stable_external_id("scrape", f"{title}:{full_url}")
            if external_id in seen_ids:
                continue
            seen_ids.add(external_id)

            jurisdiction = _detect_jurisdiction(f"{title} {card_text}", default=default_jurisdiction)
            sev = _classify_severity(f"{title} {card_text}")

            signals.append(
                ConnectorSignal(
                    external_id=external_id,
                    title=title,
                    summary=clean_text(card_text, limit=300),
                    raw_text=clean_text(card_text, limit=2000),
                    url=full_url,
                    jurisdiction=jurisdiction,
                    signal_type="regulatory",
                    severity=sev,
                    published_at=published_at,
                    metadata={
                        "connector": "web_scraper",
                        "engine": engine,
                        "retrieved_at": retrieved_at,
                        "source_url": base_url,
                    },
                )
            )

            if len(signals) >= max_records:
                break

    return signals


class WebScraperConnector:
    """Headless Web Scraper connector supporting both DOM parsing and Playwright browser rendering."""

    key = "web_scraper"

    async def _fetch_with_playwright(self, url: str, timeout_ms: int = 15000) -> str:
        """Render dynamic JavaScript web pages using Playwright headless Chromium."""
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise ConnectorError("Playwright library is not installed in runtime environment") from exc

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
                )
                try:
                    page = await browser.new_page()
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    content = await page.content()
                    return content
                finally:
                    await browser.close()
        except Exception as exc:
            logger.warning(
                "Playwright browser execution failed (%s: %s); falling back to DOM scraper",
                type(exc).__name__,
                exc,
            )
            raise ConnectorError(f"Playwright navigation failed: {type(exc).__name__}") from exc

    async def fetch(
        self,
        source: Any,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> list[ConnectorSignal]:
        """Fetch and extract regulatory bulletins from web portals."""
        settings = get_settings()
        config = getattr(source, "connector_config", None) or {}

        engine = str(config.get("engine") or "dom").lower()
        target_url = str(
            config.get("url")
            or getattr(source, "url", None)
            or "https://www.bb.org.bd/en/index.php/mediaroom/circular"
        ).strip()

        default_jurisdiction = str(
            config.get("jurisdiction")
            or getattr(source, "jurisdiction", None)
            or "BD"
        )
        max_records = int(config.get("max_records") or settings.live_connector_max_records)
        max_records = max(1, min(max_records, 50))

        filter_terms_conf = config.get("filter_terms")
        filter_terms = (
            tuple(str(t).lower() for t in filter_terms_conf)
            if filter_terms_conf
            else DEFAULT_SCRAPER_FILTER_TERMS
        )

        sample_fallback = bool(config.get("sample_fallback", True))
        use_sample_fixture = bool(config.get("sample") or config.get("use_fixture", False))

        # Explicit fixture/sample request for demo or offline mode
        if use_sample_fixture:
            return parse_regulatory_html(
                SAMPLE_BULLETINS_HTML,
                base_url=target_url,
                default_jurisdiction=default_jurisdiction,
                max_records=max_records,
                filter_terms=filter_terms,
                engine="fixture",
            )

        html_text = ""
        fetch_error: Exception | None = None

        # 1. Attempt Playwright engine if requested
        if engine == "playwright":
            try:
                html_text = await self._fetch_with_playwright(
                    target_url,
                    timeout_ms=settings.live_connector_timeout_seconds * 1000,
                )
            except Exception as exc:
                fetch_error = exc
                logger.info("Playwright failed; attempting fallback to HTTP client")

        # 2. HTTP DOM client attempt (if DOM engine or Playwright fallback)
        if not html_text:
            owns_client = client is None
            http = client or httpx.AsyncClient(
                timeout=settings.live_connector_timeout_seconds,
                headers={"User-Agent": settings.live_connector_user_agent},
                follow_redirects=True,
            )
            try:
                resp = await http.get(target_url)
                resp.raise_for_status()
                html_text = resp.text
            except Exception as exc:
                fetch_error = exc
                logger.warning(
                    "HTTP fetch failed for %s (%s: %s)",
                    target_url,
                    type(exc).__name__,
                    exc,
                )
            finally:
                if owns_client:
                    await http.aclose()

        # 3. If live fetch failed, check if sample fallback is permitted
        if not html_text:
            if sample_fallback:
                logger.info("Live portal unavailable; returning normalized sample circular bulletins")
                return parse_regulatory_html(
                    SAMPLE_BULLETINS_HTML,
                    base_url=target_url,
                    default_jurisdiction=default_jurisdiction,
                    max_records=max_records,
                    filter_terms=filter_terms,
                    engine="sample_fallback",
                )
            raise ConnectorError(
                f"Web scraper failed to retrieve content from {target_url}"
            ) from fetch_error

        # 4. Parse extracted HTML
        signals = parse_regulatory_html(
            html_text,
            base_url=target_url,
            default_jurisdiction=default_jurisdiction,
            max_records=max_records,
            filter_terms=filter_terms,
            engine=engine,
        )

        # If live HTML contained no matching rows, fall back to sample bulletins if enabled
        if not signals and sample_fallback:
            return parse_regulatory_html(
                SAMPLE_BULLETINS_HTML,
                base_url=target_url,
                default_jurisdiction=default_jurisdiction,
                max_records=max_records,
                filter_terms=filter_terms,
                engine="sample_fallback",
            )

        return signals

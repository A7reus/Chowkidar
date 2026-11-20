#!/usr/bin/env python3
"""Scrape regulatory circulars and compliance bulletins.

Uses Chowkidar's WebScraperConnector (supporting DOM parsing and Playwright)
to extract structured regulatory signals from government portals and circular tables.

Usage:
    python3 scripts/scrape_regulatory_bulletins.py
    python3 scripts/scrape_regulatory_bulletins.py --sample
    python3 scripts/scrape_regulatory_bulletins.py --engine playwright --url https://www.bb.org.bd/en/index.php/mediaroom/circular
    python3 scripts/scrape_regulatory_bulletins.py --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure apps/api is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Ensure dummy database settings for offline runner
os.environ.setdefault("DATA_MODE", "hybrid")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://chowkidar:chowkidar@localhost:5432/chowkidar")

from app.connectors.web_scraper import WebScraperConnector, parse_regulatory_html, SAMPLE_BULLETINS_HTML


def print_table(signals: list[dict]) -> None:
    headers = ["Ref / ID", "Date", "Jurisdiction", "Severity", "Title"]
    col_widths = [16, 12, 14, 10, 52]

    header_str = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    separator_str = "-+-".join("-" * w for w in col_widths)

    print("\n" + "=" * len(header_str))
    print("CHOWKIDAR REGULATORY WEB SCRAPER INTELLIGENCE")
    print("=" * len(header_str))
    print(header_str)
    print(separator_str)

    for s in signals:
        ref = (s.get("metadata", {}).get("circular_no") or s.get("external_id", "")[:14])[:col_widths[0]]
        dt = (s.get("published_at") or "")[:10][:col_widths[1]]
        jur = (s.get("jurisdiction") or "GLOBAL")[:col_widths[2]]
        sev = (s.get("severity") or "medium").upper()[:col_widths[3]]
        title = (s.get("title") or "")[:col_widths[4]]

        row_str = " | ".join(
            [
                ref.ljust(col_widths[0]),
                dt.ljust(col_widths[1]),
                jur.ljust(col_widths[2]),
                sev.ljust(col_widths[3]),
                title.ljust(col_widths[4]),
            ]
        )
        print(row_str)

    print("=" * len(header_str))
    print(f"Total extracted signals: {len(signals)}\n")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Chowkidar regulatory circular scraper CLI")
    parser.add_argument("--url", default="https://www.bb.org.bd/en/index.php/mediaroom/circular", help="Target bulletin URL")
    parser.add_argument("--engine", choices=["dom", "playwright"], default="dom", help="Scraping engine")
    parser.add_argument("--sample", action="store_true", help="Force using offline sample fixture")
    parser.add_argument("--limit", type=int, default=10, help="Maximum items to extract")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args()

    connector = WebScraperConnector()
    source = SimpleNamespace(
        url=args.url,
        jurisdiction="BD",
        connector_config={
            "engine": args.engine,
            "sample": args.sample,
            "max_records": args.limit,
            "sample_fallback": True,
        },
    )

    try:
        signals = await connector.fetch(source)
    except Exception as exc:
        print(f"Scraper encountered error: {exc}", file=sys.stderr)
        return 1

    signal_dicts = [
        {
            "external_id": s.external_id,
            "title": s.title,
            "summary": s.summary,
            "raw_text": s.raw_text,
            "url": s.url,
            "jurisdiction": s.jurisdiction,
            "severity": s.severity,
            "published_at": s.published_at.isoformat(),
            "metadata": s.metadata,
        }
        for s in signals
    ]

    if args.json:
        print(json.dumps(signal_dicts, indent=2))
    else:
        print_table(signal_dicts)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

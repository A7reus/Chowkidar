from __future__ import annotations

import hashlib
import uuid

import pytest
from app.db.models import ReportRun
from app.services.reports import (
    _render_report_bytes,
    get_report_content,
    report_is_available,
)


def _report(**overrides: object) -> ReportRun:
    values = {
        "id": uuid.uuid4(),
        "company_id": uuid.uuid4(),
        "format": "markdown",
        "status": "ready",
        "storage_path": "",
        "storage_backend": "database",
        "content": b"# Audit\n",
        "content_sha256": hashlib.sha256(b"# Audit\n").hexdigest(),
        "size_bytes": 8,
    }
    values.update(overrides)
    return ReportRun(**values)


@pytest.mark.asyncio
async def test_database_report_is_durable_and_downloadable() -> None:
    report = _report(content=b"# Audit\n", size_bytes=8)
    assert report_is_available(report) is True
    assert await get_report_content(report) == b"# Audit\n"


@pytest.mark.asyncio
async def test_checksum_mismatch_blocks_download() -> None:
    report = _report(content_sha256="0" * 64)
    assert report_is_available(report) is True
    assert await get_report_content(report) is None


@pytest.mark.asyncio
async def test_missing_database_content_is_not_available() -> None:
    report = _report(content=None)
    assert report_is_available(report) is False
    assert await get_report_content(report) is None


def test_markdown_report_renders_without_filesystem() -> None:
    data = {
        "summary": {
            "company": "Padma Apparel Ltd.",
            "generated_at": "2026-10-24T00:00:00+00:00",
            "generated_by": "analyst@example.com",
            "counts": {
                "risks": 0,
                "critical": 0,
                "high": 0,
                "pending_approvals": 0,
                "verified": 0,
            },
            "sources": [],
            "methodology": "Weighted score.",
            "limitations": ["Synthetic data."],
        },
        "risks": [],
    }
    rendered = _render_report_bytes(data, "markdown")
    assert b"Compliance Risk Audit" in rendered
    assert b"not legal advice" in rendered

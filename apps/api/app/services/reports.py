from __future__ import annotations

import hashlib
import io
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import record_audit
from app.core.auth import UserContext
from app.core.config import ROOT_DIR, get_settings
from app.core.storage import StorageError, download_report, upload_report
from app.db.models import Approval, Company, ReportRun, Risk, Source
from app.schemas import ReportOut
from app.services.serializers import report_out

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "Chowkidar provides compliance risk intelligence, not legal advice. "
    "Every finding is a reviewable signal, not a determination of legal liability. "
    "Consult qualified counsel or a compliance professional before acting."
)

LIMITATIONS = [
    "The demo uses a fictional company and a small set of synthetic and public-source signals.",
    "Source coverage is not exhaustive; absence of a signal is not evidence of compliance.",
    "Risk scores are deterministic triage aids and require human judgment.",
    "Potential matches, including sanctions or forced-labour name matches, are not findings.",
]

CONTENT_TYPES = {
    "json": "application/json",
    "markdown": "text/markdown; charset=utf-8",
    "pdf": "application/pdf",
}

EXTENSIONS = {"json": "json", "markdown": "md", "pdf": "pdf"}


def _reports_dir() -> Path:
    configured = Path(get_settings().report_storage_dir)
    directory = configured if configured.is_absolute() else ROOT_DIR / configured
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _risk_payload(risk: Risk) -> dict[str, Any]:
    return {
        "id": str(risk.id),
        "title": risk.title,
        "description": risk.description,
        "priority": risk.priority,
        "score": risk.score,
        "severity": risk.severity,
        "likelihood": risk.likelihood,
        "exposure": risk.exposure,
        "status": risk.status,
        "category": risk.category,
        "verification_status": risk.verification_status,
        "rationale": risk.rationale,
        "supplier": risk.supplier.name if risk.supplier else None,
        "obligation": risk.obligation.title if risk.obligation else None,
        "evidence": [
            {
                "quote": item.quote,
                "citation_label": item.citation_label,
                "citation_url": item.citation_url,
                "confidence": item.confidence,
                "supports": item.supports,
            }
            for item in risk.evidence
        ],
        "actions": [
            {
                "title": action.title,
                "owner_role": action.owner_role,
                "due_date": action.due_date.isoformat() if action.due_date else None,
                "priority": action.priority,
                "status": action.status,
                "automated": action.automated,
            }
            for action in risk.actions
        ],
        "approvals": [
            {
                "status": approval.status,
                "assigned_to": approval.assigned_to,
                "decision": approval.decision,
                "rationale": approval.rationale,
            }
            for approval in risk.approvals
        ],
    }


async def _collect_report_data(session: AsyncSession, actor: UserContext) -> dict[str, Any]:
    company = (await session.execute(select(Company).limit(1))).scalar_one_or_none()
    risks = list(
        (
            await session.execute(
                select(Risk)
                .options(
                    selectinload(Risk.supplier),
                    selectinload(Risk.obligation),
                    selectinload(Risk.evidence),
                    selectinload(Risk.actions),
                    selectinload(Risk.approvals),
                )
                .order_by(Risk.score.desc())
                .limit(12)
            )
        )
        .scalars()
        .all()
    )
    sources = list((await session.execute(select(Source).order_by(Source.name))).scalars().all())
    pending_approvals = (
        await session.execute(
            select(func.count()).select_from(Approval).where(Approval.status == "pending")
        )
    ).scalar_one()
    summary = {
        "company": company.name if company else "Padma Apparel Ltd.",
        "generated_at": datetime.now(UTC).isoformat(),
        "generated_by": actor.email,
        "counts": {
            "risks": len(risks),
            "critical": sum(1 for risk in risks if risk.priority == "critical"),
            "high": sum(1 for risk in risks if risk.priority == "high"),
            "pending_approvals": int(pending_approvals),
            "verified": sum(
                1 for risk in risks if risk.verification_status == "verified"
            ),
        },
        "sources": [
            {
                "name": source.name,
                "stream_key": source.stream_key,
                "jurisdiction": source.jurisdiction,
                "status": source.status,
                "last_synced_at": source.last_synced_at.isoformat()
                if source.last_synced_at
                else None,
            }
            for source in sources
        ],
        "methodology": (
            "Weighted score = ((severity x 0.40 + likelihood x 0.35 + exposure x 0.25) / 4) x 100. "
            "Priority thresholds: critical >= 80, high >= 60, medium >= 35."
        ),
        "disclaimer": DISCLAIMER,
        "limitations": LIMITATIONS,
    }
    return {
        "summary": summary,
        "risks": [_risk_payload(risk) for risk in risks],
    }


def _render_markdown(data: dict[str, Any]) -> str:
    summary = data["summary"]
    lines: list[str] = [
        f"# {summary['company']} — Compliance Risk Audit",
        "",
        f"Generated: {summary['generated_at']}  ",
        f"Generated by: {summary['generated_by']}",
        "",
        f"> **{DISCLAIMER}**",
        "",
        "## Executive summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Risks in this report | {summary['counts']['risks']} |",
        f"| Critical | {summary['counts']['critical']} |",
        f"| High | {summary['counts']['high']} |",
        f"| Verified evidence | {summary['counts']['verified']} |",
        f"| Pending approvals | {summary['counts']['pending_approvals']} |",
        "",
        "## Prioritized risk register",
        "",
    ]
    for index, risk in enumerate(data["risks"], start=1):
        lines.extend(
            [
                f"### {index}. {risk['title']}",
                "",
                f"- **Priority:** {risk['priority'].upper()} (score {risk['score']})",
                f"- **Supplier:** {risk['supplier'] or 'Company-level'}",
                f"- **Status:** {risk['status']}",
                f"- **Verification:** {risk['verification_status']}",
                f"- **Potential obligation:** {risk['obligation'] or 'Not mapped'}",
                "",
                f"**Why it matters:** {risk['rationale']}",
                "",
            ]
        )
        if risk["evidence"]:
            lines.append("**Evidence**")
            lines.append("")
            for evidence in risk["evidence"]:
                lines.append(f"> {evidence['quote']}")
                lines.append("")
                lines.append(
                    f"Source: [{evidence['citation_label']}]({evidence['citation_url']}) "
                    f"(confidence {evidence['confidence']:.2f})"
                )
                lines.append("")
        if risk["actions"]:
            lines.extend(
                [
                    "**Suggested remediation**",
                    "",
                    "| Action | Owner | Due | Priority | Status |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for action in risk["actions"]:
                lines.append(
                    f"| {action['title']} | {action['owner_role']} | "
                    f"{action['due_date'] or '—'} | {action['priority']} | {action['status']} |"
                )
            lines.append("")
        if risk["approvals"]:
            approval = risk["approvals"][0]
            lines.append(
                f"**Human decision:** {approval['status']} — assigned to {approval['assigned_to']}"
            )
            if approval.get("rationale"):
                lines.append(f"> {approval['rationale']}")
            lines.append("")

    lines.extend(["## Data sources", "", "| Source | Jurisdiction | Status | Last sync |", "| --- | --- | --- | --- |"])
    for source in summary["sources"]:
        lines.append(
            f"| {source['name']} | {source['jurisdiction']} | {source['status']} | "
            f"{source['last_synced_at'] or '—'} |"
        )
    lines.extend(
        [
            "",
            "## Methodology",
            "",
            summary["methodology"],
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["limitations"])
    lines.append("")
    return "\n".join(lines)


def _render_pdf(data: dict[str, Any], target: io.BytesIO) -> None:
    summary = data["summary"]
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ChowkidarTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ChowkidarSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "ChowkidarHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ChowkidarBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )
    small_style = ParagraphStyle(
        "ChowkidarSmall",
        parent=body_style,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
    )
    quote_style = ParagraphStyle(
        "ChowkidarQuote",
        parent=body_style,
        leftIndent=10,
        rightIndent=10,
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=6,
        backColor=colors.HexColor("#f8fafc"),
        spaceBefore=4,
        spaceAfter=6,
    )
    story: list[Any] = [
        Paragraph(escape(summary["company"]), title_style),
        Paragraph("Compliance Risk Audit — prioritized register and remediation plan", heading_style),
        Paragraph(
            escape(
                f"Generated {summary['generated_at']} by {summary['generated_by']}. "
                "Demo data — fictional company."
            ),
            subtitle_style,
        ),
        Paragraph(f"<b>Important:</b> {escape(DISCLAIMER)}", quote_style),
        Paragraph("Executive summary", heading_style),
    ]
    metrics = [
        ["Metric", "Value"],
        ["Risks in this report", str(summary["counts"]["risks"])],
        ["Critical", str(summary["counts"]["critical"])],
        ["High", str(summary["counts"]["high"])],
        ["Verified evidence", str(summary["counts"]["verified"])],
        ["Pending approvals", str(summary["counts"]["pending_approvals"])],
    ]
    table = Table(metrics, colWidths=[85 * mm, 45 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(Paragraph("Prioritized risk register", heading_style))

    for index, risk in enumerate(data["risks"], start=1):
        story.append(
            Paragraph(
                f"{index}. {escape(risk['title'])} "
                f"<font color='#dc2626'>[{escape(risk['priority'].upper())}]</font>",
                body_style,
            )
        )
        story.append(
            Paragraph(
                escape(
                    f"Score {risk['score']} · Supplier: {risk['supplier'] or 'Company-level'} · "
                    f"Status: {risk['status']} · Verification: {risk['verification_status']}"
                ),
                small_style,
            )
        )
        story.append(Paragraph(f"<b>Why it matters:</b> {escape(risk['rationale'])}", body_style))
        for evidence in risk["evidence"]:
            story.append(Paragraph(f"“{escape(evidence['quote'])}”", quote_style))
            story.append(
                Paragraph(
                    escape(
                        f"Source: {evidence['citation_label']} — {evidence['citation_url']} "
                        f"(confidence {evidence['confidence']:.2f})"
                    ),
                    small_style,
                )
            )
        if risk["actions"]:
            story.append(Paragraph("Suggested remediation", small_style))
            action_rows: list[list[Any]] = [["Action", "Owner", "Due", "Status"]]
            for action in risk["actions"]:
                action_rows.append(
                    [
                        Paragraph(escape(action["title"]), small_style),
                        Paragraph(escape(action["owner_role"]), small_style),
                        Paragraph(escape(action["due_date"] or "—"), small_style),
                        Paragraph(escape(action["status"]), small_style),
                    ]
                )
            action_table = Table(
                action_rows, colWidths=[85 * mm, 22 * mm, 22 * mm, 25 * mm], hAlign="LEFT"
            )
            action_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(action_table)
        story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Data sources", heading_style))
    source_rows: list[list[Any]] = [["Source", "Jurisdiction", "Status", "Last sync"]]
    for source in summary["sources"]:
        source_rows.append(
            [
                Paragraph(escape(source["name"]), small_style),
                Paragraph(escape(source["jurisdiction"]), small_style),
                Paragraph(escape(source["status"]), small_style),
                Paragraph(escape(source["last_synced_at"] or "—"), small_style),
            ]
        )
    source_table = Table(source_rows, colWidths=[75 * mm, 22 * mm, 20 * mm, 37 * mm], hAlign="LEFT")
    source_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(source_table)
    story.append(Paragraph("Methodology", heading_style))
    story.append(Paragraph(escape(summary["methodology"]), body_style))
    story.append(Paragraph("Limitations", heading_style))
    for limitation in summary["limitations"]:
        story.append(Paragraph(f"• {escape(limitation)}", small_style))

    document = SimpleDocTemplate(
        target,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{summary['company']} — Compliance Risk Audit",
        author="Chowkidar",
    )
    document.build(story)


def _render_report_bytes(data: dict[str, Any], format: str) -> bytes:
    if format == "json":
        return json.dumps(data, indent=2, default=str).encode("utf-8")
    if format == "markdown":
        return _render_markdown(data).encode("utf-8")
    if format == "pdf":
        buffer = io.BytesIO()
        _render_pdf(data, buffer)
        return buffer.getvalue()
    raise ValueError(f"Unsupported report format: {format}")


async def generate_report(
    session: AsyncSession, format: str, actor: UserContext
) -> ReportOut:
    data = await _collect_report_data(session, actor)
    report_id = uuid.uuid4()
    extension = EXTENSIONS[format]
    content = _render_report_bytes(data, format)
    checksum = hashlib.sha256(content).hexdigest()
    company_id = (await session.execute(select(Company.id).limit(1))).scalar_one()

    settings = get_settings()
    requested_backend = settings.storage_backend.strip().lower()
    storage_backend = requested_backend
    storage_path = ""
    stored_content: bytes | None = None
    storage_warning: str | None = None

    if requested_backend == "supabase":
        key = f"reports/{company_id}/{report_id}.{extension}"
        try:
            storage_path = await upload_report(key, content, CONTENT_TYPES[format])
        except StorageError as exc:
            logger.warning("Supabase Storage unavailable; storing report in Postgres: %s", exc)
            storage_backend = "database"
            stored_content = content
            storage_warning = str(exc)
    elif requested_backend == "database":
        stored_content = content
    elif requested_backend == "local":
        path = _reports_dir() / f"{report_id}.{extension}"
        path.write_bytes(content)
        storage_path = str(path)
    else:
        raise ValueError(f"Unsupported STORAGE_BACKEND: {requested_backend}")

    summary = {
        **data["summary"],
        "risk_ids": [risk["id"] for risk in data["risks"]],
        "content_type": CONTENT_TYPES[format],
        "file_name": f"chowkidar-audit-{report_id}.{extension}",
        "storage_backend": storage_backend,
        "content_sha256": checksum,
        "size_bytes": len(content),
    }
    if storage_warning:
        summary["storage_warning"] = storage_warning

    report = ReportRun(
        id=report_id,
        company_id=company_id,
        format=format,
        status="ready",
        storage_path=storage_path,
        storage_backend=storage_backend,
        content=stored_content,
        content_sha256=checksum,
        size_bytes=len(content),
        summary=summary,
        generated_at=datetime.now(UTC),
    )
    session.add(report)
    await session.flush()
    await record_audit(
        session,
        actor=actor,
        action="report.generated",
        entity_type="report",
        entity_id=str(report.id),
        payload={
            "format": format,
            "risks": data["summary"]["counts"]["risks"],
            "critical": data["summary"]["counts"]["critical"],
            "demo": settings.demo_enabled,
            "storage_backend": storage_backend,
            "content_sha256": checksum,
        },
    )
    return report_out(report)


async def list_reports(session: AsyncSession) -> list[ReportOut]:
    reports = list(
        (
            await session.execute(
                select(ReportRun).order_by(ReportRun.generated_at.desc()).limit(50)
            )
        )
        .scalars()
        .all()
    )
    return [report_out(report) for report in reports]


async def get_report(session: AsyncSession, report_id: uuid.UUID) -> ReportRun | None:
    return await session.get(ReportRun, report_id)


def content_type_for(format: str) -> str:
    return CONTENT_TYPES.get(format, "application/octet-stream")


def file_name_for(report: ReportRun) -> str:
    summary = report.summary or {}
    return str(summary.get("file_name") or f"chowkidar-audit-{report.id}.{report.format}")


def safe_report_path(report: ReportRun) -> Path | None:
    if not report.storage_path:
        return None
    path = Path(report.storage_path).resolve()
    reports_dir = _reports_dir().resolve()
    if reports_dir not in path.parents:
        return None
    if not path.exists() or not path.is_file():
        return None
    return path


def report_is_available(report: ReportRun) -> bool:
    backend = (report.storage_backend or "local").lower()
    if backend == "database":
        return report.content is not None
    if backend == "supabase":
        return bool(report.storage_path)
    return safe_report_path(report) is not None


def _verify_content(report: ReportRun, content: bytes) -> bool:
    if not report.content_sha256:
        return True
    actual = hashlib.sha256(content).hexdigest()
    if actual != report.content_sha256:
        logger.error(
            "Report %s checksum mismatch (expected %s, got %s)",
            report.id,
            report.content_sha256,
            actual,
        )
        return False
    return True


async def get_report_content(report: ReportRun) -> bytes | None:
    backend = (report.storage_backend or "local").lower()
    content: bytes | None = None
    if backend == "database":
        content = report.content
    elif backend == "supabase":
        try:
            content = await download_report(report.storage_path)
        except StorageError as exc:
            logger.warning("Could not download report %s from Supabase Storage: %s", report.id, exc)
            return None
    else:
        path = safe_report_path(report)
        content = path.read_bytes() if path else None
    if content is None:
        return None
    if not _verify_content(report, content):
        return None
    return content

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.deps import AnalystUser, CurrentUser, SessionDep
from app.core.ratelimit import rate_limit
from app.schemas import (
    ReportCreateRequest,
    ReportDownloadResponse,
    ReportListResponse,
    ReportOut,
)
from app.services.reports import (
    content_type_for,
    file_name_for,
    generate_report,
    get_report,
    get_report_content,
    list_reports,
    report_is_available,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=ReportListResponse)
async def reports(session: SessionDep, _user: CurrentUser) -> ReportListResponse:
    items = await list_reports(session)
    return ReportListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=ReportOut,
    dependencies=[Depends(rate_limit("report-generate", "mutation"))],
)
async def create_report(
    payload: ReportCreateRequest,
    session: SessionDep,
    user: AnalystUser,
) -> ReportOut:
    report = await generate_report(session, payload.format, user)
    await session.commit()
    return report


@router.get("/{report_id}", response_model=ReportOut)
async def report_detail(
    report_id: uuid.UUID, session: SessionDep, _user: CurrentUser
) -> ReportOut:
    from app.services.serializers import report_out

    report = await get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report_out(report)


@router.get("/{report_id}/download", response_model=ReportDownloadResponse)
async def report_download(
    report_id: uuid.UUID, session: SessionDep, _user: CurrentUser
) -> ReportDownloadResponse:
    from app.services.serializers import report_out

    report = await get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if not report_is_available(report):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report file is not available",
        )
    return ReportDownloadResponse(
        report=report_out(report),
        download_url=f"/api/v1/reports/{report.id}/file",
        content_type=content_type_for(report.format),
    )


@router.get(
    "/{report_id}/file",
    dependencies=[Depends(rate_limit("report-download", "mutation"))],
)
async def report_file(
    report_id: uuid.UUID, session: SessionDep, _user: CurrentUser
) -> Response:
    report = await get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    content = await get_report_content(report)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report file is not available",
        )
    filename = file_name_for(report)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(content)),
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    }
    if report.content_sha256:
        headers["ETag"] = f'"{report.content_sha256}"'
    return Response(
        content=content,
        media_type=content_type_for(report.format),
        headers=headers,
    )

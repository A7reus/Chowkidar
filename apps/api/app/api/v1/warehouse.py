from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from app.api.deps import AnalystUser, CurrentUser, SessionDep
from app.core.auth import Role
from app.core.config import get_settings
from app.core.ratelimit import rate_limit
from app.db.warehouse import (
    EXPORT_TABLES,
    PRESET_QUERIES,
    AnalyticalWarehouse,
    WarehouseQueryError,
    collect_snapshot,
    get_warehouse,
)
from app.schemas import (
    WarehouseExportIn,
    WarehouseExportOut,
    WarehouseQueryIn,
    WarehouseQueryOut,
    WarehouseSummaryOut,
    WarehouseTableOut,
)

router = APIRouter(prefix="/warehouse", tags=["warehouse"])

WarehouseDep = Annotated[AnalyticalWarehouse, Depends(get_warehouse)]

_EXPORT_FILE = re.compile(
    r"^(?:" + "|".join(EXPORT_TABLES) + r")_\d{8}T\d{6}\d{6}Z\.(?:parquet|csv)$"
)


async def _sync(session: SessionDep, warehouse: AnalyticalWarehouse, *, force: bool) -> None:
    if force or warehouse.is_stale(get_settings().warehouse_sync_ttl_seconds):
        snapshot = await collect_snapshot(session)
        await run_in_threadpool(warehouse.load_snapshot, snapshot)


async def _summary(warehouse: AnalyticalWarehouse) -> WarehouseSummaryOut:
    counts = await run_in_threadpool(warehouse.table_counts)
    total = sum(counts.values())
    return WarehouseSummaryOut(
        status="ready" if total else "empty",
        duckdb_version=warehouse.version,
        storage="in-memory" if warehouse.path == ":memory:" else "file",
        tables=[WarehouseTableOut(name=name, row_count=count) for name, count in counts.items()],
        total_rows=total,
        presets=list(PRESET_QUERIES),  # type: ignore[arg-type]
        last_synced_at=warehouse.last_synced_at,
    )


@router.get("/summary", response_model=WarehouseSummaryOut)
async def summary(
    session: SessionDep,
    warehouse: WarehouseDep,
    _user: CurrentUser,
    refresh: bool = False,
) -> WarehouseSummaryOut:
    await _sync(session, warehouse, force=refresh)
    return await _summary(warehouse)


@router.post(
    "/sync",
    response_model=WarehouseSummaryOut,
    dependencies=[Depends(rate_limit("warehouse-sync", "mutation"))],
)
async def sync(
    session: SessionDep, warehouse: WarehouseDep, _user: AnalystUser
) -> WarehouseSummaryOut:
    await _sync(session, warehouse, force=True)
    return await _summary(warehouse)


@router.post("/query", response_model=WarehouseQueryOut)
async def query(
    payload: WarehouseQueryIn,
    session: SessionDep,
    warehouse: WarehouseDep,
    user: AnalystUser,
) -> WarehouseQueryOut:
    if (payload.view is None) == (payload.sql is None):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of 'view' or 'sql'",
        )
    if payload.sql is not None and user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Custom warehouse SQL is limited to admins; use a preset view",
        )
    await _sync(session, warehouse, force=payload.refresh)
    try:
        if payload.view is not None:
            result = await run_in_threadpool(warehouse.run_preset, payload.view)
        else:
            result = await run_in_threadpool(warehouse.execute_query, payload.sql or "")
    except WarehouseQueryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return WarehouseQueryOut(
        view=payload.view,
        columns=result.columns,
        rows=result.rows,
        row_count=result.row_count,
        truncated=result.truncated,
        execution_ms=result.execution_ms,
        synced_at=warehouse.last_synced_at,
    )


@router.post(
    "/export",
    response_model=WarehouseExportOut,
    dependencies=[Depends(rate_limit("warehouse-export", "mutation"))],
)
async def export(
    payload: WarehouseExportIn,
    session: SessionDep,
    warehouse: WarehouseDep,
    _user: AnalystUser,
) -> WarehouseExportOut:
    await _sync(session, warehouse, force=payload.refresh)
    result = await run_in_threadpool(warehouse.export_table, payload.table, payload.format)
    return WarehouseExportOut(
        table=payload.table,
        format=payload.format,
        file_name=result.path.name,
        path=str(result.path),
        row_count=result.row_count,
        size_bytes=result.size_bytes,
        exported_at=result.exported_at,
        download_url=f"/api/v1/warehouse/exports/{result.path.name}",
    )


@router.get("/exports/{file_name}")
async def download_export(
    file_name: str,
    warehouse: WarehouseDep,
    _user: AnalystUser,
) -> FileResponse:
    if not _EXPORT_FILE.match(file_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    path = warehouse.export_dir / file_name
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    media_type = (
        "application/vnd.apache.parquet" if file_name.endswith(".parquet") else "text/csv"
    )
    return FileResponse(path, media_type=media_type, filename=file_name)

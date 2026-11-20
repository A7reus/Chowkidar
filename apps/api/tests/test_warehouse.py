from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import httpx
import pytest
from app.db.session import get_session
from app.db.warehouse import (
    AnalyticalWarehouse,
    Snapshot,
    WarehouseQueryError,
    collect_snapshot,
    get_warehouse,
)
from app.main import app

T0 = datetime(2026, 11, 1, 9, 0)


def _snapshot(*, break_chain: bool = False) -> Snapshot:
    suppliers = [
        ("s1", None, "Dhaka Knit", "Bangladesh", 1, "apparel", "active", "high", T0),
        ("s2", "s1", "Cotton Growers", "India", 3, "cotton", "active", "medium", T0),
        ("s3", None, "Idle Mill", "Vietnam", 2, "apparel", "active", "low", T0),
    ]
    risks = [
        ("r1", "Forced labour", "regulatory", "critical", "likely", "severe", 92.0,
         "critical", "open", 0.9, "verified", "s2", "Cotton Growers", 3, "India", "US", T0, T0),
        ("r2", "CSDDD gap", "regulatory", "high", "possible", "significant", 70.0,
         "high", "open", 0.8, "verified", "s1", "Dhaka Knit", 1, "Bangladesh", "EU", T0, T0),
        ("r3", "Wage audit", "labour", "medium", "possible", "moderate", 40.0,
         "medium", "closed", 0.7, "needs_review", "s1", "Dhaka Knit", 1, "Bangladesh", "EU",
         T0, T0),
        ("r4", "Company policy", "governance", "low", "rare", "limited", 10.0,
         "low", "open", 0.6, "verified", None, None, None, None, None, T0, T0),
    ]
    signals = [
        ("g1", "Federal Register", "us_fr", "s2", "Entity list", "US", "regulatory",
         "high", "processed", T0, T0),
        ("g2", "GDELT", "gdelt", "s1", "Factory protest", "BD", "news", "medium",
         "new", T0, T0),
        ("g3", "GDELT", "gdelt", "s1", "Wage strike", "BD", "news", "medium", "new", T0, T0),
    ]
    hashes = ["h1", "h2", "h3", "h4"]
    audit = []
    for seq, current in enumerate(hashes, start=1):
        prev = "genesis" if seq == 1 else hashes[seq - 2]
        if break_chain and seq == 3:
            prev = "tampered"
        actor = "admin@demo" if seq != 4 else "approver@demo"
        audit.append(
            (seq, f"e{seq}", f"u{seq}", actor, "risk.update", "risk", "r1", prev, current,
             T0 + timedelta(minutes=seq))
        )
    return {
        "warehouse_suppliers": suppliers,
        "warehouse_risks": risks,
        "warehouse_signals": signals,
        "warehouse_audit": audit,
    }


@pytest.fixture
def warehouse(tmp_path: Path) -> Iterator[AnalyticalWarehouse]:
    wh = AnalyticalWarehouse(":memory:", export_dir=tmp_path / "exports", max_rows=50)
    wh.load_snapshot(_snapshot())
    yield wh
    wh.close()


def test_initializes_empty_tables(tmp_path: Path) -> None:
    wh = AnalyticalWarehouse(":memory:", export_dir=tmp_path)
    try:
        assert wh.table_counts() == {
            "warehouse_suppliers": 0,
            "warehouse_risks": 0,
            "warehouse_signals": 0,
            "warehouse_audit": 0,
        }
        assert wh.is_stale(300)
        assert wh.version == duckdb.__version__
    finally:
        wh.close()


def test_load_snapshot_replaces_rows(warehouse: AnalyticalWarehouse) -> None:
    assert warehouse.table_counts()["warehouse_risks"] == 4
    assert not warehouse.is_stale(300)
    smaller = _snapshot()
    smaller["warehouse_risks"] = smaller["warehouse_risks"][:1]
    counts = warehouse.load_snapshot(smaller)
    assert counts["warehouse_risks"] == 1
    # The sandbox used for ad-hoc SQL holds the same snapshot.
    result = warehouse.execute_query("SELECT COUNT(*) AS n FROM warehouse_risks")
    assert result.rows == [{"n": 1}]


def test_file_backed_warehouse_persists(tmp_path: Path) -> None:
    path = tmp_path / "wh" / "chowkidar.duckdb"
    wh = AnalyticalWarehouse(str(path), export_dir=tmp_path)
    wh.load_snapshot(_snapshot())
    wh.close()
    reopened = AnalyticalWarehouse(str(path), export_dir=tmp_path)
    try:
        assert reopened.table_counts()["warehouse_audit"] == 4
    finally:
        reopened.close()


def test_risk_distribution_uses_window_aggregates(warehouse: AnalyticalWarehouse) -> None:
    result = warehouse.query_risk_distribution()
    by_bucket = {(row["jurisdiction"], row["supplier_tier"]): row for row in result.rows}
    assert by_bucket[("US", "3")]["severity_rank"] == 1
    assert by_bucket[("US", "3")]["share_pct"] == 25.0
    eu = by_bucket[("EU", "1")]
    assert eu["risk_count"] == 2
    assert eu["high_priority_count"] == 1
    assert eu["avg_score"] == 55.0
    assert eu["max_score"] == 70.0
    assert ("UNSPECIFIED", "company") in by_bucket
    assert sum(row["share_pct"] for row in result.rows) == pytest.approx(100.0)


def test_audit_integrity_detects_broken_chain(tmp_path: Path) -> None:
    wh = AnalyticalWarehouse(":memory:", export_dir=tmp_path)
    try:
        wh.load_snapshot(_snapshot())
        intact = {row["actor_email"]: row for row in wh.query_audit_integrity_metrics().rows}
        assert intact["admin@demo"]["events"] == 3
        assert intact["admin@demo"]["share_pct"] == 75.0
        assert sum(row["broken_links"] for row in intact.values()) == 0

        wh.load_snapshot(_snapshot(break_chain=True))
        broken = wh.query_audit_integrity_metrics().rows
        assert sum(row["broken_links"] for row in broken) == 1
    finally:
        wh.close()


def test_supplier_exposure_ranks_open_risk(warehouse: AnalyticalWarehouse) -> None:
    rows = warehouse.query_supplier_exposure().rows
    assert [row["supplier_id"] for row in rows] == ["s2", "s1", "s3"]
    dhaka = rows[1]
    assert dhaka["open_risks"] == 1  # the closed risk is excluded
    assert dhaka["signal_count"] == 2
    assert rows[2]["open_risks"] == 0
    assert rows[2]["exposure_rank"] == 3


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE warehouse_risks",
        "DELETE FROM warehouse_risks",
        "COPY warehouse_risks TO 'leak.csv'",
        "ATTACH 'other.duckdb'",
        "SET enable_external_access = true",
        "SELECT 1; SELECT 2",
        "",
    ],
)
def test_execute_query_rejects_non_select(warehouse: AnalyticalWarehouse, sql: str) -> None:
    with pytest.raises(WarehouseQueryError):
        warehouse.execute_query(sql)
    assert warehouse.table_counts()["warehouse_risks"] == 4


def test_execute_query_cannot_read_files(warehouse: AnalyticalWarehouse, tmp_path: Path) -> None:
    secret = tmp_path / "secret.csv"
    secret.write_text("a\n1\n")
    with pytest.raises(WarehouseQueryError):
        warehouse.execute_query(f"SELECT * FROM read_csv('{secret}')")  # noqa: S608


def test_execute_query_caps_rows_and_serializes(warehouse: AnalyticalWarehouse) -> None:
    result = warehouse.execute_query("SELECT range AS n, now() AS at FROM range(200)")
    assert result.row_count == 50
    assert result.truncated
    assert isinstance(result.rows[0]["at"], str)


def test_parquet_export_round_trip(warehouse: AnalyticalWarehouse) -> None:
    path, rows, size = warehouse.export_parquet("risks")
    assert path.suffix == ".parquet"
    assert rows == 4
    assert size == path.stat().st_size > 0
    check = duckdb.connect()
    try:
        row = check.execute(
            "SELECT COUNT(*), SUM(score) FROM read_parquet(?)", [str(path)]
        ).fetchone()
        columns = [d[0] for d in check.execute(
            "SELECT * FROM read_parquet(?) LIMIT 0", [str(path)]
        ).description or []]
    finally:
        check.close()
    assert row == (4, 212.0)
    assert "supplier_tier" in columns


def test_csv_export(warehouse: AnalyticalWarehouse) -> None:
    result = warehouse.export_table("audit_events", "csv")
    lines = result.path.read_text().splitlines()
    assert lines[0].startswith("seq,event_id")
    assert len(lines) == 5


def test_export_rejects_unknown_dataset(warehouse: AnalyticalWarehouse) -> None:
    with pytest.raises(WarehouseQueryError):
        warehouse.export_table("users")


async def test_collect_snapshot_from_database() -> None:
    from app.db.session import AsyncSessionLocal, check_database

    try:
        await check_database()
    except Exception:
        pytest.skip("PostgreSQL is not available")
    async with AsyncSessionLocal() as session:
        snapshot = await collect_snapshot(session)
    wh = AnalyticalWarehouse(":memory:")
    try:
        counts = wh.load_snapshot(snapshot)
    finally:
        wh.close()
    assert counts == {table: len(rows) for table, rows in snapshot.items()}


# --- API -------------------------------------------------------------------


@pytest.fixture
async def client(warehouse: AnalyticalWarehouse) -> AsyncIterator[httpx.AsyncClient]:
    async def no_session() -> AsyncIterator[None]:
        yield None

    app.dependency_overrides[get_warehouse] = lambda: warehouse
    app.dependency_overrides[get_session] = no_session
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
            yield http
    finally:
        app.dependency_overrides.pop(get_warehouse, None)
        app.dependency_overrides.pop(get_session, None)


ANALYST = {"X-Demo-Role": "analyst"}
ADMIN = {"X-Demo-Role": "admin"}
VIEWER = {"X-Demo-Role": "viewer"}


async def test_summary_endpoint(client: httpx.AsyncClient) -> None:
    unauthenticated = await client.get("/api/v1/warehouse/summary")
    assert unauthenticated.status_code == 401

    response = await client.get("/api/v1/warehouse/summary", headers=VIEWER)
    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] == "duckdb"
    assert payload["status"] == "ready"
    assert payload["total_rows"] == 14
    assert {t["name"] for t in payload["tables"]} >= {"warehouse_risks", "warehouse_audit"}
    assert "risk_distribution" in payload["presets"]


async def test_query_endpoint_presets_and_roles(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/warehouse/query", json={"view": "supplier_exposure"}, headers=ANALYST
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "supplier_exposure"
    assert payload["row_count"] == 3
    assert "exposure_rank" in payload["columns"]

    viewer = await client.post(
        "/api/v1/warehouse/query", json={"view": "risk_distribution"}, headers=VIEWER
    )
    assert viewer.status_code == 403

    analyst_sql = await client.post(
        "/api/v1/warehouse/query", json={"sql": "SELECT 1"}, headers=ANALYST
    )
    assert analyst_sql.status_code == 403

    both = await client.post(
        "/api/v1/warehouse/query",
        json={"view": "risk_distribution", "sql": "SELECT 1"},
        headers=ADMIN,
    )
    assert both.status_code == 422


async def test_query_endpoint_admin_sql(client: httpx.AsyncClient) -> None:
    ok = await client.post(
        "/api/v1/warehouse/query",
        json={"sql": "SELECT severity, COUNT(*) AS n FROM warehouse_risks GROUP BY 1 ORDER BY 1"},
        headers=ADMIN,
    )
    assert ok.status_code == 200
    assert ok.json()["columns"] == ["severity", "n"]

    rejected = await client.post(
        "/api/v1/warehouse/query", json={"sql": "DROP TABLE warehouse_risks"}, headers=ADMIN
    )
    assert rejected.status_code == 400


async def test_export_and_download_endpoints(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/warehouse/export", json={"table": "signals"}, headers=ANALYST
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["format"] == "parquet"
    assert payload["row_count"] == 3
    assert payload["size_bytes"] > 0

    download = await client.get(payload["download_url"], headers=ANALYST)
    assert download.status_code == 200
    assert download.content[:4] == b"PAR1"

    missing = await client.get("/api/v1/warehouse/exports/passwd", headers=ANALYST)
    assert missing.status_code == 404


def test_openapi_lists_warehouse_endpoints() -> None:
    paths = app.openapi()["paths"]
    for path in (
        "/api/v1/warehouse/summary",
        "/api/v1/warehouse/query",
        "/api/v1/warehouse/export",
    ):
        assert path in paths


def test_snapshot_timestamps_are_naive_utc() -> None:
    from app.db.warehouse import _ts

    aware = datetime(2026, 11, 1, 21, 0, tzinfo=timezone(timedelta(hours=6)))
    assert _ts(aware) == datetime(2026, 11, 1, 15, 0)
    assert _ts(None) is None

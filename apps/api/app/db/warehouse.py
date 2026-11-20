"""Embedded DuckDB analytical warehouse.

The operational store (PostgreSQL via SQLAlchemy) stays the system of record.
This module keeps a columnar snapshot of the analytics-relevant tables in an
in-process DuckDB database so OLAP queries (window functions, grouped
aggregates) and Parquet/CSV exports never load the OLTP database.

Two DuckDB connections hold the same snapshot:

* ``_conn`` is the warehouse itself. It may be file-backed and is the only
  connection allowed to touch the filesystem (Parquet/CSV export).
* ``_sandbox`` is an in-memory copy with external access disabled and its
  configuration locked. Ad-hoc SQL only ever runs here, so a query cannot read
  or write files, attach databases or install extensions.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import duckdb
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import AuditEvent, Obligation, Risk, Signal, Source, Supplier

logger = logging.getLogger(__name__)

ExportFormat = Literal["parquet", "csv"]
PresetView = Literal["risk_distribution", "audit_integrity", "supplier_exposure"]

# Warehouse table -> ordered (column, DuckDB type) pairs. Snapshot rows are
# tuples in exactly this column order.
TABLE_SCHEMAS: dict[str, tuple[tuple[str, str], ...]] = {
    "warehouse_suppliers": (
        ("supplier_id", "VARCHAR"),
        ("parent_supplier_id", "VARCHAR"),
        ("name", "VARCHAR"),
        ("country", "VARCHAR"),
        ("tier", "INTEGER"),
        ("category", "VARCHAR"),
        ("status", "VARCHAR"),
        ("risk_level", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
    ),
    "warehouse_risks": (
        ("risk_id", "VARCHAR"),
        ("title", "VARCHAR"),
        ("category", "VARCHAR"),
        ("severity", "VARCHAR"),
        ("likelihood", "VARCHAR"),
        ("exposure", "VARCHAR"),
        ("score", "DOUBLE"),
        ("priority", "VARCHAR"),
        ("status", "VARCHAR"),
        ("confidence", "DOUBLE"),
        ("verification_status", "VARCHAR"),
        ("supplier_id", "VARCHAR"),
        ("supplier_name", "VARCHAR"),
        ("supplier_tier", "INTEGER"),
        ("supplier_country", "VARCHAR"),
        ("jurisdiction", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
    ),
    "warehouse_signals": (
        ("signal_id", "VARCHAR"),
        ("source_name", "VARCHAR"),
        ("stream_key", "VARCHAR"),
        ("supplier_id", "VARCHAR"),
        ("title", "VARCHAR"),
        ("jurisdiction", "VARCHAR"),
        ("signal_type", "VARCHAR"),
        ("severity", "VARCHAR"),
        ("status", "VARCHAR"),
        ("published_at", "TIMESTAMP"),
        ("ingested_at", "TIMESTAMP"),
    ),
    "warehouse_audit": (
        ("seq", "BIGINT"),
        ("event_id", "VARCHAR"),
        ("actor_id", "VARCHAR"),
        ("actor_email", "VARCHAR"),
        ("action", "VARCHAR"),
        ("entity_type", "VARCHAR"),
        ("entity_id", "VARCHAR"),
        ("prev_hash", "VARCHAR"),
        ("hash", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
    ),
}

# Public dataset names (API) -> warehouse tables.
EXPORT_TABLES: dict[str, str] = {
    "risks": "warehouse_risks",
    "audit_events": "warehouse_audit",
    "signals": "warehouse_signals",
    "suppliers": "warehouse_suppliers",
}

PRESET_QUERIES: dict[str, str] = {
    # Risk concentration by jurisdiction x supplier tier, with each bucket's
    # share of all risks and its rank by average score.
    "risk_distribution": """
        SELECT
            COALESCE(jurisdiction, 'UNSPECIFIED') AS jurisdiction,
            COALESCE(CAST(supplier_tier AS VARCHAR), 'company') AS supplier_tier,
            COUNT(*) AS risk_count,
            COUNT(*) FILTER (WHERE priority IN ('high', 'critical')) AS high_priority_count,
            ROUND(AVG(score), 2) AS avg_score,
            ROUND(MAX(score), 2) AS max_score,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct,
            RANK() OVER (ORDER BY AVG(score) DESC) AS severity_rank
        FROM warehouse_risks
        GROUP BY ALL
        ORDER BY severity_rank, jurisdiction, supplier_tier
    """,
    # Hash-chain continuity and actor activity over the audit ledger. Each
    # event's prev_hash must equal the previous event's hash (by seq).
    "audit_integrity": """
        WITH ordered AS (
            SELECT
                *,
                LAG(hash) OVER (ORDER BY seq) AS expected_prev_hash
            FROM warehouse_audit
        )
        SELECT
            actor_email,
            COUNT(*) AS events,
            COUNT(DISTINCT action) AS distinct_actions,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct,
            COUNT(*) FILTER (
                WHERE expected_prev_hash IS NOT NULL AND prev_hash <> expected_prev_hash
            ) AS broken_links,
            MIN(created_at) AS first_event_at,
            MAX(created_at) AS last_event_at,
            ROUND(
                COUNT(*) / GREATEST(
                    date_diff('second', MIN(created_at), MAX(created_at)) / 3600.0, 1.0
                ),
                2
            ) AS events_per_hour
        FROM ordered
        GROUP BY actor_email
        ORDER BY events DESC, actor_email
    """,
    # Open-risk exposure and signal volume per supplier, densely ranked.
    "supplier_exposure": """
        WITH open_risks AS (
            SELECT supplier_id, COUNT(*) AS open_risks, SUM(score) AS total_score,
                   MAX(score) AS max_score
            FROM warehouse_risks
            WHERE status <> 'closed' AND supplier_id IS NOT NULL
            GROUP BY supplier_id
        ),
        signal_counts AS (
            SELECT supplier_id, COUNT(*) AS signal_count
            FROM warehouse_signals
            WHERE supplier_id IS NOT NULL
            GROUP BY supplier_id
        )
        SELECT
            s.supplier_id,
            s.name,
            s.country,
            s.tier,
            s.risk_level,
            COALESCE(r.open_risks, 0) AS open_risks,
            ROUND(COALESCE(r.total_score, 0), 2) AS total_score,
            ROUND(COALESCE(r.max_score, 0), 2) AS max_score,
            COALESCE(g.signal_count, 0) AS signal_count,
            DENSE_RANK() OVER (ORDER BY COALESCE(r.total_score, 0) DESC) AS exposure_rank
        FROM warehouse_suppliers s
        LEFT JOIN open_risks r USING (supplier_id)
        LEFT JOIN signal_counts g USING (supplier_id)
        ORDER BY exposure_rank, s.name
    """,
}

_SQL_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


class WarehouseQueryError(ValueError):
    """Raised for an ad-hoc query that is rejected or fails."""


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool
    execution_ms: float


@dataclass(frozen=True)
class ExportResult:
    table: str
    format: ExportFormat
    path: Path
    row_count: int
    size_bytes: int
    exported_at: datetime


Snapshot = dict[str, list[tuple[Any, ...]]]


def _id(value: Any) -> str | None:
    return None if value is None else str(value)


def _ts(value: Any) -> datetime | None:
    """Normalize to naive UTC so DuckDB TIMESTAMP columns need no tz support."""
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list | tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return str(value)


async def collect_snapshot(session: AsyncSession) -> Snapshot:
    """Read the operational tables into warehouse-shaped row tuples."""
    suppliers = (
        await session.execute(
            select(
                Supplier.id,
                Supplier.parent_supplier_id,
                Supplier.name,
                Supplier.country,
                Supplier.tier,
                Supplier.category,
                Supplier.status,
                Supplier.risk_level,
                Supplier.created_at,
            )
        )
    ).all()
    risks = (
        await session.execute(
            select(
                Risk.id,
                Risk.title,
                Risk.category,
                Risk.severity,
                Risk.likelihood,
                Risk.exposure,
                Risk.score,
                Risk.priority,
                Risk.status,
                Risk.confidence,
                Risk.verification_status,
                Risk.supplier_id,
                Supplier.name,
                Supplier.tier,
                Supplier.country,
                Obligation.jurisdiction,
                Risk.created_at,
                Risk.updated_at,
            )
            .outerjoin(Supplier, Risk.supplier_id == Supplier.id)
            .outerjoin(Obligation, Risk.obligation_id == Obligation.id)
        )
    ).all()
    signals = (
        await session.execute(
            select(
                Signal.id,
                Source.name,
                Source.stream_key,
                Signal.supplier_id,
                Signal.title,
                Signal.jurisdiction,
                Signal.signal_type,
                Signal.severity,
                Signal.status,
                Signal.published_at,
                Signal.ingested_at,
            ).join(Source, Signal.source_id == Source.id)
        )
    ).all()
    audit = (
        await session.execute(
            select(
                AuditEvent.seq,
                AuditEvent.id,
                AuditEvent.actor_id,
                AuditEvent.actor_email,
                AuditEvent.action,
                AuditEvent.entity_type,
                AuditEvent.entity_id,
                AuditEvent.prev_hash,
                AuditEvent.hash,
                AuditEvent.created_at,
            ).order_by(AuditEvent.seq)
        )
    ).all()

    return {
        "warehouse_suppliers": [
            (_id(r[0]), _id(r[1]), r[2], r[3], r[4], r[5], r[6], r[7], _ts(r[8]))
            for r in suppliers
        ],
        "warehouse_risks": [
            (
                _id(r[0]), r[1], r[2], r[3], r[4], r[5], float(r[6]), r[7], r[8],
                float(r[9]), r[10], _id(r[11]), r[12], r[13], r[14], r[15],
                _ts(r[16]), _ts(r[17]),
            )
            for r in risks
        ],
        "warehouse_signals": [
            (
                _id(r[0]), r[1], r[2], _id(r[3]), r[4], r[5], r[6], r[7], r[8],
                _ts(r[9]), _ts(r[10]),
            )
            for r in signals
        ],
        "warehouse_audit": [
            (int(r[0]), _id(r[1]), r[2], r[3], r[4], r[5], r[6], r[7], r[8], _ts(r[9]))
            for r in audit
        ],
    }


class AnalyticalWarehouse:
    def __init__(
        self,
        path: str = ":memory:",
        *,
        export_dir: str | Path = "./data/warehouse/exports",
        max_rows: int = 1000,
        query_timeout_seconds: float = 5.0,
    ) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.export_dir = Path(export_dir)
        self.max_rows = max_rows
        self.query_timeout_seconds = query_timeout_seconds
        self.last_synced_at: datetime | None = None
        self._lock = threading.RLock()
        self._conn = duckdb.connect(path)
        self._sandbox = duckdb.connect(":memory:", config={"enable_external_access": False})
        self._sandbox.execute("SET lock_configuration = true")
        self._create_tables()

    @property
    def version(self) -> str:
        return duckdb.__version__

    def close(self) -> None:
        with self._lock:
            self._conn.close()
            self._sandbox.close()

    def _create_tables(self) -> None:
        with self._lock:
            for conn in (self._conn, self._sandbox):
                for table, columns in TABLE_SCHEMAS.items():
                    cols = ", ".join(f"{name} {kind}" for name, kind in columns)
                    conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")

    def load_snapshot(self, snapshot: Snapshot) -> dict[str, int]:
        """Replace every warehouse table with the given rows, atomically per connection."""
        unknown = set(snapshot) - set(TABLE_SCHEMAS)
        if unknown:
            raise ValueError(f"Unknown warehouse tables: {sorted(unknown)}")
        with self._lock:
            for conn in (self._conn, self._sandbox):
                conn.execute("BEGIN TRANSACTION")
                try:
                    for table, columns in TABLE_SCHEMAS.items():
                        conn.execute(f"DELETE FROM {table}")  # noqa: S608
                        rows = snapshot.get(table, [])
                        if rows:
                            placeholders = ", ".join("?" for _ in columns)
                            conn.executemany(
                                f"INSERT INTO {table} VALUES ({placeholders})", rows  # noqa: S608
                            )
                    conn.execute("COMMIT")
                except Exception:
                    conn.execute("ROLLBACK")
                    raise
            self.last_synced_at = datetime.now(UTC)
            return self.table_counts()

    async def sync_from_session(self, session: AsyncSession) -> dict[str, int]:
        snapshot = await collect_snapshot(session)
        return self.load_snapshot(snapshot)

    def is_stale(self, ttl_seconds: int) -> bool:
        if self.last_synced_at is None:
            return True
        return (datetime.now(UTC) - self.last_synced_at).total_seconds() > ttl_seconds

    def table_counts(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for table in TABLE_SCHEMAS:
                row = self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
                counts[table] = int(row[0]) if row else 0
            return counts

    def _run(self, conn: duckdb.DuckDBPyConnection, sql: str) -> QueryResult:
        started = time.perf_counter()
        timer = threading.Timer(self.query_timeout_seconds, conn.interrupt)
        timer.start()
        try:
            cursor = conn.execute(sql)
            columns = [d[0] for d in cursor.description or []]
            fetched = cursor.fetchmany(self.max_rows + 1)
        except duckdb.InterruptException as exc:
            raise WarehouseQueryError(
                f"Query exceeded {self.query_timeout_seconds:g}s and was cancelled"
            ) from exc
        except duckdb.Error as exc:
            raise WarehouseQueryError(str(exc).splitlines()[0]) from exc
        finally:
            timer.cancel()
        truncated = len(fetched) > self.max_rows
        fetched = fetched[: self.max_rows]
        rows = [
            {column: _json_value(value) for column, value in zip(columns, row, strict=True)}
            for row in fetched
        ]
        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
            execution_ms=round((time.perf_counter() - started) * 1000, 3),
        )

    def run_preset(self, view: PresetView | str) -> QueryResult:
        sql = PRESET_QUERIES.get(view)
        if sql is None:
            raise WarehouseQueryError(f"Unknown preset view: {view}")
        with self._lock:
            return self._run(self._sandbox, sql)

    def query_risk_distribution(self) -> QueryResult:
        return self.run_preset("risk_distribution")

    def query_audit_integrity_metrics(self) -> QueryResult:
        return self.run_preset("audit_integrity")

    def query_supplier_exposure(self) -> QueryResult:
        return self.run_preset("supplier_exposure")

    def execute_query(self, sql: str) -> QueryResult:
        """Run one read-only SELECT against the sandboxed snapshot."""
        sql = sql.strip().rstrip(";").strip()
        if not sql:
            raise WarehouseQueryError("Query is empty")
        with self._lock:
            try:
                statements = self._sandbox.extract_statements(sql)
            except duckdb.Error as exc:
                raise WarehouseQueryError(str(exc).splitlines()[0]) from exc
            if len(statements) != 1:
                raise WarehouseQueryError("Exactly one SQL statement is allowed")
            if statements[0].type != duckdb.StatementType.SELECT:
                raise WarehouseQueryError("Only read-only SELECT queries are allowed")
            return self._run(self._sandbox, sql)

    def export_table(
        self,
        dataset: str,
        fmt: ExportFormat = "parquet",
        target_path: Path | None = None,
    ) -> ExportResult:
        table = EXPORT_TABLES.get(dataset)
        if table is None:
            raise WarehouseQueryError(f"Unknown dataset: {dataset}")
        if fmt not in ("parquet", "csv"):
            raise WarehouseQueryError(f"Unsupported export format: {fmt}")
        assert _SQL_IDENTIFIER.match(table)
        exported_at = datetime.now(UTC)
        if target_path is None:
            stamp = exported_at.strftime("%Y%m%dT%H%M%S%fZ")
            target_path = self.export_dir / f"{dataset}_{stamp}.{fmt}"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        literal = str(target_path).replace("'", "''")
        options = (
            "FORMAT PARQUET, COMPRESSION ZSTD" if fmt == "parquet" else "FORMAT CSV, HEADER"
        )
        with self._lock:
            self._conn.execute(f"COPY {table} TO '{literal}' ({options})")
            row = self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
        return ExportResult(
            table=dataset,
            format=fmt,
            path=target_path,
            row_count=int(row[0]) if row else 0,
            size_bytes=target_path.stat().st_size,
            exported_at=exported_at,
        )

    def export_parquet(
        self, dataset: str, target_path: Path | None = None
    ) -> tuple[Path, int, int]:
        result = self.export_table(dataset, "parquet", target_path)
        return result.path, result.row_count, result.size_bytes


@lru_cache
def get_warehouse() -> AnalyticalWarehouse:
    settings = get_settings()
    return AnalyticalWarehouse(
        settings.warehouse_path,
        export_dir=settings.warehouse_export_dir,
        max_rows=settings.warehouse_max_rows,
        query_timeout_seconds=settings.warehouse_query_timeout_seconds,
    )


def close_warehouse() -> None:
    if get_warehouse.cache_info().currsize:
        get_warehouse().close()
        get_warehouse.cache_clear()

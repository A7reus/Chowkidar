"""live source connectors

Revision ID: 9c1e4f2a7b10
Revises: 82eceac00bcf
Create Date: 2026-10-26 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9c1e4f2a7b10"
down_revision: str | None = "82eceac00bcf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


FEDERAL_REGISTER_ID = "00000000-0000-0000-0000-000000000105"


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column(
            "connector_key",
            sa.String(length=64),
            server_default="fixture",
            nullable=False,
        ),
    )
    op.add_column(
        "sources",
        sa.Column(
            "connector_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "sources",
        sa.Column("last_sync_mode", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "sources",
        sa.Column(
            "last_signal_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )

    # Existing seeded sources stay fixture-backed unless a connector is
    # explicitly available. GDELT already has a public, key-free endpoint.
    op.execute(
        sa.text(
            """
            UPDATE sources
            SET connector_key = 'gdelt',
                connector_config = '{"query": "\\"forced labour\\" OR \\"supply chain\\" OR \\"export controls\\"", "timespan": "7d", "max_records": 10}'::jsonb
            WHERE stream_key = 'gdelt'
            """
        )
    )

    # Add a second key-free live stream. The seed fixture mirrors this row for
    # fresh local databases; the migration handles the already-seeded hosted DB.
    op.execute(
        sa.text(
            """
            INSERT INTO sources (
                id, name, stream_key, source_type, jurisdiction, url, cadence,
                status, connector_key, connector_config, last_sync_mode,
                last_signal_count, last_synced_at, last_error,
                created_at, updated_at
            )
            SELECT
                CAST(:source_id AS uuid),
                :source_name,
                'us_federal_register',
                'regulatory',
                'US',
                'https://www.federalregister.gov/api/v1/documents.json',
                'daily',
                'fixture',
                'federal_register',
                CAST(:connector_config AS jsonb),
                'fixture',
                0,
                NULL,
                NULL,
                now(),
                now()
            WHERE NOT EXISTS (
                SELECT 1 FROM sources WHERE stream_key = 'us_federal_register'
            )
            """
        ).bindparams(
            source_id=FEDERAL_REGISTER_ID,
            source_name="US Federal Register — Trade & supply-chain rules",
            connector_config=(
                '{"term": "export controls", "per_page": 20, '
                '"document_type": "RULE"}'
            ),
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM sources WHERE stream_key = 'us_federal_register'")
    )
    op.drop_column("sources", "last_signal_count")
    op.drop_column("sources", "last_sync_mode")
    op.drop_column("sources", "connector_config")
    op.drop_column("sources", "connector_key")

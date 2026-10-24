from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="Bangladesh")
    sector: Mapped[str] = mapped_column(String(120), nullable=False, default="RMG")
    profile: Mapped[dict[str, Any]] = mapped_column("profile", JSONB, default=dict)

    suppliers: Mapped[list[Supplier]] = relationship(back_populates="company")
    buyers: Mapped[list[Buyer]] = relationship(back_populates="company")
    policies: Mapped[list[Policy]] = relationship(back_populates="company")
    risks: Mapped[list[Risk]] = relationship(back_populates="company")
    documents: Mapped[list[Document]] = relationship(back_populates="company")


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="viewer")
    supabase_user_id: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, default="apparel")
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile: Mapped[dict[str, Any]] = mapped_column("profile", JSONB, default=dict)

    company: Mapped[Company] = relationship(back_populates="suppliers")
    documents: Mapped[list[Document]] = relationship(back_populates="supplier")
    risks: Mapped[list[Risk]] = relationship(back_populates="supplier")
    signals: Mapped[list[Signal]] = relationship(back_populates="supplier")


class Buyer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "buyers"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    requirements_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)

    company: Mapped[Company] = relationship(back_populates="buyers")


class Policy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "policies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(32), default="policy", nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="1.0", nullable=False)
    owner: Mapped[str] = mapped_column(String(160), default="Compliance", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)

    company: Mapped[Company] = relationship(back_populates="policies")


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stream_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), default="regulatory", nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(32), default="GLOBAL", nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    cadence: Mapped[str] = mapped_column(String(64), default="daily", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="healthy", nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    signals: Mapped[list[Signal]] = relationship(back_populates="source")


class Signal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "signals"

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(32), default="GLOBAL", nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), default="regulatory", nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    source: Mapped[Source] = relationship(back_populates="signals")
    supplier: Mapped[Supplier | None] = relationship(back_populates="signals")
    obligations: Mapped[list[Obligation]] = relationship(back_populates="signal")
    chunks: Mapped[list[EvidenceChunk]] = relationship(back_populates="signal")

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_signal_source_external"),
        Index("ix_signals_ingested_at", "ingested_at"),
    )


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(64), default="policy", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="text/plain", nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    parsed_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="parsed", nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    company: Mapped[Company] = relationship(back_populates="documents")
    supplier: Mapped[Supplier | None] = relationship(back_populates="documents")
    chunks: Mapped[list[EvidenceChunk]] = relationship(back_populates="document")


class EvidenceChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evidence_chunks"

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("signals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citation_label: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    citation_url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    section_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    document: Mapped[Document | None] = relationship(back_populates="chunks")
    signal: Mapped[Signal | None] = relationship(back_populates="chunks")
    risk_links: Mapped[list[RiskEvidence]] = relationship(back_populates="evidence_chunk")

    __table_args__ = (
        Index("ix_evidence_chunks_search_vector", "search_vector", postgresql_using="gin"),
        Index(
            "ix_evidence_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class Obligation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "obligations"

    signal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(32), default="GLOBAL", nullable=False)
    obligation_type: Mapped[str] = mapped_column(String(64), default="due_diligence", nullable=False)
    applies_to: Mapped[str] = mapped_column(String(255), default="company", nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    citation_url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    citation_quote: Mapped[str] = mapped_column(Text, default="", nullable=False)
    section_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    signal: Mapped[Signal] = relationship(back_populates="obligations")
    source: Mapped[Source] = relationship()
    risks: Mapped[list[Risk]] = relationship(back_populates="obligation")


class Risk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risks"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    obligation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("obligations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="regulatory", nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    likelihood: Mapped[str] = mapped_column(String(32), default="possible", nullable=False)
    exposure: Mapped[str] = mapped_column(String(32), default="moderate", nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(32), default="needs_review", nullable=False
    )
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    company: Mapped[Company] = relationship(back_populates="risks")
    supplier: Mapped[Supplier | None] = relationship(back_populates="risks")
    obligation: Mapped[Obligation | None] = relationship(back_populates="risks")
    evidence: Mapped[list[RiskEvidence]] = relationship(
        back_populates="risk", cascade="all, delete-orphan"
    )
    actions: Mapped[list[RemediationAction]] = relationship(
        back_populates="risk", cascade="all, delete-orphan"
    )
    approvals: Mapped[list[Approval]] = relationship(
        back_populates="risk", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_risks_priority_score", "priority", "score"),
    )


class RiskEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_evidence"

    risk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidence_chunks.id", ondelete="SET NULL"), nullable=True
    )
    quote: Mapped[str] = mapped_column(Text, default="", nullable=False)
    citation_url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    citation_label: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    supports: Mapped[str] = mapped_column(String(32), default="supports", nullable=False)

    risk: Mapped[Risk] = relationship(back_populates="evidence")
    evidence_chunk: Mapped[EvidenceChunk | None] = relationship(back_populates="risk_links")


class RemediationAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "remediation_actions"

    risk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    owner_role: Mapped[str] = mapped_column(String(64), default="analyst", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    automated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    risk: Mapped[Risk] = relationship(back_populates="actions")
    approvals: Mapped[list[Approval]] = relationship(back_populates="action")


class Approval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "approvals"

    risk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("remediation_actions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_to: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    risk: Mapped[Risk] = relationship(back_populates="approvals")
    action: Mapped[RemediationAction | None] = relationship(back_populates="approvals")

    __table_args__ = (Index("ix_approvals_status", "status"),)


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_events"

    seq: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True, nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_audit_events_created_at", "created_at"),)


class AgentRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_runs"

    workflow: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trace_id: Mapped[str] = mapped_column(String(80), default="", nullable=False)


class ReportRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "report_runs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    storage_backend: Mapped[str] = mapped_column(
        String(32), default="local", server_default="local", nullable=False
    )
    content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    content_sha256: Mapped[str] = mapped_column(
        String(64), default="", server_default="", nullable=False
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvalRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "eval_runs"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

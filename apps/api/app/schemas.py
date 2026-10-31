from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RoleLiteral = Literal["admin", "analyst", "approver", "viewer"]
PriorityLiteral = Literal["low", "medium", "high", "critical"]
RiskStatusLiteral = Literal["open", "in_review", "mitigating", "closed"]
VerificationLiteral = Literal["verified", "needs_review", "insufficient_evidence"]
ActionStatusLiteral = Literal[
    "draft", "pending_approval", "approved", "in_progress", "done", "rejected"
]
ApprovalStatusLiteral = Literal["pending", "approved", "rejected"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(ORMModel):
    id: str
    email: str
    name: str
    role: RoleLiteral
    is_demo: bool = False


class DemoLoginRequest(BaseModel):
    role: RoleLiteral = "approver"


class PasswordLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=512)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=4096)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None
    user: UserOut


class AuthConfigOut(BaseModel):
    auth_mode: str
    demo_mode: bool
    password_auth: bool
    demo_users: list[UserOut] = Field(default_factory=list)


class HealthOut(BaseModel):
    status: str
    app: str
    version: str
    database: str
    auth_mode: str
    demo_mode: bool
    llm_mode: str
    llm_live_ready: bool = False
    data_mode: str
    live_connectors: list[str] = Field(default_factory=list)
    live_connectors_enabled: bool = False
    scheduler_enabled: bool = False
    scheduler_running: bool = False
    scheduler_next_run_at: str | None = None
    revision: str | None = None
    timestamp: datetime


class SourceOut(ORMModel):
    id: uuid.UUID
    name: str
    stream_key: str
    source_type: str
    jurisdiction: str
    url: str
    cadence: str
    status: str
    connector_key: str = "fixture"
    last_sync_mode: str | None = None
    last_signal_count: int = 0
    last_synced_at: datetime | None
    last_error: str | None


class SourceSyncResponse(BaseModel):
    source: SourceOut
    signals_created: int
    message: str
    mode: str = "fixture"
    connector: str = "fixture"


class SignalOut(ORMModel):
    id: uuid.UUID
    source_id: uuid.UUID
    supplier_id: uuid.UUID | None
    external_id: str
    title: str
    summary: str
    url: str
    jurisdiction: str
    signal_type: str
    severity: str
    published_at: datetime
    ingested_at: datetime
    status: str
    source_name: str | None = None
    supplier_name: str | None = None


class SignalDetail(SignalOut):
    raw_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SignalListResponse(BaseModel):
    items: list[SignalOut]
    total: int


class ObligationOut(ORMModel):
    id: uuid.UUID
    title: str
    description: str
    jurisdiction: str
    obligation_type: str
    applies_to: str
    effective_date: date | None
    confidence: float
    citation_url: str
    citation_quote: str
    section_path: str
    status: str


class SupplierOut(ORMModel):
    id: uuid.UUID
    name: str
    country: str
    tier: int
    category: str
    status: str
    risk_level: str


class EvidenceOut(ORMModel):
    id: uuid.UUID
    quote: str
    citation_url: str
    citation_label: str
    confidence: float
    supports: str


class ActionOut(ORMModel):
    id: uuid.UUID
    risk_id: uuid.UUID
    title: str
    description: str
    owner_role: str
    due_date: date | None
    priority: str
    status: ActionStatusLiteral
    automated: bool


class ApprovalOut(ORMModel):
    id: uuid.UUID
    risk_id: uuid.UUID
    action_id: uuid.UUID | None
    requested_by: str
    assigned_to: str
    status: ApprovalStatusLiteral
    decision: str | None
    rationale: str | None
    decided_at: datetime | None
    created_at: datetime
    risk_title: str | None = None
    action_title: str | None = None


class ScoreBreakdown(BaseModel):
    severity: str
    likelihood: str
    exposure: str
    severity_weight: float
    likelihood_weight: float
    exposure_weight: float
    severity_value: int
    likelihood_value: int
    exposure_value: int
    score: float
    priority: str
    formula: str


class RiskListItem(ORMModel):
    id: uuid.UUID
    title: str
    description: str
    category: str
    severity: str
    likelihood: str
    exposure: str
    score: float
    priority: str
    status: str
    confidence: float
    verification_status: VerificationLiteral
    supplier_name: str | None = None
    obligation_title: str | None = None
    evidence_count: int = 0
    action_count: int = 0
    created_at: datetime
    updated_at: datetime


class RiskDetail(RiskListItem):
    rationale: str
    score_breakdown: dict[str, Any]
    supplier: SupplierOut | None = None
    obligation: ObligationOut | None = None
    evidence: list[EvidenceOut] = Field(default_factory=list)
    actions: list[ActionOut] = Field(default_factory=list)
    approvals: list[ApprovalOut] = Field(default_factory=list)


class RiskListResponse(BaseModel):
    items: list[RiskListItem]
    total: int
    counts_by_priority: dict[str, int]


class ActionCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    description: str = ""
    owner_role: str = "analyst"
    due_date: date | None = None
    priority: PriorityLiteral = "medium"


class ActionUpdateRequest(BaseModel):
    status: ActionStatusLiteral | None = None
    owner_role: str | None = None
    due_date: date | None = None
    description: str | None = None


class RiskUpdateRequest(BaseModel):
    status: RiskStatusLiteral


class ApprovalCreateRequest(BaseModel):
    action_id: uuid.UUID
    assigned_to: str = "approver@chowkidar.demo"
    note: str = Field(default="", max_length=2000)


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    rationale: str = Field(min_length=5, max_length=3000)


class ApprovalListResponse(BaseModel):
    items: list[ApprovalOut]
    total: int


class TrendPoint(BaseModel):
    date: str
    open: int
    high: int


class TopRisk(BaseModel):
    id: uuid.UUID
    title: str
    priority: str
    score: float
    supplier_name: str | None = None
    status: str


class SourceHealth(BaseModel):
    id: uuid.UUID
    name: str
    stream_key: str
    jurisdiction: str
    status: str
    connector_key: str = "fixture"
    last_sync_mode: str | None = None
    last_synced_at: datetime | None
    signal_count: int


class DashboardSummary(BaseModel):
    company_name: str
    total_risks: int
    open_risks: int
    critical_risks: int
    high_risks: int
    pending_approvals: int
    signals_last_7_days: int
    verified_evidence_rate: float
    trend: list[TrendPoint]
    top_risks: list[TopRisk]
    source_health: list[SourceHealth]
    recent_signals: list[SignalOut]


class ReportCreateRequest(BaseModel):
    format: Literal["pdf", "json", "markdown"] = "json"


class ReportOut(ORMModel):
    id: uuid.UUID
    format: str
    status: str
    storage_backend: str
    content_sha256: str
    size_bytes: int
    summary: dict[str, Any]
    generated_at: datetime


class ReportListResponse(BaseModel):
    items: list[ReportOut]
    total: int


class ReportDownloadResponse(BaseModel):
    report: ReportOut
    download_url: str
    content_type: str


class AuditEventOut(ORMModel):
    id: uuid.UUID
    actor_id: str
    actor_email: str
    action: str
    entity_type: str
    entity_id: str
    payload: dict[str, Any]
    prev_hash: str
    hash: str
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEventOut]
    total: int


class AuditVerifyOut(BaseModel):
    valid: bool
    events: int
    head: str | None = None
    broken_at: int | None = None
    reason: str | None = None


class GraphNode(BaseModel):
    id: str
    label: str
    kind: Literal["company", "supplier", "obligation", "risk", "policy"]
    priority: str | None = None
    detail: str | None = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    content: str
    citation_label: str
    citation_url: str
    section_path: str
    score: float
    signal_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    mode: str


class PipelineRunRequest(BaseModel):
    source_ids: list[uuid.UUID] | None = None
    mode: Literal["mock", "live"] = "mock"


class AgentRunOut(ORMModel):
    id: uuid.UUID
    workflow: str
    status: str
    input: dict[str, Any]
    output: dict[str, Any]
    error: str | None
    started_at: datetime
    finished_at: datetime | None
    trace_id: str


class PipelineRunResponse(BaseModel):
    run: AgentRunOut
    message: str
    counts: dict[str, int]
    created_risk_ids: list[uuid.UUID]
    errors: list[str]


class LineageNode(BaseModel):
    id: str
    kind: Literal[
        "source",
        "signal",
        "obligation",
        "risk",
        "evidence",
        "action",
        "approval",
        "report",
    ]
    label: str
    status: str | None = None
    href: str | None = None
    detail: str | None = None
    occurred_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskLineageOut(BaseModel):
    risk_id: uuid.UUID
    trace_id: str | None = None
    nodes: list[LineageNode] = Field(default_factory=list)
    reports: list[ReportOut] = Field(default_factory=list)
    audit_events: list[AuditEventOut] = Field(default_factory=list)
    agent_run: AgentRunOut | None = None


class EvalCaseResult(BaseModel):
    case_id: str
    passed: bool
    citation_coverage: float
    verifier_pass: bool
    no_legal_advice: bool
    notes: list[str]


class EvalSummary(BaseModel):
    name: str
    total_cases: int
    passed_cases: int
    extraction_accuracy: float
    citation_coverage: float
    verifier_pass_rate: float
    no_legal_advice_rate: float
    priority_agreement: float
    results: list[EvalCaseResult]
    generated_at: datetime


class MessageResponse(BaseModel):
    message: str

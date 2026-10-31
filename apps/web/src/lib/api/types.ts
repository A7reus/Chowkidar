import type { components } from "./schema";

type Schema = components["schemas"];

export type User = Schema["UserOut"];
export type Role = User["role"];
export type TokenResponse = Schema["TokenResponse"];
export type AuthConfig = Schema["AuthConfigOut"];
export type PasswordLoginRequest = Schema["PasswordLoginRequest"];
export type RefreshTokenRequest = Schema["RefreshTokenRequest"];
export type DashboardSummary = Schema["DashboardSummary"];
export type TopRisk = Schema["TopRisk"];
export type SourceHealth = Schema["SourceHealth"];
export type Source = Schema["SourceOut"];
export type SourceSyncResponse = Schema["SourceSyncResponse"];
export type Signal = Schema["SignalOut"];
export type SignalDetail = Schema["SignalDetail"];
export type SignalListResponse = Schema["SignalListResponse"];
export type Supplier = Schema["SupplierOut"];
export type RiskListItem = Schema["RiskListItem"];
export type RiskListResponse = Schema["RiskListResponse"];
export type RiskDetail = Schema["RiskDetail"];
export type RiskLineage = Schema["RiskLineageOut"];
export type LineageNode = Schema["LineageNode"];
export type Action = Schema["ActionOut"];
export type Approval = Schema["ApprovalOut"];
export type ApprovalListResponse = Schema["ApprovalListResponse"];
export type Evidence = Schema["EvidenceOut"];
export type Obligation = Schema["ObligationOut"];
export type AuditEvent = Schema["AuditEventOut"];
export type AuditListResponse = Schema["AuditListResponse"];
export type AuditVerify = Schema["AuditVerifyOut"];
export type Report = Schema["ReportOut"];
export type ReportListResponse = Schema["ReportListResponse"];
export type GraphNode = Schema["GraphNode"];
export type GraphEdge = Schema["GraphEdge"];
export type GraphData = Schema["GraphOut"];
export type EvalSummary = Schema["EvalSummary"];
export type EvalCaseResult = Schema["EvalCaseResult"];
export type PipelineRunResponse = Schema["PipelineRunResponse"];
export type AgentRun = Schema["AgentRunOut"];
export type SearchResponse = Schema["SearchResponse"];
export type SearchResult = Schema["SearchResult"];
export type Health = Schema["HealthOut"];

export type RiskPriority = "critical" | "high" | "medium" | "low";
export type RiskStatus = "open" | "in_review" | "mitigating" | "closed";
export type VerificationStatus = "verified" | "needs_review" | "insufficient_evidence";
export type ReportFormat = "pdf" | "json" | "markdown";

export interface WorkspaceMeta {
  app: string;
  tagline: string;
  version: string;
  demo: boolean;
  company: {
    name: string;
    country: string;
    sector: string;
    location: string;
    note: string;
  };
  buyers: Array<{ name: string; country: string; market: string }>;
  streams: Array<{
    key: string;
    name: string;
    role: string;
    jurisdiction: string;
    connector: string;
    mode: string;
  }>;
  capabilities: string[];
  disclaimer: string;
  llm_mode: string;
  llm_live_ready?: boolean;
  embedding_mode: string;
  auth_mode: string;
  data_mode?: string;
  live_connectors?: string[];
  live_connectors_enabled?: boolean;
  scheduler_enabled?: boolean;
  storage_backend?: string;
  roles: string[];
}

export interface RiskFilters {
  priority?: string;
  status?: string;
  verification_status?: string;
  supplier_id?: string;
  category?: string;
  q?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}

export interface SignalFilters {
  source_id?: string;
  jurisdiction?: string;
  severity?: string;
  signal_type?: string;
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface AuditFilters {
  action?: string;
  entity_type?: string;
  actor_email?: string;
  limit?: number;
  offset?: number;
}

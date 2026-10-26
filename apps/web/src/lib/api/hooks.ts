"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiDownload, apiFetch, ApiError } from "@/lib/api/client";
import type {
  Action,
  AgentRun,
  Approval,
  ApprovalListResponse,
  AuditFilters,
  AuditListResponse,
  AuditVerify,
  AuthConfig,
  DashboardSummary,
  EvalSummary,
  GraphData,
  Health,
  PipelineRunResponse,
  Report,
  ReportFormat,
  ReportListResponse,
  RiskDetail,
  RiskFilters,
  RiskListResponse,
  RiskStatus,
  SearchResponse,
  SignalDetail,
  SignalFilters,
  SignalListResponse,
  Source,
  SourceHealth,
  SourceSyncResponse,
  Supplier,
  WorkspaceMeta,
} from "@/lib/api/types";
import { downloadBlob } from "@/lib/utils";

const retry = (failureCount: number, error: unknown) => {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false;
  return failureCount < 1;
};

const queryOptions = {
  staleTime: 30_000,
  retry,
  refetchOnWindowFocus: false,
} as const;

export const queryKeys = {
  authConfig: ["auth", "config"] as const,
  meta: ["meta"] as const,
  health: ["health"] as const,
  dashboard: ["dashboard"] as const,
  sources: ["sources"] as const,
  signals: (filters: SignalFilters) => ["signals", filters] as const,
  signal: (id: string) => ["signal", id] as const,
  suppliers: ["suppliers"] as const,
  risks: (filters: RiskFilters) => ["risks", filters] as const,
  risk: (id: string) => ["risk", id] as const,
  approvals: (status: string) => ["approvals", status] as const,
  audit: (filters: AuditFilters) => ["audit", filters] as const,
  auditVerify: ["audit", "verify"] as const,
  graph: ["graph"] as const,
  reports: ["reports"] as const,
  evals: ["evals"] as const,
  search: (q: string) => ["search", q] as const,
  pipelineRuns: ["pipeline", "runs"] as const,
};

export function useAuthConfig() {
  return useQuery({
    queryKey: queryKeys.authConfig,
    queryFn: () => apiFetch<AuthConfig>("/api/v1/auth/config"),
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function useMeta() {
  return useQuery({
    queryKey: queryKeys.meta,
    queryFn: () => apiFetch<WorkspaceMeta>("/api/v1/meta"),
    staleTime: 5 * 60_000,
    retry,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiFetch<Health>("/healthz"),
    refetchInterval: 60_000,
    retry,
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: () => apiFetch<DashboardSummary>("/api/v1/dashboard/summary"),
    ...queryOptions,
  });
}

export function useSources() {
  return useQuery({
    queryKey: queryKeys.sources,
    queryFn: () => apiFetch<Source[]>("/api/v1/sources"),
    ...queryOptions,
  });
}

export function useSyncSource() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (sourceId: string) =>
      apiFetch<SourceSyncResponse>(`/api/v1/sources/${sourceId}/sync`, {
        method: "POST",
      }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.sources });
      void client.invalidateQueries({ queryKey: queryKeys.dashboard });
      void client.invalidateQueries({ queryKey: ["signals"] });
      void client.invalidateQueries({ queryKey: queryKeys.auditVerify });
      void client.invalidateQueries({ queryKey: ["audit"] });
    },
  });
}

export function useSignals(filters: SignalFilters) {
  return useQuery({
    queryKey: queryKeys.signals(filters),
    queryFn: () =>
      apiFetch<SignalListResponse>("/api/v1/signals", {
        params: {
          source_id: filters.source_id,
          jurisdiction: filters.jurisdiction,
          severity: filters.severity,
          signal_type: filters.signal_type,
          status: filters.status,
          q: filters.q,
          limit: filters.limit ?? 50,
          offset: filters.offset ?? 0,
        },
      }),
    ...queryOptions,
  });
}

export function useSignal(id: string | null) {
  return useQuery({
    queryKey: queryKeys.signal(id ?? ""),
    queryFn: () => apiFetch<SignalDetail>(`/api/v1/signals/${id}`),
    enabled: Boolean(id),
    ...queryOptions,
  });
}

export function useSuppliers() {
  return useQuery({
    queryKey: queryKeys.suppliers,
    queryFn: () => apiFetch<Supplier[]>("/api/v1/suppliers"),
    staleTime: 5 * 60_000,
    retry,
  });
}

export function useRisks(filters: RiskFilters) {
  return useQuery({
    queryKey: queryKeys.risks(filters),
    queryFn: () =>
      apiFetch<RiskListResponse>("/api/v1/risks", {
        params: {
          priority: filters.priority,
          status: filters.status,
          verification_status: filters.verification_status,
          supplier_id: filters.supplier_id,
          category: filters.category,
          q: filters.q,
          sort: filters.sort ?? "score",
          limit: filters.limit ?? 50,
          offset: filters.offset ?? 0,
        },
      }),
    ...queryOptions,
  });
}

export function useRisk(id: string) {
  return useQuery({
    queryKey: queryKeys.risk(id),
    queryFn: () => apiFetch<RiskDetail>(`/api/v1/risks/${id}`),
    enabled: Boolean(id),
    ...queryOptions,
  });
}

function invalidateRiskViews(client: ReturnType<typeof useQueryClient>, riskId?: string) {
  void client.invalidateQueries({ queryKey: ["risks"] });
  void client.invalidateQueries({ queryKey: queryKeys.dashboard });
  if (riskId) void client.invalidateQueries({ queryKey: queryKeys.risk(riskId) });
  void client.invalidateQueries({ queryKey: queryKeys.approvals("pending") });
  void client.invalidateQueries({ queryKey: ["approvals"] });
  void client.invalidateQueries({ queryKey: ["audit"] });
  void client.invalidateQueries({ queryKey: queryKeys.auditVerify });
}

export function useUpdateRiskStatus(riskId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (status: RiskStatus) =>
      apiFetch<RiskDetail>(`/api/v1/risks/${riskId}`, {
        method: "PATCH",
        body: { status },
      }),
    onSuccess: () => invalidateRiskViews(client, riskId),
  });
}

export function useCreateAction(riskId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      title: string;
      description: string;
      owner_role: string;
      due_date?: string | null;
      priority: string;
    }) =>
      apiFetch<Action>(`/api/v1/risks/${riskId}/actions`, {
        method: "POST",
        body,
      }),
    onSuccess: () => invalidateRiskViews(client, riskId),
  });
}

export function useUpdateAction(riskId?: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      actionId: string;
      body: {
        status?:
          | "draft"
          | "pending_approval"
          | "approved"
          | "in_progress"
          | "done"
          | "rejected";
        owner_role?: string;
        due_date?: string | null;
        description?: string;
      };
    }) =>
      apiFetch<Action>(`/api/v1/actions/${input.actionId}`, {
        method: "PATCH",
        body: input.body,
      }),
    onSuccess: () => invalidateRiskViews(client, riskId),
  });
}

export function useRequestApproval(riskId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { actionId: string; note?: string }) =>
      apiFetch<Approval>(`/api/v1/risks/${riskId}/approvals`, {
        method: "POST",
        body: {
          action_id: input.actionId,
          assigned_to: "approver@chowkidar.demo",
          note: input.note ?? "Requested from the risk detail view.",
        },
      }),
    onSuccess: () => invalidateRiskViews(client, riskId),
  });
}

export function useApprovals(status = "pending") {
  return useQuery({
    queryKey: queryKeys.approvals(status),
    queryFn: () =>
      apiFetch<ApprovalListResponse>("/api/v1/approvals", {
        params: { status, limit: 100 },
      }),
    ...queryOptions,
  });
}

export function usePendingApprovalCount(enabled = true) {
  return useQuery({
    queryKey: ["approvals", "pending-count"],
    queryFn: () => apiFetch<{ count: number }>("/api/v1/approvals/pending-count"),
    enabled,
    staleTime: 30_000,
    retry,
    refetchOnWindowFocus: false,
  });
}

export function useDecideApproval() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      approvalId: string;
      riskId: string;
      decision: "approve" | "reject";
      rationale: string;
    }) =>
      apiFetch<Approval>(`/api/v1/approvals/${input.approvalId}/decision`, {
        method: "POST",
        body: { decision: input.decision, rationale: input.rationale },
      }),
    onSuccess: (_data, variables) => invalidateRiskViews(client, variables.riskId),
  });
}

export function useAudit(filters: AuditFilters, enabled = true) {
  return useQuery({
    queryKey: queryKeys.audit(filters),
    queryFn: () =>
      apiFetch<AuditListResponse>("/api/v1/audit", {
        params: {
          action: filters.action,
          entity_type: filters.entity_type,
          actor_email: filters.actor_email,
          limit: filters.limit ?? 100,
          offset: filters.offset ?? 0,
        },
      }),
    enabled,
    ...queryOptions,
  });
}

export function useAuditVerify(enabled = true) {
  return useQuery({
    queryKey: queryKeys.auditVerify,
    queryFn: () => apiFetch<AuditVerify>("/api/v1/audit/verify"),
    enabled,
    ...queryOptions,
  });
}

export function useGraph() {
  return useQuery({
    queryKey: queryKeys.graph,
    queryFn: () => apiFetch<GraphData>("/api/v1/graph"),
    ...queryOptions,
  });
}

export function useReports() {
  return useQuery({
    queryKey: queryKeys.reports,
    queryFn: () => apiFetch<ReportListResponse>("/api/v1/reports"),
    ...queryOptions,
  });
}

export function useGenerateReport() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (format: ReportFormat) =>
      apiFetch<Report>("/api/v1/reports", { method: "POST", body: { format } }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.reports });
      void client.invalidateQueries({ queryKey: ["audit"] });
      void client.invalidateQueries({ queryKey: queryKeys.auditVerify });
    },
  });
}

export async function downloadReportFile(report: Report) {
  const fallback = `chowkidar-audit-${report.id}.${report.format === "markdown" ? "md" : report.format}`;
  const file = await apiDownload(`/api/v1/reports/${report.id}/file`, fallback);
  downloadBlob(file.blob, file.filename);
}

export function useEvals(enabled = true) {
  return useQuery({
    queryKey: queryKeys.evals,
    queryFn: () => apiFetch<EvalSummary>("/api/v1/evals/summary"),
    enabled,
    staleTime: 60_000,
    retry,
    refetchOnWindowFocus: false,
  });
}

export function useRunEvals() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<EvalSummary>("/api/v1/evals/run", { method: "POST" }),
    onSuccess: (data) => {
      client.setQueryData(queryKeys.evals, data);
    },
  });
}

export function useSearch(q: string) {
  return useQuery({
    queryKey: queryKeys.search(q),
    queryFn: () =>
      apiFetch<SearchResponse>("/api/v1/search", {
        params: { q, limit: 10 },
      }),
    enabled: q.trim().length >= 2,
    staleTime: 60_000,
    retry,
    refetchOnWindowFocus: false,
  });
}

export function usePipelineRuns(enabled = true) {
  return useQuery({
    queryKey: queryKeys.pipelineRuns,
    queryFn: () => apiFetch<AgentRun[]>("/api/v1/pipeline/runs"),
    enabled,
    ...queryOptions,
  });
}

export function useRunPipeline() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { mode: "mock" | "live"; source_ids?: string[] }) =>
      apiFetch<PipelineRunResponse>("/api/v1/pipeline/run", {
        method: "POST",
        body: { mode: input.mode, source_ids: input.source_ids ?? null },
      }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.dashboard });
      void client.invalidateQueries({ queryKey: ["risks"] });
      void client.invalidateQueries({ queryKey: queryKeys.approvals("pending") });
      void client.invalidateQueries({ queryKey: ["approvals"] });
      void client.invalidateQueries({ queryKey: queryKeys.pipelineRuns });
      void client.invalidateQueries({ queryKey: ["audit"] });
      void client.invalidateQueries({ queryKey: queryKeys.auditVerify });
      void client.invalidateQueries({ queryKey: queryKeys.graph });
    },
  });
}

export function useSourceHealth(): SourceHealth[] {
  const dashboard = useDashboard();
  return dashboard.data?.source_health ?? [];
}

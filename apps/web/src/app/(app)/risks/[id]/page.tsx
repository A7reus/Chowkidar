"use client";

import {
  AlertTriangle,
  ArrowUpRight,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  CircleDollarSign,
  Clock3,
  FileCheck2,
  FileSearch,
  Fingerprint,
  Landmark,
  ListChecks,
  Lock,
  Plus,
  Scale,
  ShieldCheck,
  Sparkles,
  UserRound,
  Wrench,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { ApprovalDecisionDialog } from "@/components/approvals/decision-dialog";
import {
  ApprovalStatusIcon,
  PriorityBadge,
  StatusBadge,
  VerificationBadge,
} from "@/components/common/badges";
import { JsonBlock } from "@/components/common/copy";
import { PageHeader } from "@/components/common/page-header";
import { ScoreRing } from "@/components/common/score-ring";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/common/states";
import { AddActionDialog } from "@/components/risks/add-action-dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useRequestApproval,
  useRisk,
  useUpdateRiskStatus,
} from "@/lib/api/hooks";
import type { Action, Approval, Evidence, RiskStatus } from "@/lib/api/types";
import { usePermissions } from "@/lib/auth/store";
import {
  cn,
  formatDate,
  formatRelative,
  titleCase,
} from "@/lib/utils";

function percent(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function confidencePercent(value: number) {
  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

function ScoreBreakdown({ risk }: { risk: NonNullable<ReturnType<typeof useRisk>["data"]> }) {
  const t = useTranslations("risks");
  const raw = (risk.score_breakdown ?? {}) as Record<string, unknown>;
  const factors = [
    {
      key: "severity",
      label: "Severity",
      value: Number(raw.severity_value ?? 0),
      weight: Number(raw.severity_weight ?? 0.4),
      valueLabel: String(raw.severity ?? risk.severity),
      bar: "bg-rose-400",
      text: "text-rose-300",
    },
    {
      key: "likelihood",
      label: "Likelihood",
      value: Number(raw.likelihood_value ?? 0),
      weight: Number(raw.likelihood_weight ?? 0.35),
      valueLabel: String(raw.likelihood ?? risk.likelihood),
      bar: "bg-amber-400",
      text: "text-amber-300",
    },
    {
      key: "exposure",
      label: "Exposure",
      value: Number(raw.exposure_value ?? 0),
      weight: Number(raw.exposure_weight ?? 0.25),
      valueLabel: String(raw.exposure ?? risk.exposure),
      bar: "bg-sky-400",
      text: "text-sky-300",
    },
  ];
  return (
    <div className="panel p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-sm font-semibold text-slate-100">{t("scoreBreakdown")}</h2>
          <p className="mt-0.5 text-[11px] text-muted">
            Deterministic weighted model · no model discretion
          </p>
        </div>
        <span className="rounded border border-border bg-white/[0.02] px-2 py-1 font-mono text-[9px] text-muted-2">
          {risk.score.toFixed(1)} / 100
        </span>
      </div>
      <div className="mt-4 space-y-4">
        {factors.map((factor) => (
          <div key={factor.key}>
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-medium text-slate-300">{factor.label}</span>
                <span className={cn("text-[10px] capitalize", factor.text)}>{factor.valueLabel}</span>
              </div>
              <span className="font-mono text-[9px] text-muted-2">
                {Math.round(factor.weight * 100)}% weight
              </span>
            </div>
            <Progress
              value={percent((factor.value / 4) * 100)}
              className="h-1.5"
              indicatorClassName={factor.bar}
            />
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-lg border border-border-soft bg-white/[0.015] p-3">
        <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">Formula</p>
        <p className="mt-1 font-mono text-[10px] leading-relaxed text-muted">
          {String(raw.formula ?? "score = ((severity*0.40 + likelihood*0.35 + exposure*0.25) / 4) * 100")}
        </p>
      </div>
    </div>
  );
}

function EvidenceCard({ evidence }: { evidence: Evidence }) {
  return (
    <div className="rounded-xl border border-border-soft bg-white/[0.015] p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg border border-teal-400/20 bg-teal-400/10 text-teal-300">
          <FileCheck2 className="size-3.5" />
        </div>
        <div className="min-w-0 flex-1">
          <blockquote className="border-l-2 border-accent/30 pl-3 text-[12px] leading-relaxed text-slate-300">
            “{evidence.quote}”
          </blockquote>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <a
              href={evidence.citation_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 rounded border border-border bg-white/[0.025] px-1.5 py-0.5 text-[9px] text-slate-300 transition-colors hover:border-accent/30 hover:text-accent"
            >
              {evidence.citation_label}
              <ArrowUpRight className="size-2.5" />
            </a>
            <span className="text-[9px] text-muted-2">Supports: {titleCase(evidence.supports)}</span>
            <span className="ml-auto flex items-center gap-1.5 text-[9px] text-muted-2">
              <span className="h-1 w-12 overflow-hidden rounded-full bg-white/[0.06]">
                <span
                  className="block h-full rounded-full bg-teal-400"
                  style={{ width: `${confidencePercent(evidence.confidence)}%` }}
                />
              </span>
              {confidencePercent(evidence.confidence)}% confidence
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ActionRow({
  action,
  riskId,
  canAnalyze,
}: {
  action: Action;
  riskId: string;
  canAnalyze: boolean;
}) {
  const request = useRequestApproval(riskId);
  const canRequest = action.status === "draft" && canAnalyze;

  const ask = () => {
    request.mutate(
      { actionId: action.id },
      {
        onSuccess: () =>
          toast.success("Approval requested", {
            description: "The action is now in the approver's queue.",
          }),
        onError: (error) =>
          toast.error("Could not request approval.", {
            description: error instanceof Error ? error.message : undefined,
          }),
      },
    );
  };

  return (
    <div className="rounded-xl border border-border-soft bg-white/[0.015] p-4">
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg border",
            action.automated
              ? "border-accent/20 bg-accent/10 text-accent"
              : "border-sky-400/20 bg-sky-400/10 text-sky-300",
          )}
        >
          {action.automated ? <Sparkles className="size-3.5" /> : <UserRound className="size-3.5" />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-[12px] font-medium leading-snug text-slate-200">{action.title}</p>
              <p className="mt-1 text-[10px] leading-relaxed text-muted">{action.description}</p>
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              <StatusBadge status={action.status} />
              <PriorityBadge priority={action.priority} showDot={false} />
            </div>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-border-soft pt-2.5 text-[9px] text-muted-2">
            <span className="flex items-center gap-1">
              <UserRound className="size-3" /> {titleCase(action.owner_role)}
            </span>
            <span className="flex items-center gap-1">
              <CalendarDays className="size-3" /> {formatDate(action.due_date)}
            </span>
            <span className="flex items-center gap-1">
              {action.automated ? <Sparkles className="size-3" /> : <Wrench className="size-3" />}
              {action.automated ? "Agent-proposed" : "Analyst-created"}
            </span>
            {action.status === "draft" ? (
              <Button
                size="sm"
                variant="secondary"
                className="ml-auto h-7"
                onClick={ask}
                loading={request.isPending}
                disabled={!canRequest}
                title={canAnalyze ? "Request approver decision" : "Analyst or admin access required"}
              >
                {!canAnalyze ? <Lock /> : <ShieldCheck />}
                Request approval
              </Button>
            ) : null}
            {action.status === "pending_approval" ? (
              <Link
                href="/approvals"
                className="ml-auto flex items-center gap-1 text-[9px] text-amber-300 hover:text-amber-200"
              >
                <Clock3 className="size-3" />
                Pending decision
              </Link>
            ) : null}
            {action.status === "approved" ? (
              <span className="ml-auto flex items-center gap-1 text-[9px] text-emerald-300">
                <CheckCircle2 className="size-3" />
                Approved
              </span>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function ApprovalTimeline({
  approvals,
  canApprove,
  onDecision,
}: {
  approvals: Approval[];
  canApprove: boolean;
  onDecision: (approval: Approval, decision: "approve" | "reject") => void;
}) {
  const t = useTranslations("approvals");
  if (approvals.length === 0) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="No approval requests yet"
        description="Draft a remediation action, then request a human decision. Automation never approves its own work."
        className="border-0 bg-transparent py-8"
      />
    );
  }
  return (
    <div className="space-y-3">
      {approvals.map((approval) => (
        <div
          key={approval.id}
          className="rounded-xl border border-border-soft bg-white/[0.015] p-4"
        >
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border",
                approval.status === "approved"
                  ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
                  : approval.status === "rejected"
                    ? "border-rose-400/20 bg-rose-400/10 text-rose-300"
                    : "border-amber-400/20 bg-amber-400/10 text-amber-300",
              )}
            >
              <ApprovalStatusIcon status={approval.status} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={approval.status} />
                <span className="text-[10px] text-muted-2">
                  {formatRelative(approval.created_at)}
                </span>
                {approval.decision ? (
                  <span className="text-[10px] text-muted-2">· decision: {approval.decision}</span>
                ) : null}
              </div>
              <p className="mt-2 text-[12px] font-medium text-slate-200">
                {approval.action_title ?? "Remediation action"}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-[9px] text-muted-2">
                <span>{t("requestedBy")}: {approval.requested_by}</span>
                <span>·</span>
                <span>{t("assignedTo")}: {approval.assigned_to}</span>
              </div>
              {approval.rationale ? (
                <div className="mt-2 rounded-lg border border-border-soft bg-[#060d18]/60 p-2.5">
                  <p className="text-[9px] font-semibold uppercase tracking-wider text-muted-2">
                    {t("rationale")}
                  </p>
                  <p className="mt-1 text-[10px] leading-relaxed text-slate-300">{approval.rationale}</p>
                </div>
              ) : null}
              {approval.decided_at ? (
                <p className="mt-1.5 text-[9px] text-muted-2">
                  Decided {formatRelative(approval.decided_at)}
                </p>
              ) : null}
              {approval.status === "pending" && canApprove ? (
                <div className="mt-3 flex items-center gap-2 border-t border-border-soft pt-2.5">
                  <Button
                    size="sm"
                    className="h-7"
                    onClick={() => onDecision(approval, "approve")}
                  >
                    <CheckCircle2 />
                    {t("approve")}
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    className="h-7"
                    onClick={() => onDecision(approval, "reject")}
                  >
                    <XCircle />
                    {t("reject")}
                  </Button>
                </div>
              ) : null}
              {approval.status === "pending" && !canApprove ? (
                <p className="mt-2 flex items-center gap-1.5 text-[9px] text-amber-300/80">
                  <Lock className="size-3" />
                  Approver or admin access required to decide.
                </p>
              ) : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function RiskDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";
  const t = useTranslations("risks");
  const common = useTranslations("common");
  const risk = useRisk(id);
  const updateStatus = useUpdateRiskStatus(id);
  const { canAnalyze, canApprove } = usePermissions();
  const [addActionOpen, setAddActionOpen] = React.useState(false);
  const [decisionState, setDecisionState] = React.useState<{
    approval: Approval;
    decision: "approve" | "reject";
  } | null>(null);

  if (risk.isLoading) return <PageSkeleton cards={0} />;
  if (risk.isError) {
    return <ErrorState error={risk.error} onRetry={() => void risk.refetch()} />;
  }
  if (!risk.data) return <PageSkeleton cards={0} />;

  const data = risk.data;
  const evidence = data.evidence ?? [];
  const actions = data.actions ?? [];
  const approvals = data.approvals ?? [];
  const breakdown = (data.score_breakdown ?? {}) as Record<string, unknown>;
  const isClosed = data.status === "closed";

  const changeStatus = (value: string) => {
    updateStatus.mutate(value as RiskStatus, {
      onSuccess: () => toast.success(t("statusUpdated")),
      onError: (error) =>
        toast.error("Could not update the risk status.", {
          description: error instanceof Error ? error.message : undefined,
        }),
    });
  };

  return (
    <div className="space-y-5">
      <Link
        href="/risks"
        className="inline-flex items-center gap-1.5 text-[11px] text-muted transition-colors hover:text-accent"
      >
        <ChevronLeft className="size-3.5" />
        {t("title")}
      </Link>

      <PageHeader
        eyebrow={`Act · Risk detail · ${data.supplier_name ?? "Company-level"}`}
        title={data.title}
        description={data.description}
      >
        {canAnalyze ? (
          <Select value={data.status} onValueChange={changeStatus} disabled={updateStatus.isPending}>
            <SelectTrigger className="w-[145px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {["open", "in_review", "mitigating", "closed"].map((status) => (
                <SelectItem key={status} value={status}>
                  {titleCase(status)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <StatusBadge status={data.status} />
        )}
        <Button onClick={() => setAddActionOpen(true)} disabled={!canAnalyze}>
          {canAnalyze ? <Plus /> : <Lock />}
          {t("addAction")}
        </Button>
      </PageHeader>

      <div className="flex flex-wrap items-center gap-2">
        <PriorityBadge priority={data.priority} />
        <VerificationBadge status={data.verification_status} />
        <StatusBadge status={data.status} />
        <span className="rounded border border-border bg-white/[0.02] px-2 py-0.5 text-[9px] uppercase tracking-wider text-muted-2">
          {titleCase(data.category)}
        </span>
        <span className="text-[10px] text-muted-2">
          Created {formatDate(data.created_at)} · Updated {formatRelative(data.updated_at)}
        </span>
      </div>

      {isClosed ? (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/[0.045] px-4 py-3 text-[11px] text-emerald-200">
          <CheckCircle2 className="size-4" />
          This risk is closed. The audit trail preserves the full decision history.
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-12">
        <div className="space-y-4 xl:col-span-8">
          <div className="panel p-5">
            <div className="flex items-start gap-3">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-accent/20 bg-accent/10 text-accent">
                <Fingerprint className="size-4" />
              </div>
              <div>
                <h2 className="font-display text-sm font-semibold text-slate-100">{t("whyItMatters")}</h2>
                <p className="mt-2 text-[12px] leading-relaxed text-slate-300">{data.rationale}</p>
              </div>
            </div>
            <div className="mt-4 grid gap-3 border-t border-border-soft pt-4 sm:grid-cols-4">
              {[
                { label: "Severity", value: titleCase(data.severity) },
                { label: "Likelihood", value: titleCase(data.likelihood) },
                { label: "Exposure", value: titleCase(data.exposure) },
                {
                  label: "Agent confidence",
                  value: `${confidencePercent(data.confidence)}%`,
                },
              ].map((item) => (
                <div key={item.label}>
                  <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-muted-2">
                    {item.label}
                  </p>
                  <p className="mt-1 text-[12px] font-medium capitalize text-slate-200">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          <ScoreBreakdown risk={data} />

          <div className="panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-sm font-semibold text-slate-100">{t("evidenceTitle")}</h2>
                <p className="mt-0.5 text-[11px] text-muted">
                  Source-grounded passages supporting this risk record.
                </p>
              </div>
              <span className="rounded border border-border bg-white/[0.02] px-2 py-1 font-mono text-[9px] text-muted-2">
                {evidence.length} cited
              </span>
            </div>
            <div className="mt-4 space-y-3">
              {evidence.length === 0 ? (
                <EmptyState
                  icon={FileSearch}
                  title={t("noEvidence")}
                  description="A reviewer should gather source evidence before acting on this record."
                  className="border-0 bg-transparent py-8"
                />
              ) : (
                evidence.map((item) => <EvidenceCard key={item.id} evidence={item} />)
              )}
            </div>
          </div>

          <div className="panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-sm font-semibold text-slate-100">{t("remediation")}</h2>
                <p className="mt-0.5 text-[11px] text-muted">
                  Agent-proposed actions remain drafts until a person requests and records a decision.
                </p>
              </div>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setAddActionOpen(true)}
                disabled={!canAnalyze}
              >
                {canAnalyze ? <Plus /> : <Lock />}
                {t("addAction")}
              </Button>
            </div>
            <div className="mt-4 space-y-3">
              {actions.length === 0 ? (
                <EmptyState
                  icon={Wrench}
                  title={t("noActions")}
                  description="Add a concrete remediation action with an owner and due date."
                  className="border-0 bg-transparent py-8"
                />
              ) : (
                actions.map((action) => (
                  <ActionRow key={action.id} action={action} riskId={id} canAnalyze={canAnalyze} />
                ))
              )}
            </div>
          </div>

          <div className="panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-sm font-semibold text-slate-100">{t("humanDecision")}</h2>
                <p className="mt-0.5 text-[11px] text-muted">
                  Single-step approval · every decision is appended to the audit trail.
                </p>
              </div>
              <span className="flex items-center gap-1 rounded-full border border-amber-400/20 bg-amber-400/10 px-2 py-0.5 text-[9px] text-amber-200">
                <ShieldCheck className="size-2.5" />
                Human in the loop
              </span>
            </div>
            <div className="mt-4">
              <ApprovalTimeline
                approvals={approvals}
                canApprove={canApprove}
                onDecision={(approval, decision) => setDecisionState({ approval, decision })}
              />
            </div>
          </div>

          <p className="px-1 text-[10px] leading-relaxed text-muted-2">
            {t("notLegalAdvice")} {common("notLegalAdvice")}
          </p>
        </div>

        <aside className="space-y-4 xl:col-span-4">
          <div className="panel relative overflow-hidden p-5">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-rose-400/[0.04] to-transparent" />
            <div className="relative flex flex-col items-center text-center">
              <ScoreRing score={data.score} priority={data.priority} size={132} stroke={9} />
              <div className="mt-3 flex items-center gap-1.5">
                <PriorityBadge priority={data.priority} />
                <StatusBadge status={data.status} />
              </div>
              <p className="mt-2 text-[10px] leading-relaxed text-muted">
                Weighted severity, likelihood, and exposure. Higher scores enter the queue first.
              </p>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 border-t border-border-soft pt-4">
              <div className="rounded-lg border border-border-soft bg-white/[0.02] p-2.5">
                <p className="text-[9px] uppercase tracking-wider text-muted-2">Evidence</p>
                <p className="mt-1 font-display text-lg font-semibold text-slate-100">{data.evidence_count}</p>
              </div>
              <div className="rounded-lg border border-border-soft bg-white/[0.02] p-2.5">
                <p className="text-[9px] uppercase tracking-wider text-muted-2">Actions</p>
                <p className="mt-1 font-display text-lg font-semibold text-slate-100">{data.action_count}</p>
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between rounded-lg border border-border-soft bg-white/[0.02] px-2.5 py-2">
              <span className="text-[9px] uppercase tracking-wider text-muted-2">Verification</span>
              <VerificationBadge status={data.verification_status} />
            </div>
            <div className="mt-2 flex items-center justify-between rounded-lg border border-border-soft bg-white/[0.02] px-2.5 py-2">
              <span className="text-[9px] uppercase tracking-wider text-muted-2">Agent confidence</span>
              <span className="font-mono text-[10px] text-slate-300">
                {confidencePercent(data.confidence)}%
              </span>
            </div>
          </div>

          <div className="panel p-5">
            <h2 className="font-display text-sm font-semibold text-slate-100">{t("riskSnapshot")}</h2>
            <div className="mt-3 space-y-2.5 text-[11px]">
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-2">Supplier</span>
                <span className="text-right text-slate-300">{data.supplier_name ?? "Company-level"}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-2">Category</span>
                <span className="text-slate-300">{titleCase(data.category)}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-2">Created</span>
                <span className="text-slate-300">{formatDate(data.created_at)}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-2">Updated</span>
                <span className="text-slate-300">{formatRelative(data.updated_at)}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-2">Risk status</span>
                <StatusBadge status={data.status} />
              </div>
            </div>
            {data.supplier ? (
              <div className="mt-4 rounded-lg border border-border-soft bg-white/[0.02] p-3">
                <div className="flex items-center gap-2">
                  <div className="flex size-7 items-center justify-center rounded-md border border-border bg-white/[0.03] text-muted">
                    <Scale className="size-3.5" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-[11px] font-medium text-slate-200">
                      {data.supplier.name}
                    </p>
                    <p className="text-[9px] text-muted-2">
                      {data.supplier.country} · Tier {data.supplier.tier}
                    </p>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-[9px] text-muted-2">
                  <span>{titleCase(data.supplier.category)}</span>
                  <span>{titleCase(data.supplier.risk_level)} risk</span>
                </div>
              </div>
            ) : null}
          </div>

          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <Landmark className="size-4 text-sky-300" />
              <h2 className="font-display text-sm font-semibold text-slate-100">{t("obligation")}</h2>
            </div>
            {data.obligation ? (
              <div className="mt-3">
                <p className="text-[12px] font-medium leading-snug text-slate-200">
                  {data.obligation.title}
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <span className="rounded border border-border bg-white/[0.025] px-1.5 py-0.5 text-[9px] text-muted">
                    {data.obligation.jurisdiction}
                  </span>
                  <span className="rounded border border-border bg-white/[0.025] px-1.5 py-0.5 text-[9px] text-muted">
                    {titleCase(data.obligation.obligation_type)}
                  </span>
                  {data.obligation.effective_date ? (
                    <span className="rounded border border-border bg-white/[0.025] px-1.5 py-0.5 text-[9px] text-muted">
                      Effective {formatDate(data.obligation.effective_date)}
                    </span>
                  ) : null}
                </div>
                <blockquote className="mt-3 border-l-2 border-sky-400/30 pl-3 text-[10px] leading-relaxed text-muted">
                  “{data.obligation.citation_quote}”
                </blockquote>
                <a
                  href={data.obligation.citation_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex items-center gap-1 text-[10px] text-accent hover:text-teal-200"
                >
                  Open source text
                  <ArrowUpRight className="size-3" />
                </a>
              </div>
            ) : (
              <p className="mt-3 text-[11px] text-muted">No mapped obligation.</p>
            )}
          </div>

          <div className="rounded-xl border border-amber-400/15 bg-amber-400/[0.035] p-4">
            <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-200">
              <AlertTriangle className="size-3.5" />
              Review boundary
            </div>
            <p className="mt-2 text-[10px] leading-relaxed text-amber-100/70">
              This is a compliance risk signal, not a legal determination. Confirm obligations with
              qualified counsel or the relevant authority before relying on this record.
            </p>
          </div>

          <div className="panel p-4">
            <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-2">
              <CircleDollarSign className="size-3.5 text-muted" />
              Cost of inaction
            </div>
            <p className="mt-2 text-[10px] leading-relaxed text-muted">
              A late or missing remediation decision can delay buyer clearance, trigger additional
              evidence requests, or escalate supervisory attention.
            </p>
          </div>

          <div className="panel p-4">
            <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-2">
              <ListChecks className="size-3.5 text-muted" />
              Raw score breakdown
            </div>
            <JsonBlock value={breakdown} maxHeight="10rem" className="mt-2" />
          </div>
        </aside>
      </div>

      <AddActionDialog riskId={id} open={addActionOpen} onOpenChange={setAddActionOpen} />
      <ApprovalDecisionDialog
        approval={decisionState?.approval ?? null}
        decision={decisionState?.decision ?? "approve"}
        open={Boolean(decisionState)}
        onOpenChange={(open) => {
          if (!open) setDecisionState(null);
        }}
      />
    </div>
  );
}

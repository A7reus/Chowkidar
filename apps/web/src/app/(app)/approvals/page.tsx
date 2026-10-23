"use client";

import {
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  FileCheck2,
  ListChecks,
  Lock,
  ShieldCheck,
  UserRound,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import * as React from "react";

import { ApprovalDecisionDialog } from "@/components/approvals/decision-dialog";
import { RoleHint } from "@/components/common/access-denied";
import { StatusBadge } from "@/components/common/badges";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useApprovals } from "@/lib/api/hooks";
import type { Approval } from "@/lib/api/types";
import { usePermissions } from "@/lib/auth/store";
import { cn, formatRelative } from "@/lib/utils";

function ApprovalCard({
  approval,
  canApprove,
  onDecision,
}: {
  approval: Approval;
  canApprove: boolean;
  onDecision: (approval: Approval, decision: "approve" | "reject") => void;
}) {
  const t = useTranslations("approvals");
  const pending = approval.status === "pending";
  return (
    <article
      className={cn(
        "panel overflow-hidden border-l-2 p-5",
        pending
          ? "border-l-amber-400/70"
          : approval.status === "approved"
            ? "border-l-emerald-400/70"
            : "border-l-rose-400/70",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <StatusBadge status={approval.status} />
          <span className="flex items-center gap-1 text-[10px] text-muted-2">
            <Clock3 className="size-3" />
            {formatRelative(approval.created_at)}
          </span>
        </div>
        <Link
          href={`/risks/${approval.risk_id}`}
          className="flex items-center gap-1 text-[10px] text-accent transition-colors hover:text-teal-200"
        >
          {t("openRisk")}
          <ArrowUpRight className="size-3" />
        </Link>
      </div>

      <div className="mt-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-2">
          {t("action")}
        </p>
        <h2 className="mt-1 font-display text-[15px] font-semibold leading-snug text-slate-100">
          {approval.action_title ?? "Remediation action"}
        </h2>
        <p className="mt-1 text-[11px] leading-relaxed text-muted">
          {approval.risk_title ?? "Risk record"}
        </p>
      </div>

      <div className="mt-4 grid gap-2 border-t border-border-soft pt-3 text-[10px] sm:grid-cols-2">
        <div className="flex items-start gap-2">
          <UserRound className="mt-0.5 size-3 shrink-0 text-muted-2" />
          <div>
            <p className="text-muted-2">{t("requestedBy")}</p>
            <p className="mt-0.5 truncate text-slate-300">{approval.requested_by}</p>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <ShieldCheck className="mt-0.5 size-3 shrink-0 text-muted-2" />
          <div>
            <p className="text-muted-2">{t("assignedTo")}</p>
            <p className="mt-0.5 truncate text-slate-300">{approval.assigned_to}</p>
          </div>
        </div>
      </div>

      {approval.rationale ? (
        <div className="mt-3 rounded-lg border border-border-soft bg-[#060d18]/60 p-3">
          <div className="flex items-center gap-1.5">
            <FileCheck2 className="size-3 text-muted-2" />
            <p className="text-[9px] font-semibold uppercase tracking-wider text-muted-2">
              {t("rationale")}
            </p>
          </div>
          <p className="mt-1.5 text-[11px] leading-relaxed text-slate-300">{approval.rationale}</p>
          {approval.decided_at ? (
            <p className="mt-1.5 text-[9px] text-muted-2">
              {formatRelative(approval.decided_at)}
            </p>
          ) : null}
        </div>
      ) : null}

      {pending ? (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border-soft pt-3">
          <Button
            size="sm"
            onClick={() => onDecision(approval, "approve")}
            disabled={!canApprove}
          >
            {canApprove ? <CheckCircle2 /> : <Lock />}
            {t("approve")}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => onDecision(approval, "reject")}
            disabled={!canApprove}
          >
            {canApprove ? <XCircle /> : <Lock />}
            {t("reject")}
          </Button>
          {!canApprove ? (
            <span className="ml-auto text-[9px] text-amber-300/80">
              Approver or admin access required
            </span>
          ) : null}
        </div>
      ) : (
        <div className="mt-4 flex items-center gap-2 border-t border-border-soft pt-3 text-[9px] text-muted-2">
          <CheckCircle2 className={cn("size-3", approval.status === "approved" ? "text-emerald-400" : "text-rose-400")} />
          {approval.status === "approved" ? "Remediation approved" : "Remediation rejected"}
          {approval.decided_at ? <span>· {formatRelative(approval.decided_at)}</span> : null}
        </div>
      )}
    </article>
  );
}

const tabs = ["pending", "approved", "rejected", "all"] as const;
type Tab = (typeof tabs)[number];

export default function ApprovalsPage() {
  const t = useTranslations("approvals");
  const { canApprove } = usePermissions();
  const [tab, setTab] = React.useState<Tab>("pending");
  const pending = useApprovals("pending");
  const approved = useApprovals("approved");
  const rejected = useApprovals("rejected");
  const all = useApprovals("all");
  const [decisionState, setDecisionState] = React.useState<{
    approval: Approval;
    decision: "approve" | "reject";
  } | null>(null);

  const current =
    tab === "pending" ? pending : tab === "approved" ? approved : tab === "rejected" ? rejected : all;
  const counts: Record<Tab, number> = {
    pending: pending.data?.total ?? 0,
    approved: approved.data?.total ?? 0,
    rejected: rejected.data?.total ?? 0,
    all: all.data?.total ?? 0,
  };

  if (current.isLoading) return <PageSkeleton cards={3} />;
  if (current.isError) {
    return <ErrorState error={current.error} onRetry={() => void current.refetch()} />;
  }

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Act · Human decision" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <Link href="/risks">
            <ListChecks />
            Risk register
          </Link>
        </Button>
      </PageHeader>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { label: t("pending"), value: counts.pending, tone: "text-amber-300", icon: Clock3, hint: "Awaiting a human decision" },
          { label: t("approved"), value: counts.approved, tone: "text-emerald-300", icon: CheckCircle2, hint: "Recorded in the audit trail" },
          { label: t("rejected"), value: counts.rejected, tone: "text-rose-300", icon: XCircle, hint: "Rejected with a rationale" },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="panel flex items-center gap-3 p-4">
              <div className={cn("flex size-9 items-center justify-center rounded-lg border border-border bg-white/[0.025]", item.tone)}>
                <Icon className="size-4" />
              </div>
              <div>
                <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">{item.label}</p>
                <p className={cn("font-display text-2xl font-semibold", item.tone)}>{item.value}</p>
              </div>
              <p className="ml-auto hidden max-w-[100px] text-right text-[9px] leading-relaxed text-muted-2 sm:block">
                {item.hint}
              </p>
            </div>
          );
        })}
      </div>

      {!canApprove ? (
        <RoleHint
          role="approver"
          title={t("readOnlyTitle")}
          body={t("readOnlyBody")}
          label={t("switchApprover")}
        />
      ) : (
        <div className="flex items-start gap-3 rounded-xl border border-teal-400/15 bg-teal-400/[0.035] p-4">
          <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border border-teal-400/20 bg-teal-400/10 text-teal-300">
            <ShieldCheck className="size-4" />
          </div>
          <div>
            <p className="text-[12px] font-medium text-slate-100">
              Automation proposes. People decide.
            </p>
            <p className="mt-0.5 text-[10px] leading-relaxed text-muted">
              Every decision requires a rationale and is appended to the hash-chained audit trail. An
              approval moves the underlying risk into mitigation.
            </p>
          </div>
          <span className="ml-auto hidden rounded-full border border-teal-400/20 bg-teal-400/10 px-2 py-0.5 text-[9px] text-teal-200 md:block">
            Single-step approval
          </span>
        </div>
      )}

      <Tabs value={tab} onValueChange={(value) => setTab(value as Tab)}>
        <TabsList>
          {tabs.map((item) => (
            <TabsTrigger key={item} value={item} className="gap-1.5">
              {t(item)}
              <span className="rounded border border-border bg-white/[0.025] px-1 py-0.5 font-mono text-[8px] text-muted-2">
                {counts[item]}
              </span>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {current.data && current.data.items.length === 0 ? (
        <EmptyState
          icon={ListChecks}
          title={t("empty")}
          description={
            tab === "pending"
              ? "New approval requests will appear here when an analyst submits a remediation action."
              : "There are no approvals in this view."
          }
        />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {current.data?.items.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              canApprove={canApprove}
              onDecision={(item, decision) => setDecisionState({ approval: item, decision })}
            />
          ))}
        </div>
      )}

      <p className="px-1 text-[10px] leading-relaxed text-muted-2">
        The decision queue is filtered by status. Approvals are assigned to a named approver; admins
        can decide any request.
      </p>

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

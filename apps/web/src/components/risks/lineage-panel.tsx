"use client";

import {
  ArrowUpRight,
  FileCheck2,
  FileText,
  Globe2,
  Landmark,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { StatusBadge } from "@/components/common/badges";
import { ErrorState } from "@/components/common/states";
import { Skeleton } from "@/components/ui/skeleton";
import { useRiskLineage } from "@/lib/api/hooks";
import type { LineageNode } from "@/lib/api/types";
import { cn, formatDate, formatRelative, titleCase } from "@/lib/utils";

const KIND_META: Record<string, { icon: LucideIcon; labelKey: string; tone: string }> = {
  source: { icon: Landmark, labelKey: "lineageSource", tone: "text-sky-300 border-sky-400/20 bg-sky-400/10" },
  signal: { icon: Globe2, labelKey: "lineageSignal", tone: "text-cyan-300 border-cyan-400/20 bg-cyan-400/10" },
  obligation: {
    icon: Scale,
    labelKey: "lineageObligation",
    tone: "text-violet-300 border-violet-400/20 bg-violet-400/10",
  },
  risk: {
    icon: ShieldAlert,
    labelKey: "lineageRisk",
    tone: "text-rose-300 border-rose-400/20 bg-rose-400/10",
  },
  evidence: {
    icon: FileCheck2,
    labelKey: "lineageEvidence",
    tone: "text-teal-300 border-teal-400/20 bg-teal-400/10",
  },
  action: {
    icon: Wrench,
    labelKey: "lineageActions",
    tone: "text-amber-300 border-amber-400/20 bg-amber-400/10",
  },
  approval: {
    icon: ShieldCheck,
    labelKey: "lineageApprovals",
    tone: "text-emerald-300 border-emerald-400/20 bg-emerald-400/10",
  },
  report: {
    icon: FileText,
    labelKey: "lineageReports",
    tone: "text-slate-300 border-slate-400/20 bg-slate-400/10",
  },
};

const CHAIN_KINDS = new Set(["source", "signal", "obligation", "risk"]);

function ChainNode({
  node,
  last,
}: {
  node: LineageNode;
  last: boolean;
}) {
  const t = useTranslations("risks");
  const meta = KIND_META[node.kind] ?? KIND_META.risk;
  const Icon = meta.icon;

  return (
    <li className="flex gap-3">
      <div className="flex flex-col items-center">
        <div
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-lg border",
            meta.tone,
          )}
        >
          <Icon className="size-3.5" />
        </div>
        {!last ? <div className="mt-1 min-h-4 w-px flex-1 bg-border" /> : null}
      </div>
      <div className={cn("min-w-0 flex-1", last ? "pb-0" : "pb-4")}>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">
            {t(meta.labelKey)}
          </span>
          {node.status ? <StatusBadge status={node.status} /> : null}
          {node.occurred_at ? (
            <span className="text-[9px] text-muted-2">{formatDate(node.occurred_at)}</span>
          ) : null}
        </div>
        <p className="mt-1 text-[12px] font-medium leading-snug text-slate-200">{node.label}</p>
        {node.detail ? <p className="mt-0.5 text-[10px] leading-relaxed text-muted">{node.detail}</p> : null}
        {node.href ? (
          <a
            href={node.href}
            target="_blank"
            rel="noreferrer"
            className="mt-1.5 inline-flex items-center gap-1 text-[9px] text-accent transition-colors hover:text-teal-200"
          >
            {t("lineageOpenSource")}
            <ArrowUpRight className="size-2.5" />
          </a>
        ) : null}
      </div>
    </li>
  );
}

export function LineagePanel({ riskId }: { riskId: string }) {
  const t = useTranslations("risks");
  const lineage = useRiskLineage(riskId);

  if (lineage.isLoading) {
    return (
      <div className="panel space-y-3 p-5">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-3 w-64" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }
  if (lineage.isError) {
    return (
      <div className="panel p-5">
        <ErrorState
          error={lineage.error}
          onRetry={() => void lineage.refetch()}
          className="border-0 bg-transparent py-8"
        />
      </div>
    );
  }
  if (!lineage.data) return null;

  const nodes = lineage.data.nodes ?? [];
  const reports = lineage.data.reports ?? [];
  const auditEvents = lineage.data.audit_events ?? [];
  const chain = nodes.filter((node) => CHAIN_KINDS.has(node.kind));
  const evidenceCount = nodes.filter((node) => node.kind === "evidence").length;
  const actionCount = nodes.filter((node) => node.kind === "action").length;
  const approvalCount = nodes.filter((node) => node.kind === "approval").length;

  return (
    <div className="panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-sm font-semibold text-slate-100">{t("lineage")}</h2>
          <p className="mt-0.5 text-[11px] text-muted">{t("lineageSub")}</p>
        </div>
        <div className="rounded-lg border border-border-soft bg-white/[0.02] px-2.5 py-1.5 text-right">
          <p className="text-[8px] uppercase tracking-[0.14em] text-muted-2">{t("traceId")}</p>
          <p className="mt-0.5 font-mono text-[9px] text-slate-300">
            {lineage.data.trace_id ?? t("lineageNoTrace")}
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">
            {t("lineageChain")}
          </p>
          {chain.length === 0 ? (
            <p className="mt-3 text-[11px] text-muted">{t("lineageNoTrace")}</p>
          ) : (
            <ol className="mt-3">
              {chain.map((node, index) => (
                <ChainNode key={`${node.kind}-${node.id}`} node={node} last={index === chain.length - 1} />
              ))}
            </ol>
          )}
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">
              {t("lineageRecorded")}
            </p>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {[
                { label: t("lineageEvidence"), value: evidenceCount },
                { label: t("lineageActions"), value: actionCount },
                { label: t("lineageApprovals"), value: approvalCount },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-lg border border-border-soft bg-white/[0.02] p-2.5"
                >
                  <p className="text-[9px] uppercase tracking-wider text-muted-2">{item.label}</p>
                  <p className="mt-1 font-display text-lg font-semibold text-slate-100">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border-soft bg-white/[0.015] p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">
                {t("lineageReports")}
              </p>
              <Link href="/reports" className="text-[9px] text-accent hover:text-teal-200">
                {t("lineageOpenReport")}
              </Link>
            </div>
            {reports.length === 0 ? (
              <p className="mt-2 text-[10px] text-muted">{t("lineageNoReports")}</p>
            ) : (
              <ul className="mt-2 space-y-1.5">
                {reports.slice(0, 3).map((report) => (
                  <li key={report.id} className="flex items-center justify-between gap-2 text-[10px]">
                    <span className="text-slate-300">
                      {report.format.toUpperCase()} · {formatDate(report.generated_at)}
                    </span>
                    <StatusBadge status={report.status} />
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-lg border border-border-soft bg-white/[0.015] p-3">
            <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">
              {t("lineageAudit")}
            </p>
            {auditEvents.length === 0 ? (
              <p className="mt-2 text-[10px] text-muted">{t("lineageNoAudit")}</p>
            ) : (
              <ul className="mt-2 space-y-1.5">
                {auditEvents.slice(-5).map((event) => (
                  <li key={event.id} className="flex items-start justify-between gap-2 text-[10px]">
                    <div className="min-w-0">
                      <p className="truncate text-slate-300">{titleCase(event.action)}</p>
                      <p className="truncate text-[9px] text-muted-2">{event.actor_email}</p>
                    </div>
                    <span className="shrink-0 text-[9px] text-muted-2">
                      {formatRelative(event.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import {
  ArrowRight,
  Check,
  Clock3,
  Database,
  Gauge,
  Lock,
  RefreshCw,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Waypoints,
  Wrench,
} from "lucide-react";
import { useTranslations } from "next-intl";

import { StatusBadge } from "@/components/common/badges";
import { SectionHeading } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import type { AgentRun, DashboardSummary } from "@/lib/api/types";
import { formatRelative, shortHash } from "@/lib/utils";

type PipelinePanelProps = {
  summary: DashboardSummary;
  latestRun?: AgentRun;
  canRun: boolean;
  running: boolean;
  onRun: (mode: "mock" | "live") => void;
};

export function PipelinePanel({ summary, latestRun, canRun, running, onRun }: PipelinePanelProps) {
  const t = useTranslations("dashboard");
  const output = (latestRun?.output ?? {}) as Record<string, unknown>;
  const counts = (output.counts && typeof output.counts === "object" ? output.counts : {}) as Record<
    string,
    number
  >;
  const verification = Array.isArray(output.verification)
    ? output.verification.filter(
        (item) => typeof item === "object" && item !== null && item.status === "verified",
      ).length
    : null;
  const hasRun = Boolean(latestRun);
  const repairs =
    typeof output.repair_attempts === "number" ? output.repair_attempts : null;

  const steps = [
    {
      label: t("stepIngest"),
      icon: Database,
      value: hasRun ? (counts.signals ?? 0) : summary.signals_last_7_days,
      unit: "signals",
      done: hasRun,
    },
    {
      label: t("stepExtract"),
      icon: ScanSearch,
      value: hasRun ? (counts.candidate_signals ?? 0) : "—",
      unit: "candidates",
      done: hasRun,
    },
    {
      label: t("stepMap"),
      icon: Waypoints,
      value: hasRun ? (counts.obligations ?? 0) : "—",
      unit: "obligations",
      done: hasRun,
    },
    {
      label: t("stepScore"),
      icon: Gauge,
      value: hasRun ? (counts.risks ?? 0) : summary.total_risks,
      unit: hasRun ? "new risks" : "in register",
      done: hasRun,
    },
    {
      label: t("stepRemediate"),
      icon: Wrench,
      value: hasRun ? (counts.actions ?? 0) : "—",
      unit: "draft actions",
      done: hasRun,
    },
    {
      label: t("stepVerify"),
      icon: ShieldCheck,
      value: verification ?? `${summary.verified_evidence_rate}%`,
      unit: verification != null ? "verified" : "evidence rate",
      done: hasRun,
    },
    {
      label: t("stepRepair"),
      icon: RefreshCw,
      value: hasRun ? (repairs ?? 0) : "—",
      unit: "bounded repairs",
      done: hasRun,
    },
  ];

  const message =
    typeof output.message === "string"
      ? output.message
      : latestRun?.status === "failed"
        ? latestRun.error
        : t("noRuns");

  return (
    <div className="panel relative overflow-hidden p-5">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-teal-400/[0.045] to-transparent" />
      <div className="relative">
        <SectionHeading
          title={t("agentActivity")}
          description={t("agentActivitySub")}
          action={
            <div className="flex items-center gap-2">
              {latestRun ? <StatusBadge status={latestRun.status} /> : null}
              <Button
                size="sm"
                variant="secondary"
                onClick={() => onRun("mock")}
                loading={running}
                disabled={!canRun}
                title={canRun ? "Run the agent pipeline" : "Analyst or admin access required"}
              >
                {!canRun ? <Lock /> : <Sparkles />}
                {running ? t("running") : t("runPipeline")}
              </Button>
            </div>
          }
        />

        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-7">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={step.label}
                className="relative rounded-lg border border-border-soft bg-white/[0.018] p-2.5 transition-colors hover:border-accent/20 hover:bg-white/[0.03]"
              >
                <div className="flex items-center gap-1.5 text-[9px] font-semibold uppercase tracking-[0.1em] text-muted-2">
                  <Icon className="size-3 text-accent/70" />
                  {step.label}
                </div>
                <p className="mt-1.5 font-display text-xl font-semibold tracking-tight text-slate-100">
                  {step.value}
                </p>
                <p className="text-[8px] uppercase tracking-wider text-muted-2/80">{step.unit}</p>
                <div className="absolute right-2 top-2">
                  {step.done ? (
                    <span className="flex size-3.5 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300">
                      <Check className="size-2.5" />
                    </span>
                  ) : (
                    <span className="flex size-3.5 items-center justify-center rounded-full bg-white/[0.04] text-muted-2">
                      <Clock3 className="size-2.5" />
                    </span>
                  )}
                </div>
                {index < steps.length - 1 ? (
                  <ArrowRight className="absolute -right-2.5 top-1/2 hidden size-3 -translate-y-1/2 text-border xl:block" />
                ) : null}
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex flex-col gap-1.5 border-t border-border-soft pt-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[10px] leading-relaxed text-muted">
            {message ?? t("noRuns")}
          </p>
          {latestRun ? (
            <div className="flex flex-wrap items-center gap-2 text-[9px] text-muted-2">
              <span>{t("lastRun")} {formatRelative(latestRun.started_at)}</span>
              <span className="text-muted-2/60">·</span>
              <span className="font-mono">{shortHash(latestRun.trace_id, 18)}</span>
              <span className="rounded border border-border bg-white/[0.025] px-1.5 py-0.5 font-mono uppercase">
                {String(output.mode ?? "mock")}
              </span>
            </div>
          ) : (
            <span className="text-[9px] text-muted-2">LangGraph · 7 stages + bounded repair</span>
          )}
        </div>
      </div>
    </div>
  );
}

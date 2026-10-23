"use client";

import {
  ChevronDown,
  FileText,
  ListChecks,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/page-header";
import { ErrorState, PageSkeleton } from "@/components/common/states";
import { StatCard } from "@/components/common/stat-card";
import { LatestSignals } from "@/components/dashboard/latest-signals";
import { PipelinePanel } from "@/components/dashboard/pipeline-panel";
import { PriorityQueue } from "@/components/dashboard/priority-queue";
import { SourceHealthPanel } from "@/components/dashboard/source-health";
import { RiskTrendChart } from "@/components/dashboard/trend-chart";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useDashboard,
  useMeta,
  usePipelineRuns,
  useRunPipeline,
} from "@/lib/api/hooks";
import { useAuthStore, usePermissions } from "@/lib/auth/store";
import { formatDate, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const common = useTranslations("common");
  const user = useAuthStore((state) => state.user);
  const { canAnalyze } = usePermissions();
  const dashboard = useDashboard();
  const meta = useMeta();
  const runs = usePipelineRuns(canAnalyze);
  const runPipeline = useRunPipeline();

  if (dashboard.isLoading) return <PageSkeleton />;
  if (dashboard.isError) {
    return (
      <ErrorState
        error={dashboard.error}
        onRetry={() => void dashboard.refetch()}
      />
    );
  }
  if (!dashboard.data) return <PageSkeleton />;

  const summary = dashboard.data;
  const latestRun = runs.data?.[0];
  const firstName = user?.name?.split(" ")[0] ?? "there";
  const company = meta.data?.company.name ?? summary.company_name;

  const run = (mode: "mock" | "live") => {
    runPipeline.mutate(
      { mode },
      {
        onSuccess: (result) => {
          toast.success(result.message, {
            description:
              result.errors.length > 0
                ? `${result.errors.length} item(s) need review.`
                : `Trace ${result.run.trace_id.slice(0, 12)} · ${mode} mode`,
          });
          if (result.errors.length > 0) {
            toast.warning("Pipeline finished with review items.", {
              description: result.errors[0],
            });
          }
        },
        onError: (error) => {
          toast.error("Pipeline run failed.", {
            description: error instanceof Error ? error.message : undefined,
          });
        },
      },
    );
  };

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow={`Overview · ${company}`}
        title={`${t("greeting")}, ${firstName}.`}
        description={t("subtitle")}
      >
        <Button variant="secondary" asChild>
          <Link href="/reports">
            <FileText />
            Reports
          </Link>
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              loading={runPipeline.isPending}
              disabled={!canAnalyze}
              title={
                canAnalyze
                  ? "Run the risk pipeline"
                  : "Analyst or admin access required"
              }
            >
              <Sparkles />
              {runPipeline.isPending ? t("running") : t("runPipeline")}
              <ChevronDown className="size-3.5 opacity-70" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Agent execution</DropdownMenuLabel>
            <DropdownMenuItem onSelect={() => run("mock")} disabled={!canAnalyze}>
              <Sparkles />
              {t("runMock")}
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => run("live")} disabled={!canAnalyze}>
              <Sparkles />
              {t("runLive")}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <div className="px-2 py-1.5 text-[10px] leading-relaxed text-muted-2">
              Live mode calls Gemini and Groq with automatic fallback. Mock mode is
              deterministic and instant.
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
      </PageHeader>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={t("openRisks")}
          value={summary.open_risks}
          hint={`${summary.total_risks} total · ${summary.critical_risks} critical`}
          icon={ShieldAlert}
          tone="sky"
          trend={summary.trend.map((point) => point.open)}
        />
        <StatCard
          label={t("critical")}
          value={summary.critical_risks}
          hint={`${summary.high_risks} high priority`}
          icon={ShieldAlert}
          tone="rose"
          trend={summary.trend.map((point) => point.high)}
        />
        <StatCard
          label={t("pendingApprovals")}
          value={summary.pending_approvals}
          hint="Human decision required"
          icon={ListChecks}
          tone="amber"
        />
        <StatCard
          label={t("verifiedEvidence")}
          value={formatPercent(summary.verified_evidence_rate, 0)}
          hint="Evidence-linked risk records"
          icon={ShieldCheck}
          tone="teal"
        />
      </div>

      <PipelinePanel
        summary={summary}
        latestRun={latestRun}
        canRun={canAnalyze}
        running={runPipeline.isPending}
        onRun={run}
      />

      <div className="grid gap-4 xl:grid-cols-12">
        <div className="panel p-5 xl:col-span-8">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="font-display text-sm font-semibold tracking-tight text-slate-100">
                {t("riskTrend")}
              </h2>
              <p className="mt-0.5 text-[11px] text-muted">{t("riskTrendSub")}</p>
            </div>
            <div className="flex items-center gap-4 text-[10px] text-muted">
              <span className="flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-teal-400" />
                Open
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-rose-400" />
                High + critical
              </span>
              <span className="hidden items-center gap-1.5 text-muted-2 sm:flex">
                {formatDate(new Date(), "dd MMM yyyy")}
              </span>
            </div>
          </div>
          <RiskTrendChart summary={summary} />
        </div>
        <div className="xl:col-span-4">
          <PriorityQueue risks={summary.top_risks} />
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-12">
        <div className="xl:col-span-5">
          <SourceHealthPanel sources={summary.source_health} />
        </div>
        <div className="xl:col-span-7">
          <LatestSignals signals={summary.recent_signals} />
        </div>
      </div>

      <p className="px-1 text-[10px] leading-relaxed text-muted-2">
        {common("notLegalAdvice")} Evidence remains reviewable at the source, and every
        material action is written to the audit trail.
      </p>
    </div>
  );
}

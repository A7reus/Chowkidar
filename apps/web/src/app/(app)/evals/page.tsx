"use client";

import {
  AlertTriangle,
  ArrowUpRight,
  BadgeCheck,
  BrainCircuit,
  CheckCircle2,
  CircleSlash2,
  FileCheck2,
  FlaskConical,
  Play,
  RefreshCw,
  ScanText,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { AccessDenied } from "@/components/common/access-denied";
import { StatusBadge } from "@/components/common/badges";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEvals, useMeta, useRunEvals } from "@/lib/api/hooks";
import type { EvalCaseResult, EvalSummary } from "@/lib/api/types";
import { usePermissions } from "@/lib/auth/store";
import { cn, formatDate, formatPercent, titleCase } from "@/lib/utils";

type Metric = {
  key: string;
  label: string;
  value: number;
  gate: number;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
};

function metricTone(value: number, gate: number) {
  if (value >= gate) return { text: "text-emerald-300", bar: "bg-emerald-400", border: "border-emerald-400/20" };
  if (value >= gate - 0.15) return { text: "text-amber-300", bar: "bg-amber-400", border: "border-amber-400/20" };
  return { text: "text-rose-300", bar: "bg-rose-400", border: "border-rose-400/20" };
}

function MetricCard({ metric }: { metric: Metric }) {
  const tone = metricTone(metric.value, metric.gate);
  const Icon = metric.icon;
  const passing = metric.value >= metric.gate;
  return (
    <div className={cn("panel p-4", tone.border)}>
      <div className="flex items-start justify-between gap-2">
        <div className={cn("flex size-8 items-center justify-center rounded-lg border border-border bg-white/[0.025]", tone.text)}>
          <Icon className="size-3.5" />
        </div>
        <span className={cn("flex items-center gap-1 text-[9px]", passing ? "text-emerald-300" : "text-amber-300")}>
          {passing ? <CheckCircle2 className="size-3" /> : <AlertTriangle className="size-3" />}
          gate {Math.round(metric.gate * 100)}%
        </span>
      </div>
      <p className="mt-3 font-display text-2xl font-semibold tracking-tight text-slate-100">
        {formatPercent(metric.value * 100, 0)}
      </p>
      <p className="mt-0.5 text-[10px] font-medium text-slate-300">{metric.label}</p>
      <Progress value={metric.value * 100} className="mt-3 h-1" indicatorClassName={tone.bar} />
      <p className="mt-2 line-clamp-2 text-[9px] leading-relaxed text-muted-2">{metric.description}</p>
    </div>
  );
}

function CaseResultRow({ result }: { result: EvalCaseResult }) {
  return (
    <TableRow className="border-border-soft/70">
      <TableCell className="py-3">
        <p className="text-[11px] font-medium text-slate-200">{titleCase(result.case_id)}</p>
        <p className="mt-0.5 font-mono text-[8px] text-muted-2">{result.case_id}</p>
      </TableCell>
      <TableCell>
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-medium",
            result.passed
              ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
              : "border-rose-400/20 bg-rose-400/10 text-rose-300",
          )}
        >
          {result.passed ? <CheckCircle2 className="size-2.5" /> : <XCircle className="size-2.5" />}
          {result.passed ? "Pass" : "Fail"}
        </span>
      </TableCell>
      <TableCell className="hidden sm:table-cell">
        <span className={cn("text-[10px]", result.citation_coverage >= 1 ? "text-emerald-300" : "text-rose-300")}>
          {formatPercent(result.citation_coverage * 100, 0)}
        </span>
      </TableCell>
      <TableCell className="hidden md:table-cell">
        <span className={cn("flex items-center gap-1 text-[10px]", result.verifier_pass ? "text-emerald-300" : "text-rose-300")}>
          {result.verifier_pass ? <CheckCircle2 className="size-3" /> : <XCircle className="size-3" />}
          {result.verifier_pass ? "Accepted" : "Flagged"}
        </span>
      </TableCell>
      <TableCell className="hidden lg:table-cell">
        <span className={cn("flex items-center gap-1 text-[10px]", result.no_legal_advice ? "text-emerald-300" : "text-rose-300")}>
          {result.no_legal_advice ? <ShieldCheck className="size-3" /> : <CircleSlash2 className="size-3" />}
          {result.no_legal_advice ? "Clear" : "Blocked"}
        </span>
      </TableCell>
      <TableCell className="max-w-[280px]">
        {result.notes.length === 0 ? (
          <span className="text-[10px] text-muted-2">All checks passed.</span>
        ) : (
          <ul className="space-y-0.5">
            {result.notes.map((note) => (
              <li key={note} className="flex items-start gap-1 text-[9px] leading-relaxed text-amber-200/80">
                <AlertTriangle className="mt-0.5 size-2.5 shrink-0" />
                {note}
              </li>
            ))}
          </ul>
        )}
      </TableCell>
    </TableRow>
  );
}

function ModelStack({ summary }: { summary: EvalSummary }) {
  const t = useTranslations("evals");
  const meta = useMeta();
  const live = meta.data?.llm_mode === "live";
  const stack = [
    {
      role: "Extraction",
      model: "Gemini Flash",
      note: "Obligation + citation extraction",
      icon: ScanText,
      tone: "border-sky-400/20 bg-sky-400/10 text-sky-300",
    },
    {
      role: "Classification",
      model: "Groq GPT-OSS 120B",
      note: "Risk mapping and remediation drafts",
      icon: BrainCircuit,
      tone: "border-violet-400/20 bg-violet-400/10 text-violet-300",
    },
    {
      role: "Verification",
      model: "Gemini Pro",
      note: "Citation and language guard",
      icon: BadgeCheck,
      tone: "border-teal-400/20 bg-teal-400/10 text-teal-300",
    },
  ];
  return (
    <div className="panel p-5">
      <div className="flex items-center gap-2">
        <Sparkles className="size-4 text-accent" />
        <h2 className="font-display text-sm font-semibold text-slate-100">{t("stack")}</h2>
        <span
          className={cn(
            "ml-auto rounded-full border px-2 py-0.5 text-[9px]",
            live
              ? "border-teal-400/20 bg-teal-400/10 text-teal-200"
              : "border-amber-400/20 bg-amber-400/10 text-amber-200",
          )}
        >
          {live ? "Live mode" : "Mock mode"}
        </span>
      </div>
      <p className="mt-1.5 text-[10px] leading-relaxed text-muted">{t("stackBody")}</p>
      <div className="mt-4 space-y-2">
        {stack.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.role} className="flex items-start gap-2.5 rounded-lg border border-border-soft bg-white/[0.015] p-2.5">
              <div className={cn("mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md border", item.tone)}>
                <Icon className="size-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                  <p className="text-[10px] font-medium text-slate-200">{item.role}</p>
                  <p className="font-mono text-[8px] text-muted-2">{item.model}</p>
                </div>
                <p className="mt-0.5 text-[9px] text-muted-2">{item.note}</p>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 rounded-lg border border-border-soft bg-[#060d18]/60 p-2.5">
        <div className="flex items-center justify-between text-[9px]">
          <span className="text-muted-2">Retrieval</span>
          <span className="font-mono text-[8px] text-slate-300">BGE-M3 + pgvector + FTS</span>
        </div>
        <div className="mt-1 flex items-center justify-between text-[9px]">
          <span className="text-muted-2">Golden set</span>
          <span className="font-mono text-[8px] text-slate-300">{summary.name}</span>
        </div>
        <div className="mt-1 flex items-center justify-between text-[9px]">
          <span className="text-muted-2">Cases</span>
          <span className="font-mono text-[8px] text-slate-300">
            {summary.passed_cases} / {summary.total_cases}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function EvalsPage() {
  const t = useTranslations("evals");
  const { canViewEvals } = usePermissions();
  const evals = useEvals(canViewEvals);
  const runEvals = useRunEvals();

  if (!canViewEvals) {
    return (
      <div className="space-y-5">
        <PageHeader eyebrow="Governance · Quality" title={t("title")} description={t("subtitle")} />
        <AccessDenied
          role="analyst"
          title={t("restricted")}
          body="Evaluations are restricted to Analyst and Admin accounts. This account can use the rest of the pilot workspace."
          label={t("switchAnalyst")}
        />
      </div>
    );
  }

  if (evals.isLoading) return <PageSkeleton cards={5} />;
  if (evals.isError) {
    return <ErrorState error={evals.error} onRetry={() => void evals.refetch()} />;
  }
  if (!evals.data) return <PageSkeleton cards={5} />;

  const summary = evals.data;
  const allPassed = summary.passed_cases === summary.total_cases;
  const metrics: Metric[] = [
    {
      key: "extraction",
      label: t("extraction"),
      value: summary.extraction_accuracy,
      gate: 0.9,
      icon: ScanText,
      description: "Expected obligation keyword is present in extracted text.",
    },
    {
      key: "citation",
      label: t("citation"),
      value: summary.citation_coverage,
      gate: 1,
      icon: FileCheck2,
      description: "Every quoted evidence passage appears verbatim in the source.",
    },
    {
      key: "verifier",
      label: t("verifier"),
      value: summary.verifier_pass_rate,
      gate: 0.9,
      icon: ShieldCheck,
      description: "Evidence-first verifier accepts the record or sends it to review.",
    },
    {
      key: "noAdvice",
      label: t("noAdvice"),
      value: summary.no_legal_advice_rate,
      gate: 1,
      icon: CircleSlash2,
      description: "Prohibited legal-advice language is absent from generated copy.",
    },
    {
      key: "priority",
      label: t("priority"),
      value: summary.priority_agreement,
      gate: 0.9,
      icon: FlaskConical,
      description: "Deterministic score lands in the expected priority band.",
    },
  ];

  const run = () => {
    runEvals.mutate(undefined, {
      onSuccess: (result) => {
        toast.success("Evaluation run complete", {
          description: `${result.passed_cases} of ${result.total_cases} golden cases passed.`,
        });
      },
      onError: (error) => {
        toast.error("Evaluation run failed", {
          description: error instanceof Error ? error.message : undefined,
        });
      },
    });
  };

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Governance · Quality" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <Link href="/reports">
            <ArrowUpRight />
            Audit pack
          </Link>
        </Button>
        <Button onClick={run} loading={runEvals.isPending}>
          {runEvals.isPending ? <RefreshCw className="animate-spin" /> : <Play />}
          {runEvals.isPending ? t("running") : t("run")}
        </Button>
      </PageHeader>

      <div className="panel relative overflow-hidden p-5">
        <div
          className={cn(
            "pointer-events-none absolute -right-12 -top-16 size-56 rounded-full blur-3xl",
            allPassed ? "bg-emerald-400/[0.06]" : "bg-amber-400/[0.06]",
          )}
        />
        <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div
              className={cn(
                "flex size-14 shrink-0 flex-col items-center justify-center rounded-2xl border",
                allPassed
                  ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-300"
                  : "border-amber-400/25 bg-amber-400/10 text-amber-300",
              )}
            >
              <span className="font-display text-xl font-semibold leading-none">{summary.passed_cases}</span>
              <span className="mt-1 text-[8px] uppercase tracking-wider opacity-70">/ {summary.total_cases}</span>
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-display text-lg font-semibold text-slate-100">
                  {allPassed ? "All golden cases pass" : "Golden set needs review"}
                </h2>
                <StatusBadge status={allPassed ? "completed" : "degraded"} />
              </div>
              <p className="mt-1 max-w-xl text-[11px] leading-relaxed text-muted">
                {allPassed
                  ? "Extraction, citation grounding, verification, priority agreement, and the legal-advice guard all cleared every case."
                  : `${summary.total_cases - summary.passed_cases} case(s) failed one or more quality gates. Inspect the notes below before shipping a model or prompt change.`}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-[9px] text-muted-2">
                <span>{t("lastRun")}: {formatDate(summary.generated_at, "dd MMM yyyy, HH:mm")}</span>
                <span className="font-mono">{summary.name}</span>
                <span>{summary.results.length} golden cases</span>
              </div>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 rounded-xl border border-border-soft bg-white/[0.02] px-3 py-2">
            <ShieldCheck className={cn("size-4", allPassed ? "text-emerald-400" : "text-amber-400")} />
            <div>
              <p className="text-[9px] uppercase tracking-wider text-muted-2">Verdict</p>
              <p className={cn("text-[11px] font-medium", allPassed ? "text-emerald-300" : "text-amber-300")}>
                {allPassed ? "Ship-ready gate" : "Blocked from release"}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {metrics.map((metric) => (
          <MetricCard key={metric.key} metric={metric} />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-12">
        <div className="space-y-4 xl:col-span-8">
          <div className="panel overflow-hidden">
            <div className="flex items-center justify-between gap-3 border-b border-border-soft px-4 py-3">
              <div>
                <h2 className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-2">
                  {t("cases")}
                </h2>
                <p className="mt-0.5 text-[10px] text-muted">
                  Fixed inputs from the seeded source fixtures, run through the agent pipeline.
                </p>
              </div>
              <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 font-mono text-[9px] text-muted-2">
                {summary.passed_cases} / {summary.total_cases} pass
              </span>
            </div>
            {summary.results.length === 0 ? (
              <EmptyState
                icon={FlaskConical}
                title="No evaluation results"
                description="Run the golden set to generate case-level results."
                className="border-0 bg-transparent py-12"
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("case")}</TableHead>
                    <TableHead>{t("result")}</TableHead>
                    <TableHead className="hidden sm:table-cell">{t("citation")}</TableHead>
                    <TableHead className="hidden md:table-cell">{t("verifier")}</TableHead>
                    <TableHead className="hidden lg:table-cell">{t("noAdvice")}</TableHead>
                    <TableHead>{t("notes")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summary.results.map((result) => (
                    <CaseResultRow key={result.case_id} result={result} />
                  ))}
                </TableBody>
              </Table>
            )}
          </div>

          <div className="panel p-5">
            <h2 className="font-display text-sm font-semibold text-slate-100">{t("qualityGates")}</h2>
            <p className="mt-0.5 text-[10px] text-muted">
              Hard gates are enforced before a generated risk can enter the approval queue.
            </p>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {[
                [t("gateCitation"), summary.citation_coverage >= 1],
                [t("gateVerifier"), summary.verifier_pass_rate >= 0.9],
                [t("gateLanguage"), summary.no_legal_advice_rate >= 1],
                ["Deterministic weighted score with visible breakdown", summary.priority_agreement >= 0.9],
              ].map(([label, passing]) => (
                <div
                  key={String(label)}
                  className="flex items-start gap-2 rounded-lg border border-border-soft bg-white/[0.015] p-2.5"
                >
                  {passing ? (
                    <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-emerald-400" />
                  ) : (
                    <XCircle className="mt-0.5 size-3.5 shrink-0 text-rose-400" />
                  )}
                  <span className="text-[10px] leading-relaxed text-slate-300">{label}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 border-t border-border-soft pt-3 text-[9px] leading-relaxed text-muted-2">
              A passing golden set does not prove production accuracy. It is a regression guard against
              prompt, model, and retrieval changes. Human review remains mandatory for every material
              action.
            </p>
          </div>
        </div>

        <div className="space-y-4 xl:col-span-4">
          <ModelStack summary={summary} />
          <div className="panel p-5">
            <h2 className="font-display text-sm font-semibold text-slate-100">What this proves</h2>
            <div className="mt-3 space-y-3">
              {[
                {
                  title: "Grounded output",
                  body: "Every risk carries a quote that is checked against the original signal text.",
                  icon: FileCheck2,
                },
                {
                  title: "Language safety",
                  body: "Generated copy cannot contain prohibited legal-advice phrasing.",
                  icon: CircleSlash2,
                },
                {
                  title: "Reviewable priority",
                  body: "A weighted formula, not model vibes, decides the order of work.",
                  icon: FlaskConical,
                },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="flex items-start gap-2.5">
                    <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md border border-border bg-white/[0.025] text-muted">
                      <Icon className="size-3.5" />
                    </div>
                    <div>
                      <p className="text-[11px] font-medium text-slate-200">{item.title}</p>
                      <p className="mt-0.5 text-[10px] leading-relaxed text-muted">{item.body}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <p className="px-1 text-[10px] leading-relaxed text-muted-2">
            Evaluations are a governance artifact, not a compliance certification.{" "}
            {titleCase("human review remains mandatory")}.
          </p>
        </div>
      </div>
    </div>
  );
}

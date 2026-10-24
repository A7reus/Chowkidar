"use client";

import {
  Braces,
  Download,
  FileCode2,
  FileText,
  Info,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { RoleHint } from "@/components/common/access-denied";
import { ReportFormatBadge } from "@/components/common/badges";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { downloadReportFile, useGenerateReport, useReports } from "@/lib/api/hooks";
import type { Report, ReportFormat } from "@/lib/api/types";
import { usePermissions } from "@/lib/auth/store";
import { formatDate, formatRelative } from "@/lib/utils";

const formats: Array<{
  format: ReportFormat;
  icon: React.ComponentType<{ className?: string }>;
  titleKey: "pdf" | "json" | "markdown";
  descKey: "pdfDesc" | "jsonDesc" | "markdownDesc";
  accent: string;
  button: string;
}> = [
  {
    format: "pdf",
    icon: FileText,
    titleKey: "pdf",
    descKey: "pdfDesc",
    accent: "border-rose-400/20 bg-rose-400/10 text-rose-300",
    button: "Generate PDF",
  },
  {
    format: "json",
    icon: Braces,
    titleKey: "json",
    descKey: "jsonDesc",
    accent: "border-sky-400/20 bg-sky-400/10 text-sky-300",
    button: "Generate JSON",
  },
  {
    format: "markdown",
    icon: FileCode2,
    titleKey: "markdown",
    descKey: "markdownDesc",
    accent: "border-violet-400/20 bg-violet-400/10 text-violet-300",
    button: "Generate Markdown",
  },
];

function reportCounts(report: Report): Record<string, number> {
  const summary = (report.summary ?? {}) as Record<string, unknown>;
  return (summary.counts && typeof summary.counts === "object" ? summary.counts : {}) as Record<
    string,
    number
  >;
}

export default function ReportsPage() {
  const t = useTranslations("reports");
  const common = useTranslations("common");
  const { canGenerateReports } = usePermissions();
  const reports = useReports();
  const generateReport = useGenerateReport();
  const [downloading, setDownloading] = React.useState<string | null>(null);

  if (reports.isLoading) return <PageSkeleton cards={3} />;
  if (reports.isError) {
    return <ErrorState error={reports.error} onRetry={() => void reports.refetch()} />;
  }

  const generate = (format: ReportFormat) => {
    generateReport.mutate(format, {
      onSuccess: async (report) => {
        try {
          await downloadReportFile(report);
          toast.success(t("generated"), {
            description: "The download should begin automatically.",
          });
        } catch (error) {
          toast.error("Report created, but the download failed.", {
            description: error instanceof Error ? error.message : undefined,
          });
        }
      },
      onError: (error) =>
        toast.error("Could not generate the report.", {
          description: error instanceof Error ? error.message : undefined,
        }),
    });
  };

  const download = async (report: Report) => {
    setDownloading(report.id);
    try {
      await downloadReportFile(report);
    } catch (error) {
      toast.error("Could not download the report.", {
        description: error instanceof Error ? error.message : undefined,
      });
    } finally {
      setDownloading(null);
    }
  };

  const latest = reports.data?.items[0];

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Act · Audit pack" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <a href="/audit">
            <ShieldCheck />
            Audit trail
          </a>
        </Button>
        {latest ? (
          <Button
            variant="secondary"
            onClick={() => void download(latest)}
            loading={downloading === latest.id}
          >
            <Download />
            Latest
          </Button>
        ) : null}
      </PageHeader>

      {!canGenerateReports ? (
        <RoleHint
          role="analyst"
          title="Report generation requires analyst access"
          body="You can download existing reports as a member of this workspace. Generating a fresh audit pack requires Analyst or Admin access."
          label="Switch to Analyst"
        />
      ) : null}

      <div className="grid gap-3 lg:grid-cols-3">
        {formats.map((item) => {
          const Icon = item.icon;
          const loading = generateReport.isPending && generateReport.variables === item.format;
          return (
            <div key={item.format} className="panel flex flex-col p-5">
              <div className="flex items-start justify-between gap-3">
                <div className={`flex size-10 items-center justify-center rounded-xl border ${item.accent}`}>
                  <Icon className="size-4.5" />
                </div>
                <ReportFormatBadge format={item.format} />
              </div>
              <h2 className="mt-4 font-display text-[15px] font-semibold text-slate-100">
                {t(item.titleKey)}
              </h2>
              <p className="mt-1.5 flex-1 text-[11px] leading-relaxed text-muted">{t(item.descKey)}</p>
              <Button
                className="mt-4"
                variant={item.format === "pdf" ? "default" : "secondary"}
                onClick={() => generate(item.format)}
                loading={loading}
                disabled={!canGenerateReports}
              >
                {item.format === "pdf" ? <FileText /> : <Download />}
                {loading ? t("generating") : item.button}
              </Button>
            </div>
          );
        })}
      </div>

      <div className="panel overflow-hidden">
        <div className="flex items-center justify-between gap-3 border-b border-border-soft px-4 py-3">
          <div>
            <h2 className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-2">
              {t("recent")}
            </h2>
            <p className="mt-0.5 text-[10px] text-muted">{t("recentSub")}</p>
          </div>
          <Button variant="ghost" size="icon-sm" onClick={() => void reports.refetch()} title="Refresh">
            <RefreshCw />
          </Button>
        </div>

        {reports.data && reports.data.items.length === 0 ? (
          <EmptyState
            icon={FileText}
            title={t("empty")}
            description="Choose a format above. The report will include the current risk register, evidence citations, methodology, and limitations."
            className="border-0 bg-transparent py-12"
          />
        ) : (
          <div>
            {reports.data?.items.map((report) => {
              const counts = reportCounts(report);
              return (
                <div
                  key={report.id}
                  className="flex flex-col gap-3 border-b border-border-soft px-4 py-3.5 last:border-b-0 sm:flex-row sm:items-center"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-white/[0.025] text-muted">
                      {report.format === "pdf" ? (
                        <FileText className="size-3.5" />
                      ) : report.format === "json" ? (
                        <Braces className="size-3.5" />
                      ) : (
                        <FileCode2 className="size-3.5" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <ReportFormatBadge format={report.format} />
                        <span className="font-mono text-[9px] text-muted-2">
                          {report.id.slice(0, 8)}
                        </span>
                        <span className="text-[9px] text-muted-2">
                          {formatRelative(report.generated_at)}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-[11px] text-slate-300">
                        {counts.risks ?? 0} risks · {counts.critical ?? 0} critical ·{" "}
                        {counts.pending_approvals ?? 0} pending approvals
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:justify-end">
                    <span className="hidden text-[9px] text-muted-2 md:block">
                      {formatDate(report.generated_at, "dd MMM yyyy, HH:mm")}
                    </span>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => void download(report)}
                      loading={downloading === report.id}
                    >
                      <Download />
                      {t("download")}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <Info className="size-4 text-sky-300" />
            <h2 className="font-display text-sm font-semibold text-slate-100">What is inside</h2>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {[
              "Executive summary and risk counts",
              "Prioritized risk register with scores",
              "Evidence quotes and citation links",
              "Suggested remediation and owners",
              "Approval decisions and audit context",
              "Methodology and explicit limitations",
            ].map((item) => (
              <div key={item} className="flex items-start gap-2 rounded-lg border border-border-soft bg-white/[0.015] p-2.5">
                <ShieldCheck className="mt-0.5 size-3 shrink-0 text-teal-400" />
                <span className="text-[10px] leading-relaxed text-slate-300">{item}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <FileText className="size-4 text-muted" />
            <h2 className="font-display text-sm font-semibold text-slate-100">Methodology & limits</h2>
          </div>
          <p className="mt-3 text-[10px] leading-relaxed text-muted">
            Weighted score = ((severity × 0.40 + likelihood × 0.35 + exposure × 0.25) / 4) × 100.
            Priority thresholds: critical ≥ 80, high ≥ 60, medium ≥ 35.
          </p>
          <p className="mt-2 text-[10px] leading-relaxed text-muted">
            This pilot uses a fictional company and a small set of synthetic and public-source
            signals. Coverage is not exhaustive; absence of a signal is not evidence of compliance.
            Potential name matches are not findings.
          </p>
          <p className="mt-3 border-t border-border-soft pt-3 text-[10px] leading-relaxed text-amber-100/60">
            {common("notLegalAdvice")}
          </p>
        </div>
      </div>
    </div>
  );
}

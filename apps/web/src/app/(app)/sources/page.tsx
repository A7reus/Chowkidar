"use client";

import {
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  Database,
  Landmark,
  Newspaper,
  RefreshCw,
  Scale,
  ShieldAlert,
  Sparkles,
  WifiOff,
} from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/page-header";
import { ErrorState, PageSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { useDashboard, useMeta, useSources, useSyncSource } from "@/lib/api/hooks";
import { usePermissions } from "@/lib/auth/store";
import { cn, formatDate, formatRelative, titleCase } from "@/lib/utils";

const sourceIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  bd_bank: Landmark,
  eu_eurlex: Scale,
  us_uflpa: ShieldAlert,
  gdelt: Newspaper,
};

const streamRole: Record<string, { label: string; variant: "success" | "info" | "warning" }> = {
  bd_bank: { label: "Primary", variant: "success" },
  eu_eurlex: { label: "Primary", variant: "success" },
  us_uflpa: { label: "Supporting", variant: "info" },
  gdelt: { label: "News", variant: "warning" },
};

export default function SourcesPage() {
  const t = useTranslations("sources");
  const common = useTranslations("common");
  const { canAnalyze } = usePermissions();
  const sources = useSources();
  const dashboard = useDashboard();
  const meta = useMeta();
  const syncSource = useSyncSource();

  const healthById = new Map((dashboard.data?.source_health ?? []).map((item) => [item.id, item]));

  if (sources.isLoading) return <PageSkeleton cards={4} />;
  if (sources.isError) {
    return <ErrorState error={sources.error} onRetry={() => void sources.refetch()} />;
  }

  const items = sources.data ?? [];
  const primaryCount = items.filter((source) => ["bd_bank", "eu_eurlex"].includes(source.stream_key)).length;

  const sync = (sourceId: string, name: string) => {
    syncSource.mutate(sourceId, {
      onSuccess: (result) =>
        toast.success(`${name} synced`, {
          description: `${result.signals_created} new signal(s). ${result.message}`,
        }),
      onError: (error) =>
        toast.error("Sync failed", {
          description: error instanceof Error ? error.message : undefined,
        }),
    });
  };

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Monitor · Ingestion" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <a href="/signals">
            <Database />
            Signal inbox
          </a>
        </Button>
      </PageHeader>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { label: "Independent streams", value: items.length, icon: Database, tone: "text-sky-300" },
          { label: "Primary regulatory", value: primaryCount, icon: Landmark, tone: "text-teal-300" },
          {
            label: "Signals monitored",
            value: dashboard.data?.signals_last_7_days ?? 0,
            icon: Sparkles,
            tone: "text-amber-300",
          },
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
            </div>
          );
        })}
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-sky-400/15 bg-sky-400/[0.035] p-4">
        <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border border-sky-400/20 bg-sky-400/10 text-sky-300">
          <WifiOff className="size-4" />
        </div>
        <div>
          <p className="text-[12px] font-medium text-slate-100">Two independent streams are the minimum.</p>
          <p className="mt-0.5 text-[10px] leading-relaxed text-muted">
            Chowkidar combines Bangladesh Bank circulars and EUR-Lex regulation as primary sources,
            UFLPA entity-list signals as a supporting stream, and GDELT news as an operating-risk
            signal. The hosted pilot replays fixtures; live connectors are not implemented.
          </p>
        </div>
        <span className="ml-auto hidden shrink-0 rounded-full border border-sky-400/20 bg-sky-400/10 px-2 py-0.5 text-[9px] text-sky-200 md:block">
          {meta.data?.streams.length ?? 4} streams
        </span>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        {items.map((source) => {
          const Icon = sourceIcons[source.stream_key] ?? Database;
          const health = healthById.get(source.id);
          const role = streamRole[source.stream_key] ?? { label: "Supporting", variant: "info" as const };
          const isSyncing = syncSource.isPending && syncSource.variables === source.id;
          return (
            <article key={source.id} className="panel p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-xl border border-border bg-gradient-to-br from-white/[0.045] to-transparent text-slate-300">
                    <Icon className="size-4.5" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider",
                          role.variant === "success"
                            ? "border-teal-400/20 bg-teal-400/10 text-teal-300"
                            : role.variant === "info"
                              ? "border-sky-400/20 bg-sky-400/10 text-sky-300"
                              : "border-amber-400/20 bg-amber-400/10 text-amber-300",
                        )}
                      >
                        {role.label}
                      </span>
                      <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 font-mono text-[8px] text-muted-2">
                        {source.jurisdiction}
                      </span>
                    </div>
                    <h2 className="mt-1.5 font-display text-[15px] font-semibold text-slate-100">
                      {source.name}
                    </h2>
                    <p className="mt-0.5 text-[10px] text-muted-2">
                      {titleCase(source.source_type)} · {source.cadence}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className={cn("size-1.5 rounded-full", source.status === "healthy" ? "bg-emerald-400 live-dot" : "bg-amber-400")} />
                  <span className="text-[9px] capitalize text-muted">{source.status}</span>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-border-soft bg-white/[0.02] p-2.5">
                  <p className="text-[9px] uppercase tracking-wider text-muted-2">{t("signals")}</p>
                  <p className="mt-1 font-display text-lg font-semibold text-slate-100">
                    {health?.signal_count ?? "—"}
                  </p>
                </div>
                <div className="rounded-lg border border-border-soft bg-white/[0.02] p-2.5">
                  <p className="text-[9px] uppercase tracking-wider text-muted-2">{t("lastSync")}</p>
                  <p className="mt-1 text-[11px] text-slate-300">
                    {source.last_synced_at ? formatRelative(source.last_synced_at) : t("never")}
                  </p>
                </div>
              </div>

              {source.last_error ? (
                <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-400/20 bg-amber-400/[0.04] p-2.5">
                  <WifiOff className="mt-0.5 size-3 shrink-0 text-amber-300" />
                  <p className="text-[9px] leading-relaxed text-amber-100/70">{source.last_error}</p>
                </div>
              ) : null}

              <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border-soft pt-3">
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[10px] text-muted transition-colors hover:text-accent"
                >
                  Open source
                  <ArrowUpRight className="size-3" />
                </a>
                <span className="text-[9px] text-muted-2">
                  Updated {source.last_synced_at ? formatDate(source.last_synced_at, "dd MMM, HH:mm") : "never"}
                </span>
                <Button
                  size="sm"
                  variant="secondary"
                  className="ml-auto h-7"
                  onClick={() => sync(source.id, source.name)}
                  loading={isSyncing}
                  disabled={!canAnalyze}
                  title={canAnalyze ? "Sync this source" : "Analyst or admin access required"}
                >
                  <RefreshCw />
                  {t("sync")}
                </Button>
              </div>
            </article>
          );
        })}
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <Clock3 className="size-4 text-accent" />
            <h2 className="font-display text-sm font-semibold text-slate-100">How ingestion is designed</h2>
          </div>
          <div className="mt-4 space-y-3">
            {[
              { step: "01", title: "Schedule", body: "n8n and a FastAPI cron fallback are scaffolded; the hosted pilot runs manual fixture sync." },
              { step: "02", title: "Fetch & normalize", body: "Live connectors are not implemented. Fixture payloads follow the same signal-row contract." },
              { step: "03", title: "Parse & chunk", body: "Docling is optional and not on the pilot path; fixture text is chunked for citation retrieval." },
              { step: "04", title: "Agent pipeline", body: "The LangGraph workflow extracts obligations, maps risks, scores, drafts remediation, and verifies." },
            ].map((item) => (
              <div key={item.step} className="flex gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-md border border-border bg-white/[0.02] font-mono text-[9px] text-muted-2">
                  {item.step}
                </span>
                <div>
                  <p className="text-[11px] font-medium text-slate-200">{item.title}</p>
                  <p className="mt-0.5 text-[10px] leading-relaxed text-muted">{item.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="size-4 text-emerald-400" />
            <h2 className="font-display text-sm font-semibold text-slate-100">Source health policy</h2>
          </div>
          <p className="mt-2 text-[10px] leading-relaxed text-muted">{t("ingestion")}</p>
          <div className="mt-4 space-y-2">
            {[
              ["Healthy", "Last run succeeded; new signals are being ingested.", "bg-emerald-400"],
              ["Degraded", "Cached results are in use; the next run is retried.", "bg-amber-400"],
              ["Error", "The connector is failing; an analyst is notified.", "bg-rose-400"],
            ].map(([label, body, dot]) => (
              <div key={label} className="flex items-start gap-2 rounded-lg border border-border-soft bg-white/[0.015] p-2.5">
                <span className={cn("mt-1 size-1.5 shrink-0 rounded-full", dot)} />
                <div>
                  <p className="text-[10px] font-medium text-slate-300">{label}</p>
                  <p className="mt-0.5 text-[9px] leading-relaxed text-muted-2">{body}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 border-t border-border-soft pt-3 text-[9px] leading-relaxed text-muted-2">
            {common("notLegalAdvice")} Raw evidence is always retained for review.
          </p>
        </div>
      </div>
    </div>
  );
}

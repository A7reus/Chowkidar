"use client";

import {
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  FileText,
  FilterX,
  Landmark,
  Newspaper,
  Radio,
  Scale,
  Search,
  ShieldAlert,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";

import {
  JurisdictionBadge,
  SeverityBadge,
  SignalTypeBadge,
  StatusBadge,
} from "@/components/common/badges";
import { JsonBlock } from "@/components/common/copy";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSignal, useSignals, useSources } from "@/lib/api/hooks";
import type { Signal, SignalFilters } from "@/lib/api/types";
import { cn, formatDate, formatRelative, titleCase } from "@/lib/utils";

function SourceIcon({ name, className }: { name: string | null | undefined; className?: string }) {
  const value = (name ?? "").toLowerCase();
  if (value.includes("bangladesh bank")) return <Landmark className={className} />;
  if (value.includes("eur-lex") || value.includes("eurlex")) return <Scale className={className} />;
  if (value.includes("uflpa") || value.includes("dhs")) return <ShieldAlert className={className} />;
  if (value.includes("gdelt")) return <Newspaper className={className} />;
  return <Radio className={className} />;
}

const severityBar: Record<string, string> = {
  critical: "bg-rose-400",
  high: "bg-orange-400",
  medium: "bg-amber-400",
  low: "bg-slate-500",
};

function SignalRow({ signal, onOpen }: { signal: Signal; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group flex w-full items-start gap-3 border-b border-border-soft/70 px-4 py-3.5 text-left transition-colors last:border-b-0 hover:bg-white/[0.025]"
    >
      <span className={cn("mt-1 h-8 w-0.5 shrink-0 rounded-full", severityBar[signal.severity] ?? severityBar.low)} />
      <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-white/[0.025] text-muted transition-colors group-hover:border-accent/20 group-hover:text-accent">
        <SourceIcon name={signal.source_name} className="size-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <SeverityBadge severity={signal.severity} />
          <SignalTypeBadge type={signal.signal_type} />
          <JurisdictionBadge jurisdiction={signal.jurisdiction} />
          {signal.supplier_name ? (
            <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 text-[9px] text-muted-2">
              {signal.supplier_name}
            </span>
          ) : null}
        </div>
        <p className="mt-1.5 text-[12.5px] font-medium leading-snug text-slate-200 transition-colors group-hover:text-white">
          {signal.title}
        </p>
        <p className="mt-1 line-clamp-2 text-[10px] leading-relaxed text-muted">{signal.summary}</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[9px] text-muted-2">
          <span className="font-medium text-muted">{signal.source_name}</span>
          <span>·</span>
          <span>Published {formatDate(signal.published_at, "dd MMM yyyy")}</span>
          <span>·</span>
          <span>Ingested {formatRelative(signal.ingested_at)}</span>
          <span className="ml-auto hidden items-center gap-1 text-accent/70 group-hover:text-accent sm:flex">
            Inspect evidence
            <ChevronRight className="size-3 transition-transform group-hover:translate-x-0.5" />
          </span>
        </div>
      </div>
    </button>
  );
}

function SignalDetailDialog({
  signalId,
  open,
  onOpenChange,
}: {
  signalId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const t = useTranslations("signals");
  const signal = useSignal(open ? signalId : null);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t("detailTitle")}</DialogTitle>
          <DialogDescription>
            Source text is preserved verbatim. The extraction layer cites these passages.
          </DialogDescription>
        </DialogHeader>

        {signal.isLoading ? (
          <div className="space-y-3">
            <div className="skeleton h-5 w-3/4 rounded" />
            <div className="skeleton h-3 w-full rounded" />
            <div className="skeleton h-3 w-5/6 rounded" />
            <div className="skeleton h-32 w-full rounded" />
          </div>
        ) : signal.isError ? (
          <ErrorState error={signal.error} onRetry={() => void signal.refetch()} />
        ) : signal.data ? (
          <div className="space-y-4">
            <div>
              <div className="flex flex-wrap items-center gap-1.5">
                <SeverityBadge severity={signal.data.severity} />
                <SignalTypeBadge type={signal.data.signal_type} />
                <JurisdictionBadge jurisdiction={signal.data.jurisdiction} />
                <StatusBadge status={signal.data.status} />
              </div>
              <h3 className="mt-2 font-display text-lg font-semibold leading-snug text-slate-100">
                {signal.data.title}
              </h3>
              <p className="mt-1 text-[11px] leading-relaxed text-muted">{signal.data.summary}</p>
            </div>

            <div className="grid gap-3 rounded-lg border border-border-soft bg-white/[0.02] p-3 text-[10px] sm:grid-cols-2">
              <div>
                <p className="text-muted-2">{t("source")}</p>
                <p className="mt-0.5 text-slate-300">{signal.data.source_name}</p>
              </div>
              <div>
                <p className="text-muted-2">External ID</p>
                <p className="mt-0.5 font-mono text-[9px] text-slate-300">{signal.data.external_id}</p>
              </div>
              <div>
                <p className="text-muted-2">{t("published")}</p>
                <p className="mt-0.5 text-slate-300">{formatDate(signal.data.published_at, "dd MMM yyyy, HH:mm")}</p>
              </div>
              <div>
                <p className="text-muted-2">{t("ingested")}</p>
                <p className="mt-0.5 text-slate-300">{formatDate(signal.data.ingested_at, "dd MMM yyyy, HH:mm")}</p>
              </div>
              {signal.data.supplier_name ? (
                <div>
                  <p className="text-muted-2">Supplier</p>
                  <p className="mt-0.5 text-slate-300">{signal.data.supplier_name}</p>
                </div>
              ) : null}
            </div>

            <div>
              <div className="mb-1.5 flex items-center gap-1.5">
                <FileText className="size-3.5 text-muted-2" />
                <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-2">
                  {t("rawText")}
                </p>
              </div>
              <pre className="max-h-56 overflow-auto rounded-lg border border-border bg-[#060d18] p-3 font-mono text-[10px] leading-relaxed text-slate-300 scrollbar-thin">
                {signal.data.raw_text}
              </pre>
            </div>

            <div>
              <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-2">
                {t("metadata")}
              </p>
              <JsonBlock value={signal.data.metadata ?? {}} maxHeight="10rem" />
            </div>

            <div className="flex flex-wrap items-center gap-2 border-t border-border-soft pt-3">
              <a
                href={signal.data.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white/[0.025] px-2.5 py-1.5 text-[10px] text-slate-300 transition-colors hover:border-accent/30 hover:text-accent"
              >
                {t("openSource")}
                <ArrowUpRight className="size-3" />
              </a>
              <span className="flex items-center gap-1 text-[9px] text-muted-2">
                <CheckCircle2 className="size-3 text-emerald-400" />
                Original text preserved for citation
              </span>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

export default function SignalsPage() {
  const t = useTranslations("signals");
  const searchParams = useSearchParams();
  const initialSignal = searchParams.get("signal");
  const [detailId, setDetailId] = React.useState<string | null>(initialSignal);
  const [detailOpen, setDetailOpen] = React.useState(Boolean(initialSignal));
  const [search, setSearch] = React.useState("");
  const deferredSearch = React.useDeferredValue(search);
  const [source, setSource] = React.useState("all");
  const [jurisdiction, setJurisdiction] = React.useState("all");
  const [severity, setSeverity] = React.useState("all");
  const [signalType, setSignalType] = React.useState("all");
  const sources = useSources();

  const filters: SignalFilters = {
    q: deferredSearch.trim() || undefined,
    source_id: source === "all" ? undefined : source,
    jurisdiction: jurisdiction === "all" ? undefined : jurisdiction,
    severity: severity === "all" ? undefined : severity,
    signal_type: signalType === "all" ? undefined : signalType,
    limit: 100,
  };
  const signals = useSignals(filters);

  const activeFilters = [
    source !== "all",
    jurisdiction !== "all",
    severity !== "all",
    signalType !== "all",
    search.trim().length > 0,
  ].filter(Boolean).length;

  const reset = () => {
    setSearch("");
    setSource("all");
    setJurisdiction("all");
    setSeverity("all");
    setSignalType("all");
  };

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Monitor · Raw evidence" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <a href="/sources">
            <Radio />
            {sources.data?.length ?? 4} sources
          </a>
        </Button>
      </PageHeader>

      <div className="panel p-3">
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-[minmax(240px,1.5fr)_repeat(4,minmax(130px,0.7fr))_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-2" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t("searchPlaceholder")}
              className="pl-8"
            />
          </div>
          <Select value={source} onValueChange={setSource}>
            <SelectTrigger>
              <SelectValue placeholder={t("allSources")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allSources")}</SelectItem>
              {(sources.data ?? []).map((item) => (
                <SelectItem key={item.id} value={item.id}>
                  {item.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={jurisdiction} onValueChange={setJurisdiction}>
            <SelectTrigger>
              <SelectValue placeholder={t("allJurisdictions")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allJurisdictions")}</SelectItem>
              {["BD", "EU", "US", "GLOBAL"].map((item) => (
                <SelectItem key={item} value={item}>
                  {item === "GLOBAL" ? "Global" : item}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={severity} onValueChange={setSeverity}>
            <SelectTrigger>
              <SelectValue placeholder={t("allSeverities")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allSeverities")}</SelectItem>
              {["critical", "high", "medium", "low"].map((item) => (
                <SelectItem key={item} value={item}>
                  {titleCase(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={signalType} onValueChange={setSignalType}>
            <SelectTrigger>
              <SelectValue placeholder={t("allTypes")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allTypes")}</SelectItem>
              {["regulatory", "financial_regulatory", "sanctions", "operational", "news"].map((item) => (
                <SelectItem key={item} value={item}>
                  {titleCase(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="icon"
            onClick={reset}
            disabled={activeFilters === 0}
            title="Clear filters"
          >
            <FilterX />
          </Button>
        </div>
        {activeFilters > 0 ? (
          <div className="mt-2 flex items-center gap-2 border-t border-border-soft pt-2 text-[10px] text-muted-2">
            <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5">
              {activeFilters} active
            </span>
            <button type="button" onClick={reset} className="text-accent hover:text-teal-200">
              Reset
            </button>
          </div>
        ) : null}
      </div>

      {signals.isLoading ? (
        <PageSkeleton cards={0} />
      ) : signals.isError ? (
        <ErrorState error={signals.error} onRetry={() => void signals.refetch()} />
      ) : signals.data && signals.data.items.length === 0 ? (
        <EmptyState
          icon={Radio}
          title="No signals match these filters"
          description="Adjust the filters or sync a source to pull the latest evidence."
          action={
            activeFilters > 0 ? (
              <Button variant="secondary" size="sm" onClick={reset}>
                <FilterX /> Clear filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-border-soft px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-2">
                Signal inbox
              </span>
              <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 font-mono text-[9px] text-muted-2">
                {signals.data?.total ?? 0}
              </span>
            </div>
            <span className="flex items-center gap-1.5 text-[9px] text-muted-2">
              <span className="size-1.5 rounded-full bg-teal-400 live-dot" />
              {signals.data?.items.length ?? 0} loaded
            </span>
          </div>
          <div>
            {signals.data?.items.map((signal) => (
              <SignalRow
                key={signal.id}
                signal={signal}
                onOpen={() => {
                  setDetailId(signal.id);
                  setDetailOpen(true);
                }}
              />
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3 text-[10px] text-muted-2">
        <span className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-rose-400" /> Critical
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-orange-400" /> High
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-amber-400" /> Medium
        </span>
        <span className="ml-auto">Signals are evidence, not conclusions.</span>
      </div>

      <SignalDetailDialog
        signalId={detailId}
        open={detailOpen}
        onOpenChange={(open) => {
          setDetailOpen(open);
          if (!open) setDetailId(null);
        }}
      />
    </div>
  );
}

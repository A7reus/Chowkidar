"use client";

import {
  ArrowUpRight,
  Braces,
  ChevronDown,
  ChevronUp,
  FileSearch,
  Layers3,
  Link2,
  Loader2,
  Search as SearchIcon,
  ShieldCheck,
  Sparkles,
  TextSearch,
} from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";

import { EmptyState, ErrorState } from "@/components/common/states";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useSearch } from "@/lib/api/hooks";
import type { SearchResult } from "@/lib/api/types";
import { cn, titleCase } from "@/lib/utils";

const suggestions = [
  "export proceeds",
  "forced labour",
  "CSDDD due diligence",
  "port strike",
  "factory safety",
  "UFLPA entity list",
];

function SearchResultCard({ result, index }: { result: SearchResult; index: number }) {
  const t = useTranslations("search");
  const [expanded, setExpanded] = React.useState(false);
  const relevance = Math.max(0, Math.min(100, Math.round(result.score * 100)));
  const long = result.content.length > 420;
  return (
    <article className="panel overflow-hidden p-4 transition-colors hover:border-accent/20">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg border border-border bg-white/[0.025] font-mono text-[9px] text-muted-2">
          {String(index + 1).padStart(2, "0")}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="rounded border border-teal-400/20 bg-teal-400/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider text-teal-300">
              Cited chunk
            </span>
            <span className="flex items-center gap-1 rounded border border-border bg-white/[0.025] px-1.5 py-0.5 text-[8px] text-muted">
              <Layers3 className="size-2.5" />
              {result.section_path || "Body"}
            </span>
            <span className="ml-auto flex items-center gap-1.5 text-[9px] text-muted-2">
              {t("relevance")}
              <span className="font-mono text-[10px] text-slate-300">{relevance}%</span>
            </span>
          </div>

          <p className="mt-2 font-mono text-[9px] leading-relaxed text-muted-2">
            {result.citation_label}
          </p>

          <div
            className={cn(
              "mt-2 whitespace-pre-wrap text-[11px] leading-relaxed text-slate-300",
              !expanded && long && "line-clamp-5",
            )}
          >
            {result.content}
          </div>
          {long ? (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="mt-1.5 flex items-center gap-1 text-[9px] text-accent hover:text-teal-200"
            >
              {expanded ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
              {expanded ? "Show less" : "Show full chunk"}
            </button>
          ) : null}

          <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-border-soft pt-2.5">
            <div className="flex min-w-[120px] flex-1 items-center gap-2">
              <Progress value={relevance} className="h-1 max-w-[160px]" indicatorClassName="bg-teal-400" />
              <span className="text-[8px] text-muted-2">hybrid relevance</span>
            </div>
            <a
              href={result.citation_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-[9px] text-muted transition-colors hover:text-accent"
            >
              <Link2 className="size-3" />
              Open citation
              <ArrowUpRight className="size-2.5" />
            </a>
            {result.signal_id ? (
              <Link
                href={`/signals?signal=${result.signal_id}`}
                className="inline-flex items-center gap-1 text-[9px] text-accent transition-colors hover:text-teal-200"
              >
                <FileSearch className="size-3" />
                {t("openSignal")}
              </Link>
            ) : null}
          </div>
        </div>
      </div>
    </article>
  );
}

export default function SearchPage() {
  const t = useTranslations("search");
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const [input, setInput] = React.useState(initialQuery);
  const [submitted, setSubmitted] = React.useState(
    initialQuery.trim().length >= 2 ? initialQuery : "",
  );

  const search = useSearch(submitted);
  const hasQuery = submitted.trim().length >= 2;
  const results = search.data?.results ?? [];

  const execute = (value: string) => {
    const query = value.trim();
    if (query.length < 2) return;
    setInput(query);
    setSubmitted(query);
    window.history.replaceState(null, "", `/search?q=${encodeURIComponent(query)}`);
  };

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    execute(input);
  };

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Intelligence · Evidence" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <Link href="/graph">
            <Layers3 />
            Supply-chain graph
          </Link>
        </Button>
        <Button variant="secondary" asChild>
          <Link href="/signals">
            <TextSearch />
            Signal inbox
          </Link>
        </Button>
      </PageHeader>

      <div className="panel p-4">
        <form onSubmit={onSubmit} className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-2" />
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={t("placeholder")}
              className="h-11 pl-9 text-[13px]"
              autoFocus
            />
          </div>
          <Button type="submit" size="lg" disabled={input.trim().length < 2} loading={search.isFetching}>
            <SearchIcon />
            Search evidence
          </Button>
        </form>
        <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] text-muted-2">
          <Sparkles className="size-3 text-accent/70" />
          <span>{t("hint")}</span>
          <span className="ml-auto hidden items-center gap-1 sm:flex">
            <Braces className="size-3" />
            Source chunks only · no generated answer
          </span>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-12">
        <div className="space-y-3 xl:col-span-8">
          {!hasQuery ? (
            <EmptyState
              icon={FileSearch}
              title={t("start")}
              description={t("startBody")}
              className="py-16"
              action={
                <div className="flex flex-wrap justify-center gap-1.5">
                  {suggestions.slice(0, 4).map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => execute(item)}
                      className="rounded-full border border-border bg-white/[0.025] px-2.5 py-1 text-[10px] text-muted transition-colors hover:border-accent/25 hover:text-accent"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              }
            />
          ) : search.isLoading ? (
            <div className="panel flex items-center gap-3 p-8 text-[11px] text-muted">
              <Loader2 className="size-4 animate-spin text-accent" />
              {t("searching")}
            </div>
          ) : search.isError ? (
            <ErrorState error={search.error} onRetry={() => void search.refetch()} />
          ) : results.length === 0 ? (
            <EmptyState
              icon={FileSearch}
              title={t("empty")}
              description="Try a broader phrase, or check that the source chunks have been seeded for this workspace."
              action={
                <Button variant="secondary" size="sm" onClick={() => execute("export proceeds")}>
                  Try “export proceeds”
                </Button>
              }
            />
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2 px-1">
                <p className="text-[11px] text-muted">
                  <span className="font-semibold text-slate-200">{results.length}</span> {t("results")} for{" "}
                  <span className="text-slate-200">“{submitted}”</span>
                </p>
                <span className="ml-auto flex items-center gap-1.5 rounded-full border border-border bg-white/[0.02] px-2 py-0.5 text-[9px] text-muted-2">
                  <span className={cn("size-1.5 rounded-full", search.data?.mode === "live" ? "bg-emerald-400" : "bg-amber-400")} />
                  {search.data?.mode ?? "mock"} retrieval
                </span>
              </div>
              {results.map((result, index) => (
                <SearchResultCard key={result.chunk_id} result={result} index={index} />
              ))}
              <p className="px-1 text-[9px] leading-relaxed text-muted-2">
                Ranking is fused across vector similarity and full-text search, then reranked. Scores are
                relative, not a legal-confidence measure.
              </p>
            </>
          )}
        </div>

        <aside className="space-y-3 xl:col-span-4">
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <div className="flex size-8 items-center justify-center rounded-lg border border-sky-400/20 bg-sky-400/10 text-sky-300">
                <Layers3 className="size-3.5" />
              </div>
              <h2 className="font-display text-sm font-semibold text-slate-100">{t("how")}</h2>
            </div>
            <p className="mt-2 text-[10px] leading-relaxed text-muted">{t("howBody")}</p>
            <div className="mt-4 space-y-2">
              {[
                ["01", "Chunk", "Signals are parsed into citeable evidence chunks."],
                ["02", "Embed", "BGE-M3 vectors land in pgvector alongside full-text indexes."],
                ["03", "Fuse & rerank", "Both rankings are fused, then reranked for relevance."],
                ["04", "Cite", "Only source text is returned. No answer is synthesized."],
              ].map(([step, title, body]) => (
                <div key={step} className="flex gap-2.5">
                  <span className="flex size-5 shrink-0 items-center justify-center rounded border border-border bg-white/[0.02] font-mono text-[8px] text-muted-2">
                    {step}
                  </span>
                  <div>
                    <p className="text-[10px] font-medium text-slate-300">{title}</p>
                    <p className="text-[9px] leading-relaxed text-muted-2">{body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-5">
            <h2 className="font-display text-sm font-semibold text-slate-100">Suggested queries</h2>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {suggestions.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => execute(item)}
                  className="rounded-lg border border-border bg-white/[0.02] px-2 py-1 text-[9px] text-muted transition-colors hover:border-accent/25 hover:text-accent"
                >
                  {item}
                </button>
              ))}
            </div>
            <div className="mt-4 rounded-lg border border-border-soft bg-white/[0.015] p-3">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="size-3 text-emerald-400" />
                <p className="text-[9px] font-medium text-slate-300">Evidence-first by design</p>
              </div>
              <p className="mt-1 text-[9px] leading-relaxed text-muted-2">
                Every result is a source chunk with a citation. A reviewer can open the underlying
                signal and verify the exact language before relying on it.
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-amber-400/15 bg-amber-400/[0.035] p-4">
            <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-amber-200">Review boundary</p>
            <p className="mt-1.5 text-[10px] leading-relaxed text-amber-100/70">
              Retrieval helps you find language, not interpret it. {titleCase("not legal advice")}.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

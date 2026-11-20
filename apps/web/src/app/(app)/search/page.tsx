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
  Network,
  Route,
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
import { useGraphSearch, useSearch } from "@/lib/api/hooks";
import type {
  GraphRAGNode,
  GraphRAGResponse,
  GraphRAGSearchResult,
  SearchResult,
} from "@/lib/api/types";
import { cn, titleCase } from "@/lib/utils";

const suggestions = [
  "export proceeds",
  "forced labour",
  "CSDDD due diligence",
  "port strike",
  "factory safety",
  "UFLPA entity list",
  "SinoFab ownership",
  "Dhaka Knit risks",
];

type EntityKind = GraphRAGNode["kind"];

const entityTone: Record<EntityKind, string> = {
  company: "border-teal-400/20 bg-teal-400/10 text-teal-300",
  supplier: "border-slate-400/20 bg-slate-400/10 text-slate-300",
  buyer: "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
  policy: "border-violet-400/20 bg-violet-400/10 text-violet-300",
  signal: "border-amber-400/20 bg-amber-400/10 text-amber-200",
  obligation: "border-sky-400/20 bg-sky-400/10 text-sky-300",
  risk: "border-rose-400/20 bg-rose-400/10 text-rose-300",
};

function EntityChip({ kind, label }: { kind: EntityKind; label: string }) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center gap-1 truncate rounded border px-1.5 py-0.5 text-[8px]",
        entityTone[kind],
      )}
      title={label}
    >
      <span className="font-semibold uppercase tracking-wider">{kind}</span>
      <span className="truncate">{label}</span>
    </span>
  );
}

function isGraphResult(result: SearchResult): result is GraphRAGSearchResult {
  return "related_entities" in result;
}

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
            {isGraphResult(result) && result.origin === "graph" ? (
              <span className="flex items-center gap-1 rounded border border-violet-400/20 bg-violet-400/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider text-violet-300">
                <Network className="size-2.5" />
                {t("viaGraph")}
              </span>
            ) : null}
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
          {isGraphResult(result) && result.related_entities.length > 0 ? (
            <div className="mt-2.5 flex flex-wrap items-center gap-1">
              <span className="mr-0.5 text-[8px] uppercase tracking-wider text-muted-2">{t("linkedEntities")}</span>
              {result.related_entities.slice(0, 5).map((entity) => (
                <EntityChip key={entity.id} kind={entity.kind} label={entity.label} />
              ))}
            </div>
          ) : null}
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
              <span className="text-[8px] text-muted-2">
                {isGraphResult(result) ? t("fusedRelevance") : "hybrid relevance"}
              </span>
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

function GraphContextPanel({ data }: { data: GraphRAGResponse }) {
  const t = useTranslations("search");
  const queryEntities = data.entities.filter((entity) => entity.source === "query");
  const inferred = data.subgraph.edges.filter((edge) => edge.inferred).length;
  return (
    <div className="panel p-5" data-testid="graph-context">
      <div className="flex items-center gap-2">
        <div className="flex size-8 items-center justify-center rounded-lg border border-violet-400/20 bg-violet-400/10 text-violet-300">
          <Network className="size-3.5" />
        </div>
        <h2 className="font-display text-sm font-semibold text-slate-100">{t("graphContext")}</h2>
        <span className="ml-auto font-mono text-[9px] text-muted-2">
          {data.subgraph.nodes.length} nodes · {data.subgraph.edges.length} edges · {data.hops} hops
        </span>
      </div>
      <p className="mt-2 text-[10px] leading-relaxed text-muted">{data.traversal_summary.split(" Strongest path:")[0]}</p>

      <p className="mt-4 text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">{t("graphEntities")}</p>
      {queryEntities.length ? (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {queryEntities.map((entity) => (
            <EntityChip key={entity.node_id} kind={entity.kind} label={entity.label} />
          ))}
        </div>
      ) : (
        <p className="mt-1 text-[9px] leading-relaxed text-muted-2">{t("noQueryEntities")}</p>
      )}

      {data.paths.length ? (
        <>
          <p className="mt-4 flex items-center gap-1 text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">
            <Route className="size-3" />
            {t("graphPaths")}
          </p>
          <ol className="mt-1.5 space-y-1.5">
            {data.paths.slice(0, 4).map((path) => (
              <li
                key={path.node_ids.join(">")}
                className="rounded-lg border border-border-soft bg-white/[0.015] p-2 text-[9px] leading-relaxed text-slate-300"
              >
                {path.description}
              </li>
            ))}
          </ol>
        </>
      ) : null}

      <div className="mt-4 flex items-center justify-between gap-2">
        <p className="text-[8px] leading-relaxed text-muted-2">
          {inferred > 0 ? t("inferredNote", { count: inferred }) : null}
        </p>
        <Button variant="secondary" size="sm" asChild>
          <Link href="/graph">
            <Layers3 />
            {t("openGraph")}
          </Link>
        </Button>
      </div>
    </div>
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
  const [graphMode, setGraphMode] = React.useState(searchParams.get("graph") !== "0");

  const plainSearch = useSearch(submitted, !graphMode);
  const graphSearch = useGraphSearch(submitted, graphMode);
  const search = graphMode ? graphSearch : plainSearch;
  const hasQuery = submitted.trim().length >= 2;
  const results: SearchResult[] = search.data?.results ?? [];
  const graphData = graphMode ? graphSearch.data : undefined;
  const graphEvidence = graphData?.graph_evidence ?? [];

  const syncUrl = (query: string, graph: boolean) => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (!graph) params.set("graph", "0");
    const suffix = params.toString();
    window.history.replaceState(null, "", suffix ? `/search?${suffix}` : "/search");
  };

  const execute = (value: string) => {
    const query = value.trim();
    if (query.length < 2) return;
    setInput(query);
    setSubmitted(query);
    syncUrl(query, graphMode);
  };

  const toggleGraph = () => {
    const next = !graphMode;
    setGraphMode(next);
    syncUrl(submitted, next);
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
          <button
            type="button"
            role="switch"
            aria-checked={graphMode}
            onClick={toggleGraph}
            title={t("graphModeHint")}
            className={cn(
              "flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[9px] transition-colors",
              graphMode
                ? "border-violet-400/30 bg-violet-400/10 text-violet-200"
                : "border-border bg-white/[0.02] text-muted hover:text-slate-300",
            )}
          >
            <span className={cn("size-1.5 rounded-full", graphMode ? "bg-violet-300" : "bg-muted-2")} />
            <Network className="size-3" />
            {t("graphMode")}
          </button>
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
                  {search.data?.mode ?? "mock"} retrieval{graphMode ? " + graph" : ""}
                </span>
              </div>
              {results.map((result, index) => (
                <SearchResultCard key={result.chunk_id} result={result} index={index} />
              ))}
              {graphEvidence.length ? (
                <>
                  <div className="flex items-center gap-2 px-1 pt-2">
                    <Network className="size-3.5 text-violet-300" />
                    <p className="text-[11px] font-medium text-slate-200">{t("graphEvidence")}</p>
                  </div>
                  <p className="-mt-1 px-1 text-[9px] leading-relaxed text-muted-2">{t("graphEvidenceHint")}</p>
                  {graphEvidence.map((result, index) => (
                    <SearchResultCard key={result.chunk_id} result={result} index={results.length + index} />
                  ))}
                </>
              ) : null}
              <p className="px-1 text-[9px] leading-relaxed text-muted-2">
                Ranking is fused across vector similarity and full-text search, then reranked. Scores are
                relative, not a legal-confidence measure.
                {graphMode ? ` ${t("graphRankingNote")}` : ""}
              </p>
            </>
          )}
        </div>

        <aside className="space-y-3 xl:col-span-4">
          {graphData && hasQuery ? <GraphContextPanel data={graphData} /> : null}
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
                ["04", "Traverse", "Graph RAG resolves named suppliers, buyers and obligations, then walks up to 3 hops of the supply-chain graph."],
                ["05", "Cite", "Only source text is returned. No answer is synthesized."],
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

"use client";

import {
  ArrowUpRight,
  FileSearch,
  FilterX,
  ListChecks,
  Search,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";

import {
  PriorityBadge,
  StatusBadge,
  VerificationBadge,
} from "@/components/common/badges";
import { PageHeader } from "@/components/common/page-header";
import { ScorePill } from "@/components/common/score-ring";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRisks, useSuppliers } from "@/lib/api/hooks";
import type { RiskFilters, RiskListItem } from "@/lib/api/types";
import { cn, formatRelative, titleCase } from "@/lib/utils";

const priorityOrder = ["critical", "high", "medium", "low"] as const;

function RiskTableRow({ risk }: { risk: RiskListItem }) {
  const router = useRouter();
  return (
    <TableRow
      className="group cursor-pointer border-border-soft/60"
      onClick={() => router.push(`/risks/${risk.id}`)}
      onKeyDown={(event) => {
        if (event.key === "Enter") router.push(`/risks/${risk.id}`);
      }}
      tabIndex={0}
      role="link"
    >
      <TableCell className="py-3.5">
        <div className="max-w-[440px]">
          <p className="line-clamp-1 text-[13px] font-medium text-slate-200 transition-colors group-hover:text-white">
            {risk.title}
          </p>
          <p className="mt-1 line-clamp-1 text-[10px] text-muted-2">
            {risk.obligation_title ?? titleCase(risk.category)} ·{" "}
            {formatRelative(risk.created_at)}
          </p>
        </div>
      </TableCell>
      <TableCell className="hidden xl:table-cell">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-md border border-border bg-white/[0.025] text-[9px] font-semibold text-muted">
            {risk.supplier_name?.slice(0, 2).toUpperCase() ?? "CO"}
          </div>
          <span className="max-w-[150px] truncate text-[11px] text-slate-300">
            {risk.supplier_name ?? "Company-level"}
          </span>
        </div>
      </TableCell>
      <TableCell>
        <ScorePill score={risk.score} priority={risk.priority} />
      </TableCell>
      <TableCell>
        <PriorityBadge priority={risk.priority} />
      </TableCell>
      <TableCell className="hidden lg:table-cell">
        <VerificationBadge status={risk.verification_status} />
      </TableCell>
      <TableCell className="hidden md:table-cell">
        <StatusBadge status={risk.status} />
      </TableCell>
      <TableCell className="hidden sm:table-cell">
        <div className="flex items-center gap-3 text-[10px] text-muted-2">
          <span className="flex items-center gap-1" title={`${risk.evidence_count} evidence items`}>
            <FileSearch className="size-3" />
            {risk.evidence_count}
          </span>
          <span className="flex items-center gap-1" title={`${risk.action_count} actions`}>
            <ListChecks className="size-3" />
            {risk.action_count}
          </span>
        </div>
      </TableCell>
      <TableCell className="w-8">
        <ArrowUpRight className="size-3.5 text-muted-2 opacity-0 transition-all group-hover:translate-x-0.5 group-hover:opacity-100 group-hover:text-accent" />
      </TableCell>
    </TableRow>
  );
}

function RiskMobileCard({ risk }: { risk: RiskListItem }) {
  return (
    <Link
      href={`/risks/${risk.id}`}
      className="block rounded-xl border border-border bg-[#0a1322] p-4 transition-colors hover:border-accent/25"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-1.5">
            <PriorityBadge priority={risk.priority} />
            <VerificationBadge status={risk.verification_status} />
            <StatusBadge status={risk.status} />
          </div>
          <p className="text-sm font-medium leading-snug text-slate-100">{risk.title}</p>
        </div>
        <ScorePill score={risk.score} priority={risk.priority} />
      </div>
      <p className="mt-2 line-clamp-2 text-[11px] leading-relaxed text-muted">{risk.description}</p>
      <div className="mt-3 flex items-center justify-between border-t border-border-soft pt-2.5">
        <span className="text-[10px] text-muted-2">{risk.supplier_name ?? "Company-level"}</span>
        <span className="flex items-center gap-1 text-[9px] text-muted-2">
          <FileSearch className="size-3" /> {risk.evidence_count}
          <span className="mx-1">·</span>
          <ListChecks className="size-3" /> {risk.action_count}
        </span>
      </div>
    </Link>
  );
}

export default function RisksPage() {
  const t = useTranslations("risks");
  const common = useTranslations("common");
  const [search, setSearch] = React.useState("");
  const deferredSearch = React.useDeferredValue(search);
  const [priority, setPriority] = React.useState("all");
  const [status, setStatus] = React.useState("all");
  const [verification, setVerification] = React.useState("all");
  const [supplier, setSupplier] = React.useState("all");
  const [sort, setSort] = React.useState("score");
  const suppliers = useSuppliers();

  const filters: RiskFilters = {
    q: deferredSearch.trim() || undefined,
    priority: priority === "all" ? undefined : priority,
    status: status === "all" ? undefined : status,
    verification_status: verification === "all" ? undefined : verification,
    supplier_id: supplier === "all" ? undefined : supplier,
    sort,
    limit: 100,
  };
  const risks = useRisks(filters);

  const reset = () => {
    setSearch("");
    setPriority("all");
    setStatus("all");
    setVerification("all");
    setSupplier("all");
    setSort("score");
  };

  const activeFilterCount = [
    priority !== "all",
    status !== "all",
    verification !== "all",
    supplier !== "all",
    search.trim().length > 0,
  ].filter(Boolean).length;

  const counts = risks.data?.counts_by_priority ?? {};
  const total = risks.data?.total ?? 0;

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Act · Risk register" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <Link href="/graph">
            <SlidersHorizontal />
            Supply-chain graph
          </Link>
        </Button>
        <Button asChild>
          <Link href="/approvals">
            <ShieldCheck />
            Approvals
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setPriority("all")}
          className={cn(
            "flex h-8 items-center gap-2 rounded-lg border px-3 text-[11px] font-medium transition-colors",
            priority === "all"
              ? "border-accent/30 bg-accent/10 text-teal-200"
              : "border-border bg-white/[0.02] text-muted hover:border-accent/20 hover:text-slate-200",
          )}
        >
          All risks
          <span className="font-mono text-[10px] opacity-70">{total}</span>
        </button>
        {priorityOrder.map((item) => {
          const count = counts[item] ?? 0;
          return (
            <button
              key={item}
              type="button"
              onClick={() => setPriority(item)}
              className={cn(
                "flex h-8 items-center gap-2 rounded-lg border px-3 text-[11px] font-medium transition-colors",
                priority === item
                  ? "border-accent/30 bg-accent/10 text-teal-200"
                  : "border-border bg-white/[0.02] text-muted hover:border-accent/20 hover:text-slate-200",
              )}
            >
              <span
                className={cn(
                  "size-1.5 rounded-full",
                  item === "critical"
                    ? "bg-rose-400"
                    : item === "high"
                      ? "bg-orange-400"
                      : item === "medium"
                        ? "bg-amber-400"
                        : "bg-slate-400",
                )}
              />
              {titleCase(item)}
              <span className="font-mono text-[10px] opacity-70">{count}</span>
            </button>
          );
        })}
        <span className="ml-auto hidden text-[10px] text-muted-2 sm:block">
          {t("newNote")}
        </span>
      </div>

      <div className="panel p-3">
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-[minmax(200px,1.4fr)_repeat(4,minmax(130px,0.7fr))_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-2" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t("searchPlaceholder")}
              className="pl-8"
            />
          </div>
          <Select value={priority} onValueChange={setPriority}>
            <SelectTrigger>
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All priorities</SelectItem>
              {priorityOrder.map((item) => (
                <SelectItem key={item} value={item}>
                  {titleCase(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger>
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {["open", "in_review", "mitigating", "closed"].map((item) => (
                <SelectItem key={item} value={item}>
                  {titleCase(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={verification} onValueChange={setVerification}>
            <SelectTrigger>
              <SelectValue placeholder="Verification" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All verification</SelectItem>
              <SelectItem value="verified">Verified</SelectItem>
              <SelectItem value="needs_review">Needs review</SelectItem>
              <SelectItem value="insufficient_evidence">Insufficient</SelectItem>
            </SelectContent>
          </Select>
          <Select value={supplier} onValueChange={setSupplier}>
            <SelectTrigger>
              <SelectValue placeholder="Supplier" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All suppliers</SelectItem>
              {(suppliers.data ?? []).map((item) => (
                <SelectItem key={item.id} value={item.id}>
                  {item.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex gap-2">
            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger className="min-w-[130px]">
                <SelectValue placeholder="Sort" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="score">Risk score</SelectItem>
                <SelectItem value="created_at">Newest</SelectItem>
                <SelectItem value="updated_at">Recently updated</SelectItem>
                <SelectItem value="priority">Priority</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="ghost"
              size="icon"
              onClick={reset}
              disabled={activeFilterCount === 0}
              title="Clear filters"
            >
              <FilterX />
            </Button>
          </div>
        </div>
        {activeFilterCount > 0 ? (
          <div className="mt-2 flex items-center gap-2 border-t border-border-soft pt-2 text-[10px] text-muted-2">
            <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5">
              {activeFilterCount} active filter{activeFilterCount > 1 ? "s" : ""}
            </span>
            <button type="button" onClick={reset} className="text-accent hover:text-teal-200">
              Reset all
            </button>
          </div>
        ) : null}
      </div>

      {risks.isLoading ? (
        <PageSkeleton cards={0} />
      ) : risks.isError ? (
        <ErrorState error={risks.error} onRetry={() => void risks.refetch()} />
      ) : risks.data && risks.data.items.length === 0 ? (
        <EmptyState
          icon={FileSearch}
          title="No risks match these filters"
          description="Try clearing the filters or running the agent pipeline to ingest new evidence."
          action={
            activeFilterCount > 0 ? (
              <Button variant="secondary" size="sm" onClick={reset}>
                <FilterX />
                Clear filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          <div className="panel hidden overflow-hidden md:block">
            <div className="flex items-center justify-between border-b border-border-soft px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-2">
                  Risk register
                </span>
                <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 font-mono text-[9px] text-muted-2">
                  {risks.data?.items.length ?? 0} of {total}
                </span>
              </div>
              <span className="text-[10px] text-muted-2">Sorted by {titleCase(sort)}</span>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Risk</TableHead>
                  <TableHead className="hidden xl:table-cell">Supplier</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead className="hidden lg:table-cell">Verification</TableHead>
                  <TableHead className="hidden md:table-cell">Status</TableHead>
                  <TableHead className="hidden sm:table-cell">Links</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {risks.data?.items.map((risk) => (
                  <RiskTableRow key={risk.id} risk={risk} />
                ))}
              </TableBody>
            </Table>
          </div>
          <div className="space-y-3 md:hidden">
            {risks.data?.items.map((risk) => (
              <RiskMobileCard key={risk.id} risk={risk} />
            ))}
          </div>
        </>
      )}

      <div className="flex flex-wrap items-center gap-3 text-[10px] text-muted-2">
        <span className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-emerald-400" /> Verified evidence
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-amber-400" /> Needs human review
        </span>
        <span className="ml-auto">{common("notLegalAdvice")}</span>
      </div>
    </div>
  );
}

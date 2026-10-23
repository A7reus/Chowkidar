"use client";

import {
  CheckCircle2,
  ChevronRight,
  Copy,
  FilterX,
  Link2,
  LockKeyhole,
  Search,
  ShieldAlert,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { AccessDenied } from "@/components/common/access-denied";
import { JsonBlock } from "@/components/common/copy";
import { PageHeader } from "@/components/common/page-header";
import { ErrorState, PageSkeleton } from "@/components/common/states";
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
import { useAudit, useAuditVerify } from "@/lib/api/hooks";
import type { AuditEvent, AuditFilters } from "@/lib/api/types";
import { usePermissions } from "@/lib/auth/store";
import { cn, formatDate, formatRelative, humanizeAction, shortHash } from "@/lib/utils";

const actionOptions = [
  "risk.created",
  "risk.status_changed",
  "action.created",
  "action.updated",
  "approval.requested",
  "approval.approved",
  "approval.rejected",
  "pipeline.run",
  "pipeline.failed",
  "source.sync",
  "report.generated",
];

const entityOptions = ["risk", "action", "approval", "source", "report", "agent_run"];

function AuditRow({ event }: { event: AuditEvent }) {
  const [expanded, setExpanded] = React.useState(false);
  return (
    <>
      <TableRow className="cursor-pointer border-border-soft/70" onClick={() => setExpanded((value) => !value)}>
        <TableCell className="whitespace-nowrap">
          <span className="text-[10px] text-slate-300">{formatDate(event.created_at, "dd MMM, HH:mm")}</span>
          <p className="mt-0.5 text-[9px] text-muted-2">{formatRelative(event.created_at)}</p>
        </TableCell>
        <TableCell>
          <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 font-mono text-[9px] text-slate-300">
            {event.action}
          </span>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-1.5">
            <UserRound className="size-3 text-muted-2" />
            <span className="max-w-[190px] truncate text-[10px] text-muted">{event.actor_email}</span>
          </div>
        </TableCell>
        <TableCell>
          <span className="text-[10px] text-muted">{event.entity_type}</span>
          <p className="font-mono text-[8px] text-muted-2">{shortHash(event.entity_id, 10)}</p>
        </TableCell>
        <TableCell className="hidden lg:table-cell">
          <span className="font-mono text-[9px] text-muted-2">{shortHash(event.hash, 16)}</span>
        </TableCell>
        <TableCell className="w-8">
          <ChevronRight className={cn("size-3.5 text-muted-2 transition-transform", expanded && "rotate-90")} />
        </TableCell>
      </TableRow>
      {expanded ? (
        <TableRow className="bg-[#060d18]/70">
          <TableCell colSpan={6} className="p-4">
            <div className="grid gap-3 lg:grid-cols-[1fr_260px]">
              <div>
                <p className="mb-1.5 text-[9px] font-semibold uppercase tracking-wider text-muted-2">
                  Payload
                </p>
                <JsonBlock value={event.payload} maxHeight="13rem" />
              </div>
              <div className="space-y-2">
                <div className="rounded-lg border border-border-soft bg-white/[0.02] p-2.5">
                  <p className="text-[8px] uppercase tracking-wider text-muted-2">Prev hash</p>
                  <p className="mt-1 break-all font-mono text-[9px] text-muted">{event.prev_hash || "genesis"}</p>
                </div>
                <div className="rounded-lg border border-border-soft bg-white/[0.02] p-2.5">
                  <p className="text-[8px] uppercase tracking-wider text-muted-2">Event hash</p>
                  <p className="mt-1 break-all font-mono text-[9px] text-teal-300">{event.hash}</p>
                </div>
                <div className="flex items-center gap-1 text-[8px] text-muted-2">
                  <Link2 className="size-2.5" />
                  Entity {event.entity_id}
                </div>
              </div>
            </div>
          </TableCell>
        </TableRow>
      ) : null}
    </>
  );
}

export default function AuditPage() {
  const t = useTranslations("audit");
  const common = useTranslations("common");
  const { canViewAudit } = usePermissions();
  const [action, setAction] = React.useState("all");
  const [entity, setEntity] = React.useState("all");
  const [actor, setActor] = React.useState("");
  const deferredActor = React.useDeferredValue(actor);

  const filters: AuditFilters = {
    action: action === "all" ? undefined : action,
    entity_type: entity === "all" ? undefined : entity,
    actor_email: deferredActor.trim() || undefined,
    limit: 200,
  };

  const audit = useAudit(filters, canViewAudit);
  const verify = useAuditVerify(canViewAudit);

  if (!canViewAudit) {
    return (
      <div className="space-y-5">
        <PageHeader eyebrow="Governance · Integrity" title={t("title")} description={t("subtitle")} />
        <AccessDenied
          role="admin"
          title={t("adminOnly")}
          body={t("adminOnlyBody")}
          label={t("switchAdmin")}
        />
      </div>
    );
  }

  if (audit.isLoading || verify.isLoading) return <PageSkeleton cards={3} />;
  if (audit.isError) {
    return <ErrorState error={audit.error} onRetry={() => void audit.refetch()} />;
  }

  const verification = verify.data;
  const activeFilters = [action !== "all", entity !== "all", actor.trim().length > 0].filter(Boolean).length;
  const reset = () => {
    setAction("all");
    setEntity("all");
    setActor("");
  };

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Governance · Integrity" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" onClick={() => void verify.refetch()} loading={verify.isFetching}>
          <ShieldCheck />
          {t("verify")}
        </Button>
      </PageHeader>

      <div className="grid gap-3 lg:grid-cols-[1fr_280px]">
        <div
          className={cn(
            "panel relative overflow-hidden p-5",
            verification?.valid ? "border-emerald-400/20" : "border-rose-400/20",
          )}
        >
          <div className="pointer-events-none absolute -right-10 -top-10 size-40 rounded-full bg-emerald-400/[0.04] blur-2xl" />
          <div className="relative flex items-start gap-4">
            <div
              className={cn(
                "flex size-11 shrink-0 items-center justify-center rounded-xl border",
                verification?.valid
                  ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-300"
                  : "border-rose-400/25 bg-rose-400/10 text-rose-300",
              )}
            >
              {verification?.valid ? <ShieldCheck className="size-5" /> : <ShieldAlert className="size-5" />}
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-display text-lg font-semibold text-slate-100">
                  {verification?.valid ? t("verified") : t("broken")}
                </h2>
                <span
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-[9px]",
                    verification?.valid
                      ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-200"
                      : "border-rose-400/20 bg-rose-400/10 text-rose-200",
                  )}
                >
                  SHA-256 hash chain
                </span>
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-muted">{t("explain")}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px] text-muted-2">
                <span>
                  <span className="font-semibold text-slate-300">{verification?.events ?? 0}</span> {t("events")}
                </span>
                {verification?.broken_at ? (
                  <span className="text-rose-300">{t("brokenAt")} #{verification.broken_at}</span>
                ) : null}
                {verification?.reason ? <span className="text-rose-300">{verification.reason}</span> : null}
              </div>
              {verification?.head ? (
                <div className="mt-3 flex items-center gap-2 rounded-lg border border-border-soft bg-white/[0.02] px-2.5 py-2">
                  <span className="text-[9px] uppercase tracking-wider text-muted-2">{t("head")}</span>
                  <span className="truncate font-mono text-[9px] text-teal-300">{verification.head}</span>
                </div>
              ) : null}
            </div>
          </div>
        </div>
        <div className="panel p-5">
          <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">Integrity model</p>
          <div className="mt-3 space-y-2.5">
            {[
              ["Append-only", "Events are inserted, never edited."],
              ["Hash chained", "Each event commits to the previous hash."],
              ["Verifiable", "One click re-computes the full chain."],
            ].map(([title, body]) => (
              <div key={title} className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 size-3 shrink-0 text-emerald-400" />
                <div>
                  <p className="text-[10px] font-medium text-slate-300">{title}</p>
                  <p className="text-[9px] leading-relaxed text-muted-2">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel p-3">
        <div className="grid gap-2 md:grid-cols-[minmax(160px,0.8fr)_minmax(160px,0.8fr)_minmax(220px,1.4fr)_auto]">
          <Select value={action} onValueChange={setAction}>
            <SelectTrigger>
              <SelectValue placeholder="All actions" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All actions</SelectItem>
              {actionOptions.map((item) => (
                <SelectItem key={item} value={item}>
                  {item}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={entity} onValueChange={setEntity}>
            <SelectTrigger>
              <SelectValue placeholder="All entities" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All entities</SelectItem>
              {entityOptions.map((item) => (
                <SelectItem key={item} value={item}>
                  {humanizeAction(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-2" />
            <Input
              value={actor}
              onChange={(event) => setActor(event.target.value)}
              placeholder="Filter by actor email"
              className="pl-8"
            />
          </div>
          <Button variant="ghost" size="icon" onClick={reset} disabled={activeFilters === 0} title="Clear filters">
            <FilterX />
          </Button>
        </div>
      </div>

      <div className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-border-soft px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-2">
              Audit events
            </span>
            <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 font-mono text-[9px] text-muted-2">
              {audit.data?.total ?? 0}
            </span>
          </div>
          <span className="text-[9px] text-muted-2">Newest first</span>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("time")}</TableHead>
              <TableHead>{t("action")}</TableHead>
              <TableHead>{t("actor")}</TableHead>
              <TableHead>{t("entity")}</TableHead>
              <TableHead className="hidden lg:table-cell">{t("hash")}</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {audit.data?.items.map((event) => <AuditRow key={event.id} event={event} />)}
          </TableBody>
        </Table>
        {audit.data && audit.data.items.length === 0 ? (
          <div className="px-4 py-12 text-center text-xs text-muted">{t("empty")}</div>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted-2">
        <LockKeyhole className="size-3" />
        Admin-only view. Every material mutation appends an event.
        <span className="ml-auto flex items-center gap-1">
          <Copy className="size-3" />
          Expand a row to inspect its payload and hash linkage.
        </span>
      </div>
      <p className="px-1 text-[10px] leading-relaxed text-muted-2">{common("notLegalAdvice")}</p>
    </div>
  );
}

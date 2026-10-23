import { ArrowUpRight, ChevronRight } from "lucide-react";
import Link from "next/link";

import { JurisdictionBadge } from "@/components/common/badges";
import { SectionHeading } from "@/components/common/page-header";
import type { Signal } from "@/lib/api/types";
import { cn, formatRelative } from "@/lib/utils";

const severityDot: Record<string, string> = {
  critical: "bg-rose-400",
  high: "bg-orange-400",
  medium: "bg-amber-400",
  low: "bg-slate-400",
};

export function LatestSignals({ signals }: { signals: Signal[] }) {
  return (
    <div className="panel flex h-full flex-col p-5">
      <SectionHeading
        title="Latest signals"
        description="Newest evidence in the workspace"
        action={
          <Link
            href="/signals"
            className="flex items-center gap-1 text-[10px] font-medium text-accent transition-colors hover:text-teal-200"
          >
            View all
            <ArrowUpRight className="size-3" />
          </Link>
        }
      />
      <div className="mt-4 flex-1 space-y-0.5">
        {signals.length === 0 ? (
          <div className="flex min-h-40 items-center justify-center text-xs text-muted">
            No signals ingested yet.
          </div>
        ) : (
          signals.map((signal) => (
            <Link
              key={signal.id}
              href={`/signals?signal=${signal.id}`}
              className="group flex items-start gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-white/[0.03]"
            >
              <span className={cn("mt-1.5 size-1.5 shrink-0 rounded-full", severityDot[signal.severity] ?? severityDot.low)} />
              <div className="min-w-0 flex-1">
                <p className="line-clamp-1 text-[12px] font-medium text-slate-200 transition-colors group-hover:text-white">
                  {signal.title}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-1.5">
                  <span className="truncate text-[9px] text-muted">{signal.source_name}</span>
                  <span className="text-muted-2">·</span>
                  <JurisdictionBadge jurisdiction={signal.jurisdiction} className="h-4 px-1 text-[8px]" />
                  <span className="text-muted-2">·</span>
                  <span className="text-[9px] text-muted-2">{formatRelative(signal.published_at)}</span>
                </div>
              </div>
              <ChevronRight className="mt-1 size-3.5 shrink-0 text-muted-2 transition-transform group-hover:translate-x-0.5 group-hover:text-accent" />
            </Link>
          ))
        )}
      </div>
      <div className="mt-auto flex items-center justify-between border-t border-border-soft pt-3 text-[9px] text-muted-2">
        <span>{signals.length} recent signals</span>
        <span className="flex items-center gap-1">
          <span className="size-1 rounded-full bg-teal-400" />
          evidence-first
        </span>
      </div>
    </div>
  );
}

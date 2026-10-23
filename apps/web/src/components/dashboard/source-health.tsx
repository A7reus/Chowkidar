import { ArrowUpRight, Landmark, Newspaper, Scale, ShieldAlert } from "lucide-react";
import Link from "next/link";

import { SectionHeading } from "@/components/common/page-header";
import type { SourceHealth } from "@/lib/api/types";
import { cn, formatRelative } from "@/lib/utils";

const sourceIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  bd_bank: Landmark,
  eu_eurlex: Scale,
  us_uflpa: ShieldAlert,
  gdelt: Newspaper,
};

export function SourceHealthPanel({ sources }: { sources: SourceHealth[] }) {
  return (
    <div className="panel flex h-full flex-col p-5">
      <SectionHeading
        title="Source health"
        description="Independent streams monitored"
        action={
          <Link
            href="/sources"
            className="flex items-center gap-1 text-[10px] font-medium text-accent transition-colors hover:text-teal-200"
          >
            Manage
            <ArrowUpRight className="size-3" />
          </Link>
        }
      />
      <div className="mt-4 space-y-1.5">
        {sources.map((source) => {
          const Icon = sourceIcons[source.stream_key] ?? Newspaper;
          const healthy = source.status === "healthy";
          return (
            <Link
              key={source.id}
              href="/sources"
              className="group flex items-center gap-3 rounded-lg border border-transparent px-2 py-2.5 transition-colors hover:border-border-soft hover:bg-white/[0.025]"
            >
              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-white/[0.025] text-muted transition-colors group-hover:border-accent/20 group-hover:text-accent">
                <Icon className="size-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <p className="truncate text-[11px] font-medium text-slate-200">{source.name}</p>
                  <span className={cn("size-1.5 shrink-0 rounded-full", healthy ? "bg-emerald-400 live-dot" : "bg-amber-400")} />
                </div>
                <p className="mt-0.5 text-[9px] text-muted-2">
                  {source.jurisdiction} · {source.signal_count} signals
                </p>
              </div>
              <div className="shrink-0 text-right">
                <p className="font-mono text-[9px] text-muted-2">
                  {source.last_synced_at ? formatRelative(source.last_synced_at) : "never"}
                </p>
                <p className="text-[8px] uppercase tracking-wider text-muted-2/70">last sync</p>
              </div>
            </Link>
          );
        })}
      </div>
      <div className="mt-auto flex items-center gap-2 border-t border-border-soft pt-3 text-[9px] text-muted-2">
        <span className="size-1.5 rounded-full bg-emerald-400" />
        {sources.length} streams · scheduled by n8n
      </div>
    </div>
  );
}

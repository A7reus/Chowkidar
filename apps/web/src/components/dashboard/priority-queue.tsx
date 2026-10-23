import { ArrowUpRight, ChevronRight } from "lucide-react";
import Link from "next/link";

import { PriorityBadge, priorityStyle } from "@/components/common/badges";
import { SectionHeading } from "@/components/common/page-header";
import { ScorePill } from "@/components/common/score-ring";
import type { TopRisk } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export function PriorityQueue({ risks }: { risks: TopRisk[] }) {
  return (
    <div className="panel flex h-full flex-col p-5">
      <SectionHeading
        title="Priority queue"
        description="Highest-scoring open risks"
        action={
          <Link
            href="/risks"
            className="flex items-center gap-1 text-[10px] font-medium text-accent transition-colors hover:text-teal-200"
          >
            Register
            <ArrowUpRight className="size-3" />
          </Link>
        }
      />
      <div className="mt-4 flex-1 space-y-1">
        {risks.length === 0 ? (
          <div className="flex h-full min-h-40 items-center justify-center text-xs text-muted">
            No open risks.
          </div>
        ) : (
          risks.map((risk, index) => {
            const style = priorityStyle(risk.priority);
            return (
              <Link
                key={risk.id}
                href={`/risks/${risk.id}`}
                className="group relative flex items-start gap-3 rounded-lg px-2 py-3 transition-colors hover:bg-white/[0.03]"
              >
                <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded border border-border bg-white/[0.02] font-mono text-[9px] text-muted-2">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="line-clamp-2 text-[12px] font-medium leading-snug text-slate-200 transition-colors group-hover:text-white">
                    {risk.title}
                  </p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                    <PriorityBadge priority={risk.priority} />
                    <span className="truncate text-[10px] text-muted">{risk.supplier_name ?? "Company-level"}</span>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <ScorePill score={risk.score} priority={risk.priority} />
                  <ChevronRight className={cn("size-3.5 text-muted-2 transition-transform group-hover:translate-x-0.5", style.text)} />
                </div>
              </Link>
            );
          })
        )}
      </div>
      <div className="mt-3 border-t border-border-soft pt-3">
        <Link
          href="/risks"
          className="flex items-center justify-between rounded-lg px-2 py-1.5 text-[10px] font-medium text-muted transition-colors hover:bg-white/[0.03] hover:text-accent"
        >
          Open the full risk register
          <ChevronRight className="size-3" />
        </Link>
      </div>
    </div>
  );
}

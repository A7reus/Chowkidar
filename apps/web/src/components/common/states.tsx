import { AlertCircle, Inbox, RefreshCw, type LucideIcon } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-white/[0.012] px-6 py-14 text-center",
        className,
      )}
    >
      <div className="mb-3 flex size-11 items-center justify-center rounded-full border border-border bg-panel-2 text-muted">
        <Icon className="size-5" />
      </div>
      <h3 className="font-display text-sm font-semibold text-slate-200">{title}</h3>
      {description ? <p className="mt-1 max-w-sm text-xs leading-relaxed text-muted">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
  className,
}: {
  error?: unknown;
  onRetry?: () => void;
  className?: string;
}) {
  const message =
    error instanceof Error ? error.message : typeof error === "string" ? error : "Something went wrong.";
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-rose-400/20 bg-rose-400/[0.04] px-6 py-12 text-center",
        className,
      )}
    >
      <div className="mb-3 flex size-11 items-center justify-center rounded-full border border-rose-400/25 bg-rose-400/10 text-rose-300">
        <AlertCircle className="size-5" />
      </div>
      <h3 className="font-display text-sm font-semibold text-slate-100">Could not load this view</h3>
      <p className="mt-1 max-w-md text-xs leading-relaxed text-muted">{message}</p>
      {onRetry ? (
        <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw />
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function PageSkeleton({ cards = 4 }: { cards?: number }) {
  return (
    <div className="space-y-5 animate-fade-in">
      <div className="space-y-2">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-3 w-full max-w-xl" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: cards }).map((_, index) => (
          <Skeleton key={index} className="h-32 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Skeleton className="h-80 rounded-xl lg:col-span-2" />
        <Skeleton className="h-80 rounded-xl" />
      </div>
    </div>
  );
}

export function InlineLoading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted">
      <span className="size-3.5 animate-spin rounded-full border-2 border-border border-t-accent" />
      {label}
    </div>
  );
}

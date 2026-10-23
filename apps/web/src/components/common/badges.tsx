import {
  AlertTriangle,
  CheckCircle2,
  CircleDashed,
  Clock3,
  FileText,
  ShieldCheck,
  ShieldQuestion,
  XCircle,
} from "lucide-react";
import * as React from "react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { cn, titleCase } from "@/lib/utils";

const priorityStyles: Record<
  string,
  { variant: BadgeProps["variant"]; dot: string; ring: string; text: string }
> = {
  critical: {
    variant: "danger",
    dot: "bg-rose-400",
    ring: "border-rose-400/30 bg-rose-400/10",
    text: "text-rose-300",
  },
  high: {
    variant: "orange",
    dot: "bg-orange-400",
    ring: "border-orange-400/30 bg-orange-400/10",
    text: "text-orange-300",
  },
  medium: {
    variant: "warning",
    dot: "bg-amber-400",
    ring: "border-amber-400/30 bg-amber-400/10",
    text: "text-amber-300",
  },
  low: {
    variant: "muted",
    dot: "bg-slate-400",
    ring: "border-slate-400/20 bg-slate-400/10",
    text: "text-slate-300",
  },
};

export function PriorityBadge({
  priority,
  showDot = true,
  className,
}: {
  priority: string;
  showDot?: boolean;
  className?: string;
}) {
  const style = priorityStyles[priority] ?? priorityStyles.low;
  return (
    <Badge variant={style.variant} className={className}>
      {showDot ? <span className={cn("size-1.5 rounded-full", style.dot)} /> : null}
      {titleCase(priority)}
    </Badge>
  );
}

export function priorityStyle(priority: string) {
  return priorityStyles[priority] ?? priorityStyles.low;
}

export function VerificationBadge({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  if (status === "verified") {
    return (
      <Badge variant="success" className={className}>
        <ShieldCheck className="size-2.5" />
        Verified
      </Badge>
    );
  }
  if (status === "needs_review") {
    return (
      <Badge variant="warning" className={className}>
        <ShieldQuestion className="size-2.5" />
        Needs review
      </Badge>
    );
  }
  return (
    <Badge variant="muted" className={className}>
      <CircleDashed className="size-2.5" />
      Insufficient
    </Badge>
  );
}

export function verificationIcon(status: string) {
  if (status === "verified") return <CheckCircle2 className="size-4 text-emerald-400" />;
  if (status === "needs_review") return <AlertTriangle className="size-4 text-amber-400" />;
  return <CircleDashed className="size-4 text-slate-400" />;
}

const statusVariants: Record<string, BadgeProps["variant"]> = {
  open: "info",
  in_review: "purple",
  mitigating: "warning",
  closed: "muted",
  draft: "outline",
  pending_approval: "warning",
  approved: "success",
  in_progress: "info",
  done: "success",
  rejected: "danger",
  pending: "warning",
  ready: "success",
  completed: "success",
  failed: "danger",
  running: "info",
  healthy: "success",
  degraded: "warning",
  error: "danger",
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <Badge variant={statusVariants[status] ?? "secondary"} className={className}>
      {titleCase(status)}
    </Badge>
  );
}

export function SeverityBadge({ severity, className }: { severity: string; className?: string }) {
  return <PriorityBadge priority={severity} className={className} />;
}

export function RoleBadge({ role, className }: { role: string; className?: string }) {
  const variant: BadgeProps["variant"] =
    role === "admin" ? "purple" : role === "analyst" ? "info" : role === "approver" ? "success" : "muted";
  return (
    <Badge variant={variant} className={className}>
      {titleCase(role)}
    </Badge>
  );
}

export function SignalTypeBadge({ type, className }: { type: string; className?: string }) {
  const variant: BadgeProps["variant"] =
    type === "regulatory"
      ? "info"
      : type === "sanctions"
        ? "danger"
        : type === "financial_regulatory"
          ? "purple"
          : type === "operational"
            ? "warning"
            : "secondary";
  return (
    <Badge variant={variant} className={className}>
      {titleCase(type)}
    </Badge>
  );
}

export function JurisdictionBadge({ jurisdiction, className }: { jurisdiction: string; className?: string }) {
  const label = jurisdiction === "GLOBAL" ? "Global" : jurisdiction;
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center rounded border border-border bg-white/[0.03] px-1.5 font-mono text-[10px] font-medium tracking-wide text-slate-300",
        className,
      )}
    >
      {label}
    </span>
  );
}

export function VerificationIcon({ status }: { status: string }) {
  if (status === "verified") return <CheckCircle2 className="size-4 text-emerald-400" />;
  if (status === "needs_review") return <AlertTriangle className="size-4 text-amber-400" />;
  return <XCircle className="size-4 text-slate-400" />;
}

export function ApprovalStatusIcon({ status }: { status: string }) {
  if (status === "approved") return <CheckCircle2 className="size-4 text-emerald-400" />;
  if (status === "rejected") return <XCircle className="size-4 text-rose-400" />;
  return <Clock3 className="size-4 text-amber-400" />;
}

export function ReportFormatBadge({ format }: { format: string }) {
  const variant: BadgeProps["variant"] =
    format === "pdf" ? "danger" : format === "json" ? "info" : "purple";
  return (
    <Badge variant={variant}>
      {format === "pdf" ? <FileText className="size-2.5" /> : null}
      {format === "markdown" ? "MD" : format.toUpperCase()}
    </Badge>
  );
}

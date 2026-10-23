"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import {
  Building2,
  Factory,
  FileText,
  Scale,
  ShieldAlert,
} from "lucide-react";
import * as React from "react";

import { cn, titleCase } from "@/lib/utils";

export type SupplyNodeData = {
  label: string;
  kind: "company" | "supplier" | "obligation" | "risk" | "policy";
  detail?: string | null;
  priority?: string | null;
};

export type SupplyNodeType = Node<SupplyNodeData, "supply">;

const kindStyles = {
  company: {
    icon: Building2,
    border: "border-teal-400/35",
    bg: "bg-teal-400/[0.055]",
    iconClass: "border-teal-400/25 bg-teal-400/10 text-teal-300",
    label: "Company",
  },
  supplier: {
    icon: Factory,
    border: "border-border",
    bg: "bg-[#0b1525]",
    iconClass: "border-border bg-white/[0.03] text-slate-300",
    label: "Supplier",
  },
  risk: {
    icon: ShieldAlert,
    border: "border-rose-400/25",
    bg: "bg-[#180d16]",
    iconClass: "border-rose-400/20 bg-rose-400/10 text-rose-300",
    label: "Risk",
  },
  obligation: {
    icon: Scale,
    border: "border-sky-400/25",
    bg: "bg-[#0a1524]",
    iconClass: "border-sky-400/20 bg-sky-400/10 text-sky-300",
    label: "Obligation",
  },
  policy: {
    icon: FileText,
    border: "border-violet-400/25",
    bg: "bg-[#120f22]",
    iconClass: "border-violet-400/20 bg-violet-400/10 text-violet-300",
    label: "Policy",
  },
} as const;

const priorityDot: Record<string, string> = {
  critical: "bg-rose-400",
  high: "bg-orange-400",
  medium: "bg-amber-400",
  low: "bg-slate-400",
};

export function SupplyNode({ data, selected }: NodeProps<SupplyNodeType>) {
  const style = kindStyles[data.kind];
  const Icon = style.icon;
  return (
    <div
      className={cn(
        "w-[196px] rounded-xl border px-3 py-2.5 shadow-xl shadow-black/25 transition-all",
        style.border,
        style.bg,
        selected ? "ring-2 ring-accent/40 ring-offset-2 ring-offset-[#060a12]" : "hover:border-accent/30",
        data.kind === "company" && "w-[218px]",
      )}
    >
      <Handle type="target" position={Position.Left} className="!size-1.5 !border-0 !bg-accent/40" />
      <Handle type="source" position={Position.Right} className="!size-1.5 !border-0 !bg-accent/40" />
      <div className="flex items-start gap-2">
        <div className={cn("mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md border", style.iconClass)}>
          <Icon className="size-3" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-1">
            <span className="text-[8px] font-semibold uppercase tracking-[0.14em] text-muted-2">
              {style.label}
            </span>
            {data.priority ? (
              <span className="flex items-center gap-1 text-[8px] capitalize text-muted">
                <span className={cn("size-1 rounded-full", priorityDot[data.priority] ?? priorityDot.low)} />
                {titleCase(data.priority)}
              </span>
            ) : null}
          </div>
          <p className="mt-0.5 line-clamp-2 text-[11px] font-medium leading-snug text-slate-100">
            {data.label}
          </p>
          {data.detail ? (
            <p className="mt-1 line-clamp-1 text-[8.5px] text-muted-2">{data.detail}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export const nodeTypes = { supply: SupplyNode };

export const edgeColors = {
  company: "#2dd4bf",
  supplier: "#3b506e",
  risk: "#7f3f52",
  obligation: "#31577c",
  policy: "#4c3c70",
} as const;

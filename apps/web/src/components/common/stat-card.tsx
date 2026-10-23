import type { LucideIcon } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

const tones = {
  teal: {
    icon: "border-teal-400/20 bg-teal-400/10 text-teal-300",
    bar: "#2dd4bf",
    glow: "from-teal-400/[0.07]",
  },
  rose: {
    icon: "border-rose-400/20 bg-rose-400/10 text-rose-300",
    bar: "#fb7185",
    glow: "from-rose-400/[0.08]",
  },
  amber: {
    icon: "border-amber-400/20 bg-amber-400/10 text-amber-300",
    bar: "#fbbf24",
    glow: "from-amber-400/[0.07]",
  },
  sky: {
    icon: "border-sky-400/20 bg-sky-400/10 text-sky-300",
    bar: "#38bdf8",
    glow: "from-sky-400/[0.07]",
  },
  violet: {
    icon: "border-violet-400/20 bg-violet-400/10 text-violet-300",
    bar: "#a78bfa",
    glow: "from-violet-400/[0.07]",
  },
} satisfies Record<string, { icon: string; bar: string; glow: string }>;

export type StatTone = keyof typeof tones;

function Sparkline({ values, color }: { values: number[]; color: string }) {
  if (!values.length) return null;
  const width = 92;
  const height = 28;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(1, values.length - 1)) * width;
      const y = height - 3 - ((value - min) / span) * (height - 7);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = values[values.length - 1];
  const lastY = height - 3 - ((last - min) / span) * (height - 7);
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.8"
      />
      <circle cx={width} cy={lastY} r="2.2" fill={color} />
    </svg>
  );
}

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "teal",
  trend,
  className,
  children,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  icon: LucideIcon;
  tone?: StatTone;
  trend?: number[];
  className?: string;
  children?: React.ReactNode;
}) {
  const style = tones[tone];
  return (
    <div className={cn("panel relative overflow-hidden p-5", className)}>
      <div
        className={cn(
          "pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b to-transparent",
          style.glow,
        )}
      />
      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-2">{label}</p>
          <div className="mt-2 font-display text-3xl font-semibold tracking-tight text-slate-50">
            {value}
          </div>
        </div>
        <div className={cn("flex size-9 items-center justify-center rounded-lg border", style.icon)}>
          <Icon className="size-4" />
        </div>
      </div>
      <div className="relative mt-3 flex items-end justify-between gap-2">
        <div className="text-[11px] leading-relaxed text-muted">{hint}</div>
        {trend && trend.length > 1 ? <Sparkline values={trend} color={style.bar} /> : null}
      </div>
      {children}
    </div>
  );
}

"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatDate } from "@/lib/utils";
import type { DashboardSummary } from "@/lib/api/types";

type TrendTooltipProps = {
  active?: boolean;
  label?: string;
  payload?: Array<{ dataKey?: string | number; value?: number; color?: string }>;
};

function TrendTooltip({ active, label, payload }: TrendTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-2">
        {label ? formatDate(label, "dd MMM yyyy") : ""}
      </p>
      <div className="space-y-1.5">
        {payload.map((item) => (
          <div key={String(item.dataKey)} className="flex items-center gap-2 text-xs">
            <span className="size-1.5 rounded-full" style={{ background: item.color }} />
            <span className="capitalize text-muted">{String(item.dataKey)}</span>
            <span className="ml-auto font-mono font-semibold text-slate-100">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function RiskTrendChart({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="mt-4 h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={summary.trend} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="openGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.26} />
              <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="highGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fb7185" stopOpacity={0.24} />
              <stop offset="100%" stopColor="#fb7185" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={(value) => formatDate(String(value), "dd MMM")}
            axisLine={false}
            tickLine={false}
            dy={8}
          />
          <YAxis allowDecimals={false} axisLine={false} tickLine={false} width={34} />
          <Tooltip content={<TrendTooltip />} cursor={{ stroke: "#334155", strokeDasharray: "4 4" }} />
          <Area
            type="monotone"
            dataKey="open"
            stroke="#2dd4bf"
            strokeWidth={2}
            fill="url(#openGradient)"
            dot={false}
            activeDot={{ r: 4, fill: "#2dd4bf", stroke: "#06111e", strokeWidth: 2 }}
          />
          <Area
            type="monotone"
            dataKey="high"
            stroke="#fb7185"
            strokeWidth={2}
            fill="url(#highGradient)"
            dot={false}
            activeDot={{ r: 4, fill: "#fb7185", stroke: "#06111e", strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

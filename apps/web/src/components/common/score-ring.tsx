import { cn } from "@/lib/utils";

const colors: Record<string, string> = {
  critical: "#fb7185",
  high: "#fb923c",
  medium: "#fbbf24",
  low: "#94a3b8",
};

export function ScoreRing({
  score,
  priority,
  size = 112,
  stroke = 8,
  className,
  showLabel = true,
}: {
  score: number;
  priority: string;
  size?: number;
  stroke?: number;
  className?: string;
  showLabel?: boolean;
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference - (clamped / 100) * circumference;
  const color = colors[priority] ?? colors.low;
  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(148,163,184,0.12)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ filter: `drop-shadow(0 0 6px ${color}55)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-display text-2xl font-semibold tracking-tight"
          style={{ color }}
        >
          {Number.isInteger(score) ? score : score.toFixed(1)}
        </span>
        {showLabel ? (
          <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-2">
            risk score
          </span>
        ) : null}
      </div>
    </div>
  );
}

export function ScorePill({ score, priority }: { score: number; priority: string }) {
  const color = colors[priority] ?? colors.low;
  return (
    <span
      className="inline-flex min-w-12 items-center justify-center rounded-md border px-2 py-1 font-mono text-xs font-semibold"
      style={{
        color,
        borderColor: `${color}44`,
        background: `${color}12`,
      }}
    >
      {Number.isInteger(score) ? score : score.toFixed(1)}
    </span>
  );
}

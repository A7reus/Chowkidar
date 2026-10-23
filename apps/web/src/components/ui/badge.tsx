import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] transition-colors",
  {
    variants: {
      variant: {
        default: "border-accent/25 bg-accent/10 text-teal-300",
        secondary: "border-border bg-white/[0.035] text-slate-300",
        outline: "border-border bg-transparent text-muted",
        success: "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
        warning: "border-amber-400/25 bg-amber-400/10 text-amber-300",
        danger: "border-rose-400/25 bg-rose-400/10 text-rose-300",
        orange: "border-orange-400/25 bg-orange-400/10 text-orange-300",
        info: "border-sky-400/25 bg-sky-400/10 text-sky-300",
        purple: "border-violet-400/25 bg-violet-400/10 text-violet-300",
        muted: "border-slate-500/20 bg-slate-500/10 text-slate-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };

import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-9.5 w-full rounded-lg border border-border bg-[#08111f]/80 px-3 py-2 text-sm text-slate-100 shadow-inner shadow-black/20 transition-colors placeholder:text-muted-2 focus:border-accent/45 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };

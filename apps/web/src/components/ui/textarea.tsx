import * as React from "react";

import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    className={cn(
      "flex min-h-24 w-full rounded-lg border border-border bg-[#08111f]/80 px-3 py-2 text-sm text-slate-100 shadow-inner shadow-black/20 transition-colors placeholder:text-muted-2 focus:border-accent/45 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    ref={ref}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export { Textarea };

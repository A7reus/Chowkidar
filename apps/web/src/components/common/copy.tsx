"use client";

import { Check, Copy } from "lucide-react";
import * as React from "react";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function CopyButton({
  value,
  label = "Copy",
  className,
}: {
  value: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = React.useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      toast.error("Could not copy to clipboard.");
    }
  };
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      className={cn("text-muted hover:text-white", className)}
      onClick={copy}
      title={label}
      type="button"
    >
      {copied ? <Check className="text-emerald-400" /> : <Copy />}
    </Button>
  );
}

export function JsonBlock({
  value,
  className,
  maxHeight = "18rem",
}: {
  value: unknown;
  className?: string;
  maxHeight?: string;
}) {
  const text = JSON.stringify(value, null, 2);
  return (
    <div className={cn("relative overflow-hidden rounded-lg border border-border bg-[#060d18]", className)}>
      <div className="absolute right-2 top-2 z-10">
        <CopyButton value={text} label="Copy JSON" />
      </div>
      <pre
        className="overflow-auto p-3 pr-10 font-mono text-[11px] leading-relaxed text-slate-300 scrollbar-thin"
        style={{ maxHeight }}
      >
        {text}
      </pre>
    </div>
  );
}

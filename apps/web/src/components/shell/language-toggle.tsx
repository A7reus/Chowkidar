"use client";

import { Languages } from "lucide-react";
import { useLocale } from "next-intl";
import * as React from "react";

import { cn } from "@/lib/utils";

function persistLocale(locale: "en" | "bn") {
  document.cookie = `NEXT_LOCALE=${locale}; path=/; max-age=31536000; samesite=lax`;
  window.location.reload();
}

export function LanguageToggle({ className }: { className?: string }) {
  const locale = useLocale();
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-lg border border-border bg-[#08111f]/80 p-0.5",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => persistLocale("en")}
        className={cn(
          "rounded-md px-2 py-1 text-[10px] font-semibold uppercase tracking-wider transition-colors",
          locale === "en" ? "bg-white/[0.08] text-white" : "text-muted hover:text-slate-200",
        )}
        aria-pressed={locale === "en"}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => persistLocale("bn")}
        className={cn(
          "rounded-md px-2 py-1 text-[10px] font-semibold transition-colors",
          locale === "bn" ? "bg-white/[0.08] text-white" : "text-muted hover:text-slate-200",
        )}
        aria-pressed={locale === "bn"}
      >
        বাংলা
      </button>
    </div>
  );
}

export function ToggleLanguageItem() {
  const locale = useLocale();
  return (
    <button
      type="button"
      className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-slate-200 outline-none transition-colors hover:bg-white/[0.06]"
      onClick={() => persistLocale(locale === "en" ? "bn" : "en")}
    >
      <Languages className="size-4 text-muted" />
      {locale === "en" ? "বাংলায় দেখুন" : "View in English"}
    </button>
  );
}

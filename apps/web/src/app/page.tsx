"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { useAuthStore } from "@/lib/auth/store";

export default function Home() {
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const hydrated = useAuthStore((state) => state.hydrated);

  React.useEffect(() => {
    if (!hydrated) return;
    router.replace(token ? "/dashboard" : "/login");
  }, [hydrated, router, token]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="relative flex size-14 items-center justify-center rounded-2xl border border-accent/25 bg-accent/10 text-accent">
          <span className="absolute inset-0 animate-ping rounded-2xl border border-accent/20" />
          <span className="font-display text-xl font-semibold">C</span>
        </div>
        <p className="text-xs uppercase tracking-[0.24em] text-muted">Chowkidar</p>
      </div>
    </div>
  );
}

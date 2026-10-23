"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { useAuthStore } from "@/lib/auth/store";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const hydrated = useAuthStore((state) => state.hydrated);
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  React.useEffect(() => {
    if (!hydrated) return;
    if (!token || !user) {
      if (token && !user) logout();
      router.replace("/login");
    }
  }, [hydrated, logout, router, token, user]);

  if (!hydrated || !token || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center grid-bg">
        <div className="flex flex-col items-center gap-5">
          <div className="relative flex size-16 items-center justify-center rounded-2xl border border-accent/25 bg-accent/10">
            <span className="absolute inset-0 animate-ping rounded-2xl border border-accent/20" />
            <span className="font-display text-2xl font-semibold text-accent">C</span>
          </div>
          <div className="text-center">
            <p className="font-display text-sm font-semibold text-slate-100">Chowkidar</p>
            <p className="mt-1 text-[10px] uppercase tracking-[0.22em] text-muted">
              Preparing your risk workspace
            </p>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

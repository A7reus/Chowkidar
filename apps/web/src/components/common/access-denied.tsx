"use client";

import { LockKeyhole, ShieldAlert } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth/store";
import type { Role } from "@/lib/api/types";
import { cn } from "@/lib/utils";

function useSwitchRole() {
  const switchRole = useAuthStore((state) => state.switchRole);
  const isDemo = useAuthStore((state) => Boolean(state.user?.is_demo));
  const [loading, setLoading] = React.useState(false);
  const change = async (role: Role) => {
    setLoading(true);
    try {
      await switchRole(role);
      window.location.reload();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not switch demo role.");
      setLoading(false);
    }
  };
  return { change, loading, isDemo };
}

export function AccessDenied({
  role,
  title,
  body,
  label,
  className,
}: {
  role: Role;
  title: string;
  body: string;
  label: string;
  className?: string;
}) {
  const { change, loading, isDemo } = useSwitchRole();
  return (
    <div
      className={cn(
        "panel flex flex-col items-center justify-center px-6 py-16 text-center",
        className,
      )}
    >
      <div className="mb-4 flex size-12 items-center justify-center rounded-full border border-amber-400/25 bg-amber-400/10 text-amber-300">
        <LockKeyhole className="size-5" />
      </div>
      <h2 className="font-display text-lg font-semibold text-slate-100">{title}</h2>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-muted">{body}</p>
      {isDemo ? (
        <Button className="mt-5" onClick={() => change(role)} loading={loading}>
          <ShieldAlert />
          {label}
        </Button>
      ) : (
        <p className="mt-4 text-[10px] text-muted-2">
          Access is managed by a workspace administrator.
        </p>
      )}
    </div>
  );
}

export function RoleHint({
  role,
  title,
  body,
  label,
  className,
}: {
  role: Role;
  title: string;
  body: string;
  label: string;
  className?: string;
}) {
  const { change, loading, isDemo } = useSwitchRole();
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-amber-400/20 bg-amber-400/[0.045] p-4 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border border-amber-400/20 bg-amber-400/10 text-amber-300">
          <LockKeyhole className="size-4" />
        </div>
        <div>
          <p className="text-sm font-medium text-slate-100">{title}</p>
          <p className="mt-0.5 text-xs leading-relaxed text-muted">{body}</p>
        </div>
      </div>
      {isDemo ? (
        <Button variant="secondary" size="sm" onClick={() => change(role)} loading={loading}>
          {label}
        </Button>
      ) : (
        <span className="shrink-0 text-[10px] text-muted-2">Managed by an administrator</span>
      )}
    </div>
  );
}

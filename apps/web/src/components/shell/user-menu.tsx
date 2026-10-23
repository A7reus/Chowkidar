"use client";

import {
  BarChart3,
  Check,
  ChevronDown,
  Eye,
  LogOut,
  Shield,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { RoleBadge } from "@/components/common/badges";
import { ToggleLanguageItem } from "@/components/shell/language-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { Role } from "@/lib/api/types";
import { useAuthStore, usePermissions } from "@/lib/auth/store";
import { initials } from "@/lib/utils";

const roleIcons = {
  admin: Shield,
  analyst: BarChart3,
  approver: ShieldCheck,
  viewer: Eye,
} as const;

const roleLabels: Record<Role, string> = {
  admin: "Admin",
  analyst: "Analyst",
  approver: "Approver",
  viewer: "Viewer",
};

export function UserMenu({ variant = "sidebar" }: { variant?: "sidebar" | "topbar" }) {
  const t = useTranslations("common");
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const switchRole = useAuthStore((state) => state.switchRole);
  const logout = useAuthStore((state) => state.logout);
  const { role } = usePermissions();
  const [switching, setSwitching] = React.useState<Role | null>(null);

  const changeRole = async (nextRole: Role) => {
    if (nextRole === role) return;
    setSwitching(nextRole);
    try {
      await switchRole(nextRole);
      toast.success(`Demo role switched to ${roleLabels[nextRole]}.`);
      window.setTimeout(() => window.location.reload(), 350);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not switch role.");
      setSwitching(null);
    }
  };

  const signOut = () => {
    logout();
    router.replace("/login");
  };

  if (!user) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {variant === "sidebar" ? (
          <button
            type="button"
            className="group flex w-full items-center gap-2.5 rounded-xl border border-border bg-[#08111f]/70 p-2.5 text-left transition-colors hover:border-accent/25 hover:bg-[#0c1728]"
          >
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-accent/20 bg-gradient-to-br from-teal-400/20 to-sky-400/10 font-display text-xs font-semibold text-teal-200">
              {initials(user.name)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-slate-100">{user.name}</p>
              <p className="truncate text-[10px] capitalize text-muted">{user.role}</p>
            </div>
            <ChevronDown className="size-3.5 text-muted transition-transform group-data-[state=open]:rotate-180" />
          </button>
        ) : (
          <button
            type="button"
            className="flex size-8 items-center justify-center rounded-full border border-accent/20 bg-gradient-to-br from-teal-400/20 to-sky-400/10 font-display text-[10px] font-semibold text-teal-200 transition-transform hover:scale-105"
            aria-label="Open user menu"
          >
            {initials(user.name)}
          </button>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align={variant === "sidebar" ? "start" : "end"}
        side={variant === "sidebar" ? "top" : "bottom"}
        className="w-64"
      >
        <DropdownMenuLabel>Signed in as</DropdownMenuLabel>
        <div className="flex items-center gap-2.5 px-2 pb-2 pt-1">
          <div className="flex size-9 items-center justify-center rounded-lg border border-accent/20 bg-teal-400/10 font-display text-xs font-semibold text-teal-200">
            {initials(user.name)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-100">{user.name}</p>
            <p className="truncate text-[10px] text-muted">{user.email}</p>
          </div>
          <RoleBadge role={user.role} />
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuLabel>{t("switchRole")}</DropdownMenuLabel>
        {(Object.keys(roleIcons) as Role[]).map((item) => {
          const Icon = roleIcons[item];
          return (
            <DropdownMenuItem
              key={item}
              disabled={switching !== null}
              onSelect={(event) => {
                event.preventDefault();
                void changeRole(item);
              }}
              className="justify-between"
            >
              <span className="flex items-center gap-2">
                <Icon className="size-4 text-muted" />
                {roleLabels[item]}
                {switching === item ? (
                  <span className="size-3 animate-spin rounded-full border border-border border-t-accent" />
                ) : null}
              </span>
              {item === role ? <Check className="size-3.5 text-accent" /> : null}
            </DropdownMenuItem>
          );
        })}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={(event) => event.preventDefault()} className="p-0">
          <ToggleLanguageItem />
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={signOut} className="text-rose-300 focus:text-rose-200">
          <LogOut className="size-4 text-rose-300" />
          {t("signOut")}
        </DropdownMenuItem>
        {variant === "topbar" ? (
          <div className="flex items-center gap-2 px-2 py-2 text-[10px] text-muted-2">
            <UserRound className="size-3" />
            Demo accounts are seeded and fictional.
          </div>
        ) : null}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

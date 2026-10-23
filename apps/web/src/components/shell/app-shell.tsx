"use client";

import {
  Activity,
  ArrowUpRight,
  BadgeCheck,
  Bell,
  Building2,
  ChevronRight,
  Database,
  FileText,
  FlaskConical,
  LayoutDashboard,
  ListChecks,
  Lock,
  Menu,
  Network,
  Radio,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";

import { LanguageToggle } from "@/components/shell/language-toggle";
import { UserMenu } from "@/components/shell/user-menu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_URL } from "@/lib/api/client";
import { useHealth, useMeta, usePendingApprovalCount } from "@/lib/api/hooks";
import { useAuthStore, usePermissions } from "@/lib/auth/store";
import { cn } from "@/lib/utils";

type NavItem = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  locked?: boolean;
  badge?: number;
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations("nav");
  const common = useTranslations("common");
  const pathname = usePathname();
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const { canViewAudit, canViewEvals } = usePermissions();
  const meta = useMeta();
  const health = useHealth();
  const pending = usePendingApprovalCount(Boolean(token));
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const searchRef = React.useRef<HTMLInputElement>(null);

  const navGroups: Array<{ label: string; items: NavItem[] }> = [
    {
      label: t("overview"),
      items: [{ href: "/dashboard", label: t("dashboard"), icon: LayoutDashboard }],
    },
    {
      label: t("monitor"),
      items: [
        { href: "/signals", label: t("signals"), icon: Radio },
        { href: "/sources", label: t("sources"), icon: Database },
      ],
    },
    {
      label: t("act"),
      items: [
        { href: "/risks", label: t("risks"), icon: ShieldCheck },
        {
          href: "/approvals",
          label: t("approvals"),
          icon: ListChecks,
          badge: pending.data?.count ?? 0,
        },
        { href: "/reports", label: t("reports"), icon: FileText },
      ],
    },
    {
      label: t("intelligence"),
      items: [
        { href: "/graph", label: t("graph"), icon: Network },
        { href: "/search", label: t("search"), icon: Search },
        {
          href: "/evals",
          label: t("evals"),
          icon: FlaskConical,
          locked: !canViewEvals,
        },
      ],
    },
    {
      label: t("governance"),
      items: [
        {
          href: "/audit",
          label: t("audit"),
          icon: BadgeCheck,
          locked: !canViewAudit,
        },
      ],
    },
  ];

  const flatItems = navGroups.flatMap((group) => group.items.map((item) => ({ ...item, group: group.label })));
  const current = flatItems.find((item) =>
    item.href === "/dashboard" ? pathname === "/dashboard" : pathname === item.href || pathname.startsWith(`${item.href}/`),
  );

  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- close the mobile drawer after navigation
    setMobileOpen(false);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname]);

  React.useEffect(() => {
    document.title = current ? `${current.label} · Chowkidar` : "Chowkidar";
  }, [current]);

  React.useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const value = query.trim();
    if (value.length < 2) return;
    router.push(`/search?q=${encodeURIComponent(value)}`);
    setQuery("");
  };

  const online = health.data?.status === "ok";
  const companyName = meta.data?.company.name ?? "Padma Apparel Ltd.";
  const companyLocation = meta.data?.company.location ?? "Gazipur, Bangladesh";

  const sidebar = (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex w-[268px] flex-col border-r border-border bg-[#070d17]/98 backdrop-blur-xl transition-transform duration-300 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
        mobileOpen ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <div className="flex items-center justify-between px-5 pb-4 pt-5">
        <Link href="/dashboard" className="group flex items-center gap-2.5">
          <div className="relative flex size-9 items-center justify-center rounded-xl border border-accent/30 bg-gradient-to-br from-teal-400/20 to-sky-400/5 text-accent shadow-[0_0_25px_-8px_rgba(45,212,191,0.6)]">
            <ShieldCheck className="size-4.5" />
          </div>
          <div>
            <p className="font-display text-[15px] font-semibold tracking-tight text-white">Chowkidar</p>
            <p className="text-[9px] uppercase tracking-[0.18em] text-muted-2">See the risk · approve the fix</p>
          </div>
        </Link>
        <button
          type="button"
          onClick={() => setMobileOpen(false)}
          className="rounded-md p-1 text-muted hover:bg-white/[0.05] hover:text-white lg:hidden"
          aria-label="Close navigation"
        >
          <X className="size-4" />
        </button>
      </div>

      <div className="px-4 pb-4">
        <div className="relative overflow-hidden rounded-xl border border-border bg-gradient-to-br from-[#0c1728] to-[#08101d] p-3">
          <div className="pointer-events-none absolute -right-6 -top-6 size-20 rounded-full bg-teal-400/10 blur-2xl" />
          <div className="flex items-start gap-2.5">
            <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg border border-border bg-white/[0.03] text-muted">
              <Building2 className="size-3.5" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs font-medium text-slate-100">{companyName}</p>
              <p className="mt-0.5 truncate text-[10px] text-muted">{companyLocation}</p>
              <div className="mt-2 flex items-center gap-1.5">
                <span className="inline-flex items-center gap-1 rounded border border-teal-400/20 bg-teal-400/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider text-teal-300">
                  <span className="size-1 rounded-full bg-teal-300" />
                  Demo
                </span>
                <span className="text-[9px] text-muted-2">EU + US buyers</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-4 scrollbar-thin">
        <div className="space-y-5">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="mb-1.5 px-2.5 text-[9px] font-semibold uppercase tracking-[0.18em] text-muted-2">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const active =
                    item.href === "/dashboard"
                      ? pathname === "/dashboard"
                      : pathname === item.href || pathname.startsWith(`${item.href}/`);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[12.5px] font-medium transition-all",
                        active
                          ? "bg-accent/[0.09] text-white"
                          : "text-muted hover:bg-white/[0.035] hover:text-slate-200",
                      )}
                    >
                      {active ? (
                        <span className="absolute -left-3 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r bg-accent shadow-[0_0_12px_rgba(45,212,191,0.8)]" />
                      ) : null}
                      <Icon
                        className={cn(
                          "size-4 transition-colors",
                          active ? "text-accent" : "text-muted-2 group-hover:text-slate-300",
                        )}
                      />
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.locked ? <Lock className="size-3 text-muted-2" /> : null}
                      {item.badge ? (
                        <span className="flex min-w-4 items-center justify-center rounded-full border border-amber-400/25 bg-amber-400/15 px-1.5 py-0.5 text-[9px] font-semibold text-amber-200">
                          {item.badge}
                        </span>
                      ) : null}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </nav>

      <div className="border-t border-border-soft p-3">
        <div className="mb-3 flex items-center justify-between rounded-lg border border-border-soft bg-white/[0.015] px-2.5 py-2">
          <div className="flex items-center gap-1.5 text-[9px] uppercase tracking-wider text-muted-2">
            <Sparkles className="size-3 text-accent/70" />
            Agent ready
          </div>
          <span className="font-mono text-[9px] text-muted-2">mock</span>
        </div>
        <div className="mb-2.5 flex items-center justify-between gap-2">
          <LanguageToggle />
          <a
            href={`${API_URL}/docs`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-[10px] text-muted transition-colors hover:text-accent"
          >
            API docs
            <ArrowUpRight className="size-3" />
          </a>
        </div>
        <UserMenu />
        <p className="mt-2.5 px-1 text-[9px] leading-relaxed text-muted-2">
          {common("notLegalAdvice")}
        </p>
      </div>
    </aside>
  );

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[268px_minmax(0,1fr)]">
      {mobileOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation overlay"
        />
      ) : null}
      {sidebar}

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-[#060a12]/85 px-3 backdrop-blur-xl sm:px-5">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu />
          </Button>

          <div className="hidden min-w-0 items-center gap-1.5 text-[11px] text-muted md:flex">
            <span className="text-muted-2">{current?.group ?? "Workspace"}</span>
            <ChevronRight className="size-3 text-muted-2" />
            <span className="truncate font-medium text-slate-300">{current?.label ?? "Overview"}</span>
          </div>

          <form onSubmit={submitSearch} className="relative ml-auto w-full max-w-[320px]">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-2" />
            <Input
              ref={searchRef}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search risks, signals, evidence…"
              className="h-8.5 border-border-soft bg-white/[0.025] pl-8 pr-14 text-xs focus:bg-white/[0.04]"
              aria-label="Global search"
            />
            <kbd className="pointer-events-none absolute right-2 top-1/2 hidden -translate-y-1/2 rounded border border-border bg-white/[0.03] px-1.5 py-0.5 font-mono text-[9px] text-muted-2 sm:block">
              ⌘K
            </kbd>
          </form>

          <div className="hidden items-center gap-1.5 rounded-full border border-border-soft bg-white/[0.02] px-2.5 py-1 xl:flex">
            <Activity className={cn("size-3", online ? "text-emerald-400" : "text-rose-400")} />
            <span className="text-[10px] text-muted">{online ? "API online" : health.isLoading ? "Checking" : "API offline"}</span>
            <span className="font-mono text-[9px] uppercase text-muted-2">{health.data?.llm_mode ?? "—"}</span>
          </div>

          <Link
            href="/approvals"
            className="relative flex size-8.5 items-center justify-center rounded-lg border border-transparent text-muted transition-colors hover:border-border hover:bg-white/[0.03] hover:text-white"
            aria-label="Pending approvals"
          >
            <Bell className="size-4" />
            {pending.data?.count ? (
              <span className="absolute -right-0.5 -top-0.5 flex size-4 items-center justify-center rounded-full bg-amber-400 text-[9px] font-bold text-slate-950">
                {pending.data.count}
              </span>
            ) : null}
          </Link>

          <UserMenu variant="topbar" />
        </header>

        <main key={pathname} className="mx-auto w-full max-w-[1600px] flex-1 animate-fade-in px-4 py-6 sm:px-6 lg:px-8 lg:py-7">
          {children}
        </main>

        <footer className="mx-auto flex w-full max-w-[1600px] flex-col gap-1 border-t border-border-soft px-4 py-4 text-[10px] text-muted-2 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <span>Chowkidar · Compliance risk intelligence for export supply chains.</span>
          <span className="flex items-center gap-1.5">
            <span className="size-1 rounded-full bg-teal-400" />
            Demo workspace · fictional data · not legal advice
          </span>
        </footer>
      </div>
    </div>
  );
}

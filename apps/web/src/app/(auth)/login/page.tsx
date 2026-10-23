"use client";

import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Building2,
  Check,
  ChevronRight,
  Eye,
  FileCheck2,
  Fingerprint,
  Globe2,
  Loader2,
  LockKeyhole,
  ScanSearch,
  Shield,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { LanguageToggle } from "@/components/shell/language-toggle";
import type { Role } from "@/lib/api/types";
import { useAuthStore } from "@/lib/auth/store";
import { cn } from "@/lib/utils";

const roles: Array<{
  role: Role;
  name: string;
  email: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
  iconClass: string;
  descriptionKey: "adminDesc" | "analystDesc" | "approverDesc" | "viewerDesc";
  labelKey: "admin" | "analyst" | "approver" | "viewer";
}> = [
  {
    role: "admin",
    name: "Ayesha Rahman",
    email: "admin@chowkidar.demo",
    icon: Shield,
    accent: "hover:border-violet-400/40 hover:bg-violet-400/[0.035]",
    iconClass: "border-violet-400/25 bg-violet-400/10 text-violet-300",
    descriptionKey: "adminDesc",
    labelKey: "admin",
  },
  {
    role: "analyst",
    name: "Rafiq Hasan",
    email: "analyst@chowkidar.demo",
    icon: BarChart3,
    accent: "hover:border-sky-400/40 hover:bg-sky-400/[0.035]",
    iconClass: "border-sky-400/25 bg-sky-400/10 text-sky-300",
    descriptionKey: "analystDesc",
    labelKey: "analyst",
  },
  {
    role: "approver",
    name: "Nusrat Jahan",
    email: "approver@chowkidar.demo",
    icon: BadgeCheck,
    accent: "hover:border-teal-400/40 hover:bg-teal-400/[0.035]",
    iconClass: "border-teal-400/25 bg-teal-400/10 text-teal-300",
    descriptionKey: "approverDesc",
    labelKey: "approver",
  },
  {
    role: "viewer",
    name: "Imran Chowdhury",
    email: "viewer@chowkidar.demo",
    icon: Eye,
    accent: "hover:border-slate-400/40 hover:bg-slate-400/[0.035]",
    iconClass: "border-slate-400/25 bg-slate-400/10 text-slate-300",
    descriptionKey: "viewerDesc",
    labelKey: "viewer",
  },
];

const flow = [
  { icon: ScanSearch, label: "Ingest" },
  { icon: FileCheck2, label: "Extract" },
  { icon: Waypoints, label: "Map" },
  { icon: Fingerprint, label: "Verify" },
];

export default function LoginPage() {
  const t = useTranslations("login");
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const hydrated = useAuthStore((state) => state.hydrated);
  const login = useAuthStore((state) => state.login);
  const loggingIn = useAuthStore((state) => state.loggingIn);
  const [selected, setSelected] = React.useState<Role | null>(null);

  React.useEffect(() => {
    if (hydrated && token) router.replace("/dashboard");
  }, [hydrated, router, token]);

  const handleLogin = async (role: Role) => {
    setSelected(role);
    try {
      await login(role);
      router.replace("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not sign in to the demo.");
      setSelected(null);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-[0.55]" />
      <div className="pointer-events-none absolute -left-40 top-0 size-[560px] rounded-full bg-teal-400/[0.055] blur-3xl" />
      <div className="pointer-events-none absolute -right-40 bottom-0 size-[620px] rounded-full bg-sky-400/[0.05] blur-3xl" />
      <div className="pointer-events-none absolute left-1/2 top-1/3 size-[360px] -translate-x-1/2 rounded-full bg-violet-400/[0.035] blur-3xl" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-[1400px] flex-col px-5 py-5 sm:px-8 lg:px-10">
        <header className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-xl border border-accent/30 bg-gradient-to-br from-teal-400/20 to-sky-400/5 text-accent shadow-[0_0_25px_-8px_rgba(45,212,191,0.6)]">
              <ShieldCheck className="size-4.5" />
            </div>
            <div>
              <p className="font-display text-[15px] font-semibold tracking-tight text-white">Chowkidar</p>
              <p className="text-[9px] uppercase tracking-[0.18em] text-muted-2">Risk intelligence workspace</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-border bg-white/[0.02] px-3 py-1.5 text-[10px] text-muted sm:flex">
              <span className="size-1.5 rounded-full bg-teal-400 live-dot" />
              {t("demoMode")}
              <span className="text-muted-2">·</span>
              {t("localApi")}
            </div>
            <LanguageToggle />
          </div>
        </header>

        <main className="grid flex-1 items-center gap-12 py-10 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:py-14">
          <section className="max-w-2xl animate-slide-up">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/[0.055] px-3 py-1.5 text-[10px] font-medium text-teal-200">
              <Sparkles className="size-3" />
              {t("eyebrow")}
            </div>
            <h1 className="font-display text-[42px] font-semibold leading-[1.04] tracking-[-0.035em] text-white sm:text-[56px] lg:text-[62px]">
              <span className="text-gradient">{t("headline")}</span>
            </h1>
            <p className="mt-5 max-w-xl text-[15px] leading-relaxed text-slate-400 sm:text-base">
              {t("subhead")}
            </p>

            <div className="mt-7 grid gap-2.5 sm:grid-cols-3">
              {[
                { icon: Globe2, text: t("featureStreams") },
                { icon: FileCheck2, text: t("featureEvidence") },
                { icon: BadgeCheck, text: t("featureApproval") },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.text}
                    className="flex items-start gap-2.5 rounded-xl border border-border-soft bg-white/[0.018] px-3 py-3"
                  >
                    <Icon className="mt-0.5 size-4 shrink-0 text-accent/80" />
                    <p className="text-[11px] leading-relaxed text-slate-300">{item.text}</p>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-[#0b1525] to-[#08111d] shadow-2xl shadow-black/30">
              <div className="flex items-center justify-between border-b border-border-soft px-5 py-3.5">
                <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-2">
                  <Building2 className="size-3.5 text-accent/70" />
                  {t("caseEyebrow")}
                </div>
                <span className="rounded-full border border-border bg-white/[0.03] px-2 py-0.5 font-mono text-[9px] text-muted-2">
                  CASE-2026-001
                </span>
              </div>
              <div className="grid gap-5 p-5 sm:grid-cols-[1.1fr_0.9fr]">
                <div>
                  <h2 className="font-display text-xl font-semibold tracking-tight text-white">
                    {t("caseCompany")}
                  </h2>
                  <p className="mt-1 text-xs text-muted">{t("caseMeta")}</p>
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    <span className="rounded-md border border-border bg-white/[0.025] px-2 py-1 text-[9px] text-slate-300">EU CSDDD</span>
                    <span className="rounded-md border border-border bg-white/[0.025] px-2 py-1 text-[9px] text-slate-300">Bangladesh Bank</span>
                    <span className="rounded-md border border-border bg-white/[0.025] px-2 py-1 text-[9px] text-slate-300">UFLPA</span>
                    <span className="rounded-md border border-border bg-white/[0.025] px-2 py-1 text-[9px] text-slate-300">GDELT</span>
                  </div>
                  <div className="mt-5 grid grid-cols-3 gap-2">
                    {[
                      { value: "8", label: "open risks" },
                      { value: "3", label: "critical" },
                      { value: "4", label: "approvals" },
                    ].map((metric) => (
                      <div key={metric.label} className="rounded-lg border border-border-soft bg-white/[0.02] px-2.5 py-2">
                        <p className="font-display text-lg font-semibold text-white">{metric.value}</p>
                        <p className="text-[9px] uppercase tracking-wider text-muted-2">{metric.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="relative flex min-h-[150px] items-center justify-center rounded-xl border border-border-soft bg-[#060d18]/70 dot-bg">
                  <svg viewBox="0 0 220 170" className="h-full w-full">
                    <defs>
                      <linearGradient id="loginEdge" x1="0" y1="0" x2="1" y2="1">
                        <stop stopColor="#2dd4bf" stopOpacity="0.55" />
                        <stop offset="1" stopColor="#38bdf8" stopOpacity="0.25" />
                      </linearGradient>
                    </defs>
                    <path d="M110 84 45 42M110 84 45 124M110 84 176 38M110 84 176 118M110 84 110 22M110 84 110 148" stroke="url(#loginEdge)" strokeWidth="1.2" />
                    <circle cx="110" cy="84" r="20" fill="#0d1b2d" stroke="#2dd4bf" strokeOpacity="0.55" />
                    <text x="110" y="88" textAnchor="middle" fill="#99f6e4" fontSize="8" fontFamily="sans-serif">PADMA</text>
                    {[
                      [45, 42, "#38bdf8"],
                      [45, 124, "#a78bfa"],
                      [176, 38, "#fbbf24"],
                      [176, 118, "#fb7185"],
                      [110, 22, "#34d399"],
                      [110, 148, "#fb923c"],
                    ].map(([x, y, color], index) => (
                      <circle key={index} cx={x as number} cy={y as number} r="6.5" fill="#0b1525" stroke={color as string} strokeWidth="1.4" />
                    ))}
                  </svg>
                  <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between rounded-md border border-border-soft bg-[#070f1b]/90 px-2 py-1.5">
                    <span className="text-[8px] uppercase tracking-wider text-muted-2">Supply-chain graph</span>
                    <span className="font-mono text-[8px] text-teal-300">8 suppliers</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 border-t border-border-soft px-5 py-3">
                <span className="text-[9px] uppercase tracking-[0.14em] text-muted-2">Agent flow</span>
                <div className="ml-auto flex items-center gap-1">
                  {flow.map((step, index) => {
                    const Icon = step.icon;
                    return (
                      <React.Fragment key={step.label}>
                        <div className="flex items-center gap-1 rounded-md border border-border-soft bg-white/[0.02] px-1.5 py-1">
                          <Icon className="size-2.5 text-accent/70" />
                          <span className="text-[8px] text-muted">{step.label}</span>
                        </div>
                        {index < flow.length - 1 ? <ChevronRight className="size-2.5 text-muted-2" /> : null}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>

          <section className="w-full max-w-md justify-self-center lg:justify-self-end">
            <div className="panel relative overflow-hidden p-6 shadow-2xl shadow-black/50 sm:p-7">
              <div className="pointer-events-none absolute -right-16 -top-16 size-40 rounded-full bg-teal-400/[0.08] blur-3xl" />
              <div className="relative">
                <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-accent">
                  <LockKeyhole className="size-3" />
                  Demo access
                </div>
                <h2 className="mt-2 font-display text-2xl font-semibold tracking-tight text-white">
                  {t("enter")}
                </h2>
                <p className="mt-1.5 text-xs leading-relaxed text-muted">{t("chooseRole")}</p>

                <div className="mt-5 space-y-2.5">
                  {roles.map((item) => {
                    const Icon = item.icon;
                    const isLoading = loggingIn && selected === item.role;
                    return (
                      <button
                        key={item.role}
                        type="button"
                        disabled={loggingIn}
                        onClick={() => handleLogin(item.role)}
                        className={cn(
                          "group flex w-full items-start gap-3 rounded-xl border border-border bg-white/[0.018] p-3 text-left transition-all disabled:cursor-not-allowed disabled:opacity-60",
                          item.accent,
                        )}
                      >
                        <div className={cn("mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border", item.iconClass)}>
                          {isLoading ? <Loader2 className="size-4 animate-spin" /> : <Icon className="size-4" />}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-slate-100">{item.name}</span>
                            <span className="rounded border border-border bg-white/[0.025] px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider text-muted-2">
                              {t(item.labelKey)}
                            </span>
                          </div>
                          <p className="mt-0.5 text-[10px] text-muted">{item.email}</p>
                          <p className="mt-1 text-[10px] leading-relaxed text-muted-2">{t(item.descriptionKey)}</p>
                        </div>
                        <ArrowRight className="mt-1 size-3.5 text-muted-2 transition-transform group-hover:translate-x-0.5 group-hover:text-accent" />
                      </button>
                    );
                  })}
                </div>

                <div className="mt-5 rounded-lg border border-border-soft bg-[#060d18]/70 p-3">
                  <div className="flex items-center gap-2 text-[10px] text-muted">
                    <Check className="size-3 text-emerald-400" />
                    Seeded demo accounts · no password required
                  </div>
                  <div className="mt-1.5 flex items-center gap-2 text-[10px] text-muted">
                    <Check className="size-3 text-emerald-400" />
                    Role-based access · human approval workflow
                  </div>
                </div>

                <p className="mt-4 text-[9px] leading-relaxed text-muted-2">{t("disclaimer")}</p>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-center gap-2 text-[9px] uppercase tracking-[0.16em] text-muted-2">
              <ShieldCheck className="size-3 text-accent/60" />
              JU_StackMind · JusticeSphere AI · Risk Sentinel
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

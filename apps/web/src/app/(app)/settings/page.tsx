"use client";

import {
  Building2,
  Cpu,
  Database,
  HardDrive,
  LogOut,
  Server,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { PageHeader } from "@/components/common/page-header";
import { PageSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { API_URL, apiFetch } from "@/lib/api/client";
import { useHealth, useMeta } from "@/lib/api/hooks";
import { useAuthStore, usePermissions } from "@/lib/auth/store";

const AUTH_LABELS: Record<string, string> = {
  dev: "authDev",
  supabase: "authSupabase",
};

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border-soft py-2.5 last:border-0">
      <span className="text-[10px] uppercase tracking-wider text-muted-2">{label}</span>
      <span className="max-w-[60%] break-words text-right text-[11px] text-slate-200">{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const t = useTranslations("settings");
  const common = useTranslations("common");
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const { readOnly } = usePermissions();
  const meta = useMeta();
  const health = useHealth();

  if (!user) return <PageSkeleton cards={2} />;

  const authMode = meta.data?.auth_mode ?? health.data?.auth_mode ?? "unknown";
  const dataMode = meta.data?.data_mode ?? health.data?.data_mode ?? "unknown";
  const llmMode = meta.data?.llm_mode ?? health.data?.llm_mode ?? "unknown";
  const storage = meta.data?.storage_backend ?? "unknown";
  const isDemo = Boolean(user.is_demo || meta.data?.demo);

  const signOut = () => {
    void apiFetch("/api/v1/auth/logout", { method: "POST" }).catch(() => undefined);
    logout();
    router.replace("/login");
  };

  return (
    <div className="space-y-5">
      <PageHeader eyebrow={t("eyebrow")} title={t("title")} description={t("subtitle")}>
        <span className="rounded-full border border-border bg-white/[0.025] px-2.5 py-1 text-[9px] uppercase tracking-wider text-muted">
          {isDemo ? t("demoAccount") : t("managedAccount")}
        </span>
      </PageHeader>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="panel p-5">
          <div className="mb-3 flex items-center gap-2">
            <UserRound className="size-4 text-accent" />
            <h2 className="font-display text-sm font-semibold text-slate-100">{t("profile")}</h2>
          </div>
          <DetailRow label={t("name")} value={user.name} />
          <DetailRow label={t("email")} value={user.email} />
          <DetailRow label={t("role")} value={user.role} />
          <DetailRow
            label={t("authentication")}
            value={AUTH_LABELS[authMode] ? t(AUTH_LABELS[authMode]) : authMode}
          />
        </section>

        <section className="panel p-5">
          <div className="mb-3 flex items-center gap-2">
            <Building2 className="size-4 text-accent" />
            <h2 className="font-display text-sm font-semibold text-slate-100">{t("workspace")}</h2>
          </div>
          <DetailRow label={t("company")} value={meta.data?.company.name ?? "Padma Apparel Ltd."} />
          <DetailRow label={t("dataMode")} value={dataMode} />
          <DetailRow label={t("llmMode")} value={llmMode} />
          <DetailRow label={t("embeddingMode")} value={meta.data?.embedding_mode ?? "unknown"} />
          <DetailRow label={t("storage")} value={storage} />
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <section className="panel p-5">
          <div className="mb-3 flex items-center gap-2">
            <ShieldCheck className="size-4 text-accent" />
            <h2 className="font-display text-sm font-semibold text-slate-100">{t("security")}</h2>
          </div>
          <p className="text-[11px] leading-relaxed text-muted">{t("sessionNote")}</p>
          {readOnly ? (
            <p className="mt-3 rounded-lg border border-amber-400/20 bg-amber-400/[0.05] p-3 text-[10px] text-amber-100">
              {t("readOnlyNote")}
            </p>
          ) : null}
          <div className="mt-4 flex flex-wrap items-center gap-2 text-[10px] text-muted-2">
            <Cpu className="size-3" />
            <span>{health.data?.status === "ok" ? "API healthy" : "API status unknown"}</span>
            <span className="text-border">·</span>
            <Database className="size-3" />
            <span>{health.data?.database ?? "database unknown"}</span>
            <span className="text-border">·</span>
            <HardDrive className="size-3" />
            <span>{storage}</span>
          </div>
        </section>

        <section className="panel flex flex-col justify-between p-5">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <Server className="size-4 text-accent" />
              <h2 className="font-display text-sm font-semibold text-slate-100">{t("api")}</h2>
            </div>
            <p className="break-all font-mono text-[10px] text-muted">{API_URL}</p>
            <p className="mt-3 text-[10px] leading-relaxed text-muted-2">{t("pilotNote")}</p>
          </div>
          <Button variant="outline" className="mt-5 w-full" onClick={signOut}>
            <LogOut className="size-3.5" />
            {t("signOut")}
          </Button>
        </section>
      </div>

      <p className="text-[9px] text-muted-2">{common("notLegalAdvice")}</p>
    </div>
  );
}

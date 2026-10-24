"use client";

import { create } from "zustand";
import { createJSONStorage, persist, type StateStorage } from "zustand/middleware";

import { apiFetch } from "@/lib/api/client";
import { setApiToken } from "@/lib/api/token";
import type { Role, TokenResponse, User } from "@/lib/api/types";

const noopStorage: StateStorage = {
  getItem: () => null,
  setItem: () => undefined,
  removeItem: () => undefined,
};

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
  user: User | null;
  hydrated: boolean;
  loggingIn: boolean;
  login: (role: Role) => Promise<void>;
  loginWithPassword: (email: string, password: string) => Promise<void>;
  refresh: () => Promise<boolean>;
  refreshIfNeeded: () => Promise<void>;
  switchRole: (role: Role) => Promise<void>;
  logout: () => void;
  setHydrated: (value: boolean) => void;
}

let refreshInFlight: Promise<boolean> | null = null;

function applySession(
  set: (partial: Partial<AuthState>) => void,
  response: TokenResponse,
) {
  setApiToken(response.access_token);
  set({
    token: response.access_token,
    refreshToken: response.refresh_token ?? null,
    expiresAt: response.expires_at ?? null,
    user: response.user,
    loggingIn: false,
    hydrated: true,
  });
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      expiresAt: null,
      user: null,
      hydrated: false,
      loggingIn: false,
      login: async (role) => {
        set({ loggingIn: true });
        try {
          const response = await apiFetch<TokenResponse>("/api/v1/auth/demo-login", {
            method: "POST",
            body: { role },
          });
          applySession(set, response);
        } catch (error) {
          set({ loggingIn: false });
          throw error;
        }
      },
      loginWithPassword: async (email, password) => {
        set({ loggingIn: true });
        try {
          const response = await apiFetch<TokenResponse>("/api/v1/auth/login", {
            method: "POST",
            body: { email, password },
          });
          applySession(set, response);
        } catch (error) {
          set({ loggingIn: false });
          throw error;
        }
      },
      refresh: async () => {
        const refreshToken = get().refreshToken;
        if (!refreshToken) return false;
        if (refreshInFlight) return refreshInFlight;
        refreshInFlight = (async () => {
          try {
            const response = await apiFetch<TokenResponse>("/api/v1/auth/refresh", {
              method: "POST",
              body: { refresh_token: refreshToken },
            });
            applySession(set, response);
            return true;
          } catch {
            get().logout();
            return false;
          } finally {
            refreshInFlight = null;
          }
        })();
        return refreshInFlight;
      },
      refreshIfNeeded: async () => {
        const { expiresAt, refreshToken } = get();
        if (!refreshToken) return;
        // Refresh a minute early so an active session does not expire mid-request.
        if (expiresAt && expiresAt * 1000 > Date.now() + 60_000) return;
        await get().refresh();
      },
      switchRole: async (role) => {
        await get().login(role);
      },
      logout: () => {
        setApiToken(null);
        set({
          token: null,
          refreshToken: null,
          expiresAt: null,
          user: null,
          hydrated: true,
        });
      },
      setHydrated: (value) => set({ hydrated: value }),
    }),
    {
      name: "chowkidar-auth",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? window.localStorage : noopStorage,
      ),
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        expiresAt: state.expiresAt,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        setApiToken(state?.token ?? null);
        state?.setHydrated(true);
        void state?.refreshIfNeeded();
      },
    },
  ),
);

export function usePermissions() {
  const role = useAuthStore((state) => state.user?.role);
  return {
    role,
    isAdmin: role === "admin",
    isAnalyst: role === "analyst",
    isApprover: role === "approver",
    isViewer: role === "viewer",
    canAnalyze: role === "admin" || role === "analyst",
    canApprove: role === "admin" || role === "approver",
    canViewAudit: role === "admin",
    canViewEvals: role === "admin" || role === "analyst",
    canGenerateReports: role === "admin" || role === "analyst",
    readOnly: role === "viewer",
  };
}

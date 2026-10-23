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
  user: User | null;
  hydrated: boolean;
  loggingIn: boolean;
  login: (role: Role) => Promise<void>;
  switchRole: (role: Role) => Promise<void>;
  logout: () => void;
  setHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
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
          setApiToken(response.access_token);
          set({
            token: response.access_token,
            user: response.user,
            loggingIn: false,
            hydrated: true,
          });
        } catch (error) {
          set({ loggingIn: false });
          throw error;
        }
      },
      switchRole: async (role) => {
        await get().login(role);
      },
      logout: () => {
        setApiToken(null);
        set({ token: null, user: null });
      },
      setHydrated: (value) => set({ hydrated: value }),
    }),
    {
      name: "chowkidar-auth",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? window.localStorage : noopStorage,
      ),
      partialize: (state) => ({ token: state.token, user: state.user }),
      onRehydrateStorage: () => (state) => {
        setApiToken(state?.token ?? null);
        state?.setHydrated(true);
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

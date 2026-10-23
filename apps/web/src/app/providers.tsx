"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import * as React from "react";
import { Toaster } from "sonner";

import { useAuthStore } from "@/lib/auth/store";
import { setApiToken } from "@/lib/api/token";

function UnauthorizedBridge() {
  const router = useRouter();
  React.useEffect(() => {
    const handler = () => {
      useAuthStore.getState().logout();
      router.replace("/login");
    };
    window.addEventListener("chowkidar:unauthorized", handler);
    return () => window.removeEventListener("chowkidar:unauthorized", handler);
  }, [router]);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
          mutations: {
            retry: 0,
          },
        },
      }),
  );

  React.useEffect(() => {
    const state = useAuthStore.getState();
    setApiToken(state.token);
    if (!state.hydrated) state.setHydrated(true);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <UnauthorizedBridge />
      {children}
      <Toaster
        theme="dark"
        position="top-right"
        toastOptions={{
          style: {
            background: "#0b1525",
            border: "1px solid #1b2a42",
            color: "#e6edf7",
          },
        }}
      />
    </QueryClientProvider>
  );
}

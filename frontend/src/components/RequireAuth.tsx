"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiGet, ApiClientError } from "@/lib/api";
import { clearAccessToken, getAccessToken } from "@/lib/auth";
import type { UserPublic } from "@/lib/types";

type RequireAuthProps = {
  children: (user: UserPublic) => React.ReactNode;
};

type AuthState =
  | { kind: "loading" }
  | { kind: "ready"; user: UserPublic }
  | { kind: "error"; message: string };

export function RequireAuth({ children }: RequireAuthProps) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!getAccessToken()) {
        router.replace("/login");
        return;
      }

      try {
        const user = await apiGet<UserPublic>("/api/auth/me", true);
        if (!cancelled) setState({ kind: "ready", user });
      } catch (error) {
        clearAccessToken();
        if (cancelled) return;
        if (error instanceof ApiClientError && error.status === 401) {
          router.replace("/login");
          return;
        }
        setState({
          kind: "error",
          message: error instanceof ApiClientError ? error.message : "Unable to load session",
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (state.kind === "loading") {
    return (
      <main className="page">
        <p className="status">Loading workspace…</p>
      </main>
    );
  }

  if (state.kind === "error") {
    return (
      <main className="page">
        <p className="status status-error">{state.message}</p>
      </main>
    );
  }

  return <>{children(state.user)}</>;
}

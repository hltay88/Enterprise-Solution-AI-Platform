"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiGet, ApiClientError } from "@/lib/api";
import { clearAccessToken, getAccessToken } from "@/lib/auth";
import type { UserPublic } from "@/lib/types";
import { HealthStatus } from "@/components/HealthStatus";

type PanelState =
  | { kind: "loading" }
  | { kind: "guest" }
  | { kind: "user"; user: UserPublic }
  | { kind: "error"; message: string };

export function HomeAuthPanel() {
  const router = useRouter();
  const [state, setState] = useState<PanelState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const token = getAccessToken();
      if (!token) {
        if (!cancelled) setState({ kind: "guest" });
        return;
      }

      try {
        const user = await apiGet<UserPublic>("/api/auth/me", true);
        if (!cancelled) setState({ kind: "user", user });
      } catch (error) {
        clearAccessToken();
        if (cancelled) return;
        if (error instanceof ApiClientError && error.status === 401) {
          setState({ kind: "guest" });
          return;
        }
        setState({
          kind: "error",
          message: error instanceof ApiClientError ? error.message : "Session check failed",
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  function signOut() {
    clearAccessToken();
    setState({ kind: "guest" });
    router.refresh();
  }

  if (state.kind === "loading") {
    return <p className="status">Checking session…</p>;
  }

  if (state.kind === "error") {
    return (
      <div className="stack">
        <p className="status status-error">{state.message}</p>
        <Link className="btn-primary" href="/login">
          Go to login
        </Link>
      </div>
    );
  }

  if (state.kind === "guest") {
    return (
      <div className="stack">
        <p>
          Sign in to start creating projects and analyzing customer requirements.
        </p>
        <Link className="btn-primary" href="/login">
          Sign in
        </Link>
        <HealthStatus />
      </div>
    );
  }

  return (
    <div className="stack">
      <p className="status status-ok">
        Signed in as {state.user.name} ({state.user.email})
      </p>
      <p>Dashboard arrives next in Phase C.</p>
      <button className="btn-secondary" type="button" onClick={signOut}>
        Sign out
      </button>
      <HealthStatus />
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

import { apiGet, ApiClientError } from "@/lib/api";
import type { HealthData } from "@/lib/types";

type StatusState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthData }
  | { kind: "error"; message: string };

export function HealthStatus() {
  const [state, setState] = useState<StatusState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await apiGet<HealthData>("/api/health");
        if (!cancelled) {
          setState({ kind: "ok", data });
        }
      } catch (error) {
        if (cancelled) return;
        const message =
          error instanceof ApiClientError
            ? error.message
            : "Unable to reach API";
        setState({ kind: "error", message });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === "loading") {
    return <p className="status">Checking API…</p>;
  }

  if (state.kind === "error") {
    return (
      <p className="status status-error">
        API offline — {state.message}
      </p>
    );
  }

  return (
    <p className="status status-ok">
      API {state.data.status} · database {state.data.database}
    </p>
  );
}

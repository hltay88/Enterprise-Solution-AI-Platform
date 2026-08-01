"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { apiPost, ApiClientError } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";
import type { LoginData } from "@/lib/types";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("changeme");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);

    try {
      const data = await apiPost<LoginData>("/api/auth/login", { email, password });
      setAccessToken(data.access_token);
      router.replace("/dashboard");
      router.refresh();
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.message : "Unable to sign in";
      setError(message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="login-form" onSubmit={onSubmit}>
      <label className="field">
        <span>Email</span>
        <input
          type="email"
          name="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </label>

      <label className="field">
        <span>Password</span>
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </label>

      {error ? <p className="form-error">{error}</p> : null}

      <button className="btn-primary" type="submit" disabled={pending}>
        {pending ? "Signing in…" : "Sign in"}
      </button>

      <p className="hint">
        Local demo: <code>demo@example.com</code> / <code>changeme</code>
      </p>
    </form>
  );
}

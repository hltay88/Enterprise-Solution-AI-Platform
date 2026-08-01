"use client";

import { FormEvent, useState } from "react";

import type { ProjectInput, ProjectSummary } from "@/lib/types";

type ProjectFormProps = {
  initial?: ProjectSummary | null;
  submitLabel: string;
  onSubmit: (values: ProjectInput) => Promise<void>;
};

const STATUS_OPTIONS = ["draft", "active", "archived"];

export function ProjectForm({ initial, submitLabel, onSubmit }: ProjectFormProps) {
  const [projectName, setProjectName] = useState(initial?.project_name ?? "");
  const [customer, setCustomer] = useState(initial?.customer ?? "");
  const [industry, setIndustry] = useState(initial?.industry ?? "");
  const [status, setStatus] = useState(initial?.status ?? "draft");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await onSubmit({
        project_name: projectName.trim(),
        customer: customer.trim() || null,
        industry: industry.trim() || null,
        status,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save project");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Project name</span>
        <input
          required
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="ACME Network Refresh"
        />
      </label>

      <label className="field">
        <span>Customer</span>
        <input
          value={customer}
          onChange={(event) => setCustomer(event.target.value)}
          placeholder="ACME Corp"
        />
      </label>

      <label className="field">
        <span>Industry</span>
        <input
          value={industry}
          onChange={(event) => setIndustry(event.target.value)}
          placeholder="Manufacturing"
        />
      </label>

      <label className="field">
        <span>Status</span>
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      {error ? <p className="form-error">{error}</p> : null}

      <button className="btn-primary" type="submit" disabled={pending}>
        {pending ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}

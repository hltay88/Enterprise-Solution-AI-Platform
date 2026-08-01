"use client";

import { FormEvent, useState } from "react";

import { REQUEST_TYPES, type ProjectInput, type ProjectSummary } from "@/lib/types";

type ProjectFormProps = {
  initial?: ProjectSummary | null;
  submitLabel: string;
  defaultAccountManager?: string;
  onSubmit: (values: ProjectInput) => Promise<void>;
};

const STATUS_OPTIONS = ["draft", "active", "archived"];

function toDateInput(value: string | null | undefined): string {
  if (!value) return "";
  return value.slice(0, 10);
}

export function ProjectForm({
  initial,
  submitLabel,
  defaultAccountManager = "",
  onSubmit,
}: ProjectFormProps) {
  const [projectName, setProjectName] = useState(initial?.project_name ?? "");
  const [customer, setCustomer] = useState(initial?.customer ?? "");
  const [industry, setIndustry] = useState(initial?.industry ?? "");
  const [status, setStatus] = useState(initial?.status ?? "draft");
  const [accountManager, setAccountManager] = useState(
    initial?.account_manager ?? defaultAccountManager,
  );
  const [dealId, setDealId] = useState(initial?.deal_id ?? "");
  const [dealName, setDealName] = useState(initial?.deal_name ?? "");
  const [picName, setPicName] = useState(initial?.pic_name ?? "");
  const [picContact, setPicContact] = useState(initial?.pic_contact ?? "");
  const [picDesignation, setPicDesignation] = useState(initial?.pic_designation ?? "");
  const [budgetInformation, setBudgetInformation] = useState(
    initial?.budget_information ?? "",
  );
  const [requestType, setRequestType] = useState(
    initial?.request_type ?? REQUEST_TYPES[0],
  );
  const [requiredCompletionDate, setRequiredCompletionDate] = useState(
    toDateInput(initial?.required_completion_date),
  );
  const [requirementDetails, setRequirementDetails] = useState(
    initial?.requirement_details ?? "",
  );
  const [winningProbability, setWinningProbability] = useState(
    initial?.winning_probability != null ? String(initial.winning_probability) : "",
  );
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const winRaw = winningProbability.trim();
    let winValue: number | null = null;
    if (winRaw) {
      const parsed = Number(winRaw);
      if (!Number.isInteger(parsed) || parsed < 0 || parsed > 100) {
        setError("Winning probability must be a whole number from 0 to 100");
        return;
      }
      winValue = parsed;
    }

    setPending(true);
    try {
      await onSubmit({
        project_name: projectName.trim(),
        customer: customer.trim(),
        industry: industry.trim() || null,
        status,
        account_manager: accountManager.trim() || null,
        deal_id: dealId.trim(),
        deal_name: dealName.trim(),
        pic_name: picName.trim(),
        pic_contact: picContact.trim() || null,
        pic_designation: picDesignation.trim() || null,
        budget_information: budgetInformation.trim() || null,
        request_type: requestType,
        required_completion_date: requiredCompletionDate || null,
        requirement_details: requirementDetails.trim(),
        winning_probability: winValue,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save project");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="project-form" onSubmit={handleSubmit}>
      <fieldset className="form-section">
        <legend>Project basics</legend>
        <div className="form-grid">
          <label className="field">
            <span>Project name *</span>
            <input
              required
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              placeholder="SEGi Subang WiFi & Network"
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
          <label className="field">
            <span>Industry</span>
            <input
              value={industry}
              onChange={(event) => setIndustry(event.target.value)}
              placeholder="Education"
            />
          </label>
        </div>
      </fieldset>

      <fieldset className="form-section">
        <legend>Sales intake</legend>
        <p className="muted form-section-help">
          Capture what sales already knows before PreSales analysis. Mandatory fields match
          SmartSD intake.
        </p>
        <div className="form-grid">
          <label className="field">
            <span>Account manager</span>
            <input
              value={accountManager}
              onChange={(event) => setAccountManager(event.target.value)}
              placeholder="Defaults to logged-in user"
            />
          </label>
          <label className="field">
            <span>Customer name *</span>
            <input
              required
              value={customer}
              onChange={(event) => setCustomer(event.target.value)}
              placeholder="SEGi University"
            />
          </label>
          <label className="field">
            <span>Deal ID *</span>
            <input
              required
              value={dealId}
              onChange={(event) => setDealId(event.target.value)}
              placeholder="HubSpot deal ID"
            />
          </label>
          <label className="field">
            <span>Deal name *</span>
            <input
              required
              value={dealName}
              onChange={(event) => setDealName(event.target.value)}
              placeholder="HubSpot deal name"
            />
          </label>
          <label className="field">
            <span>Request type *</span>
            <select
              required
              value={requestType}
              onChange={(event) => setRequestType(event.target.value)}
            >
              {REQUEST_TYPES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Required completion date</span>
            <input
              type="date"
              value={requiredCompletionDate}
              onChange={(event) => setRequiredCompletionDate(event.target.value)}
            />
          </label>
          <label className="field">
            <span>PIC name *</span>
            <input
              required
              value={picName}
              onChange={(event) => setPicName(event.target.value)}
              placeholder="End-user contact name"
            />
          </label>
          <label className="field">
            <span>PIC contact</span>
            <input
              value={picContact}
              onChange={(event) => setPicContact(event.target.value)}
              placeholder="Email or phone"
            />
          </label>
          <label className="field">
            <span>PIC designation</span>
            <input
              value={picDesignation}
              onChange={(event) => setPicDesignation(event.target.value)}
              placeholder="IT Manager"
            />
          </label>
          <label className="field">
            <span>Budget information</span>
            <input
              value={budgetInformation}
              onChange={(event) => setBudgetInformation(event.target.value)}
              placeholder="Estimated budget"
            />
          </label>
          <label className="field">
            <span>Winning probability %</span>
            <input
              type="number"
              min={0}
              max={100}
              step={1}
              value={winningProbability}
              onChange={(event) => setWinningProbability(event.target.value)}
              placeholder="0–100"
            />
          </label>
        </div>
        <label className="field field-full">
          <span>Requirement details *</span>
          <textarea
            required
            rows={6}
            value={requirementDetails}
            onChange={(event) => setRequirementDetails(event.target.value)}
            placeholder="Describe requirements from customer discussions, constraints, scope, and known gaps."
          />
        </label>
      </fieldset>

      {error ? <p className="form-error">{error}</p> : null}

      <button className="btn-primary" type="submit" disabled={pending}>
        {pending ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}

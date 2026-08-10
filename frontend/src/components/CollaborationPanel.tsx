"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  ActivityItem,
  ApprovalRequest,
  CommentItem,
  ReviewRequest,
} from "@/lib/types";

type CollaborationPanelProps = {
  projectId: string;
  refreshToken?: number;
};

export function CollaborationPanel({
  projectId,
  refreshToken = 0,
}: CollaborationPanelProps) {
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [reviews, setReviews] = useState<ReviewRequest[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [commentBody, setCommentBody] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");
  const [approvalMessage, setApprovalMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setError(null);
    try {
      const [c, r, a, act] = await Promise.all([
        apiGet<CommentItem[]>(`/api/v1/projects/${projectId}/comments`, true),
        apiGet<ReviewRequest[]>(
          `/api/v1/projects/${projectId}/review-requests`,
          true,
        ),
        apiGet<ApprovalRequest[]>(
          `/api/v1/projects/${projectId}/approval-requests`,
          true,
        ),
        apiGet<ActivityItem[]>(
          `/api/v1/projects/${projectId}/activity?limit=20`,
          true,
        ),
      ]);
      setComments(c);
      setReviews(r);
      setApprovals(a);
      setActivity(act);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load collaboration data",
      );
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  async function postComment() {
    if (!commentBody.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await apiPost(
        `/api/v1/projects/${projectId}/comments`,
        { body: commentBody.trim(), resource_type: "project" },
        true,
      );
      setCommentBody("");
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Comment failed");
    } finally {
      setBusy(false);
    }
  }

  async function createReview() {
    setBusy(true);
    setError(null);
    try {
      await apiPost(
        `/api/v1/projects/${projectId}/review-requests`,
        {
          resource_type: "project",
          message: reviewMessage.trim() || "Please review this project",
        },
        true,
      );
      setReviewMessage("");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Review request failed",
      );
    } finally {
      setBusy(false);
    }
  }

  async function createApproval() {
    setBusy(true);
    setError(null);
    try {
      await apiPost(
        `/api/v1/projects/${projectId}/approval-requests`,
        {
          resource_type: "project",
          message: approvalMessage.trim() || "Please approve this project package",
        },
        true,
      );
      setApprovalMessage("");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Approval request failed",
      );
    } finally {
      setBusy(false);
    }
  }

  async function completeReview(id: string) {
    setBusy(true);
    try {
      await apiPost(
        `/api/v1/review-requests/${id}/complete`,
        { resolution_note: "Reviewed" },
        true,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Complete review failed",
      );
    } finally {
      setBusy(false);
    }
  }

  async function resolveApproval(id: string, decision: "approved" | "rejected") {
    setBusy(true);
    try {
      await apiPost(
        `/api/v1/approval-requests/${id}/resolve`,
        { decision, resolution_note: decision },
        true,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Resolve approval failed",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel rkm-panel" id="collaboration-panel">
      <div className="panel-heading">
        <div>
          <h2>Collaboration</h2>
          <p className="muted">
            Sprint 5.4 — comments, review requests, and approval requests
          </p>
        </div>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      <label className="field">
        <span>Add comment</span>
        <textarea
          rows={3}
          value={commentBody}
          onChange={(e) => setCommentBody(e.target.value)}
          placeholder="Share context for the team…"
        />
      </label>
      <button
        className="btn-primary btn-compact"
        type="button"
        disabled={busy || !commentBody.trim()}
        onClick={() => void postComment()}
      >
        Post comment
      </button>

      <div className="rkm-section">
        <h3>Comments</h3>
        {comments.length === 0 ? (
          <p className="muted">No comments yet.</p>
        ) : (
          <ul>
            {comments.map((c) => (
              <li key={c.id}>
                <span className="muted">
                  {new Date(c.created_at).toLocaleString()}
                </span>{" "}
                — {c.body}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rkm-section">
        <h3>Review requests</h3>
        <label className="field">
          <span>Message</span>
          <input
            value={reviewMessage}
            onChange={(e) => setReviewMessage(e.target.value)}
            placeholder="Please review architecture option…"
          />
        </label>
        <button
          className="btn-secondary btn-compact"
          type="button"
          disabled={busy}
          onClick={() => void createReview()}
        >
          Request review
        </button>
        <ul>
          {reviews.map((r) => (
            <li key={r.id}>
              [{r.status}] {r.resource_type} — {r.message || "(no message)"}{" "}
              {r.status === "open" ? (
                <button
                  type="button"
                  className="btn-secondary btn-compact"
                  disabled={busy}
                  onClick={() => void completeReview(r.id)}
                >
                  Complete
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </div>

      <div className="rkm-section">
        <h3>Approval requests</h3>
        <label className="field">
          <span>Message</span>
          <input
            value={approvalMessage}
            onChange={(e) => setApprovalMessage(e.target.value)}
            placeholder="Ready for formal approval…"
          />
        </label>
        <button
          className="btn-secondary btn-compact"
          type="button"
          disabled={busy}
          onClick={() => void createApproval()}
        >
          Request approval
        </button>
        <ul>
          {approvals.map((a) => (
            <li key={a.id}>
              [{a.status}] {a.resource_type} — {a.message || "(no message)"}{" "}
              {a.status === "open" ? (
                <>
                  <button
                    type="button"
                    className="btn-primary btn-compact"
                    disabled={busy}
                    onClick={() => void resolveApproval(a.id, "approved")}
                  >
                    Approve
                  </button>{" "}
                  <button
                    type="button"
                    className="btn-secondary btn-compact"
                    disabled={busy}
                    onClick={() => void resolveApproval(a.id, "rejected")}
                  >
                    Reject
                  </button>
                </>
              ) : null}
            </li>
          ))}
        </ul>
      </div>

      <div className="rkm-section">
        <h3>Activity</h3>
        {activity.length === 0 ? (
          <p className="muted">No activity yet.</p>
        ) : (
          <ul>
            {activity.map((item) => (
              <li key={`${item.kind}-${item.id}`}>
                <span className="muted">
                  {item.kind} · {new Date(item.created_at).toLocaleString()}
                </span>{" "}
                — {item.summary}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

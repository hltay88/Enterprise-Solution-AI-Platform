#!/usr/bin/env python3
"""One-command Stage F smoke test (audit + RBAC + pack + publish).

Usage (Atlas must be running):
  python3 scripts/verify_stage_f.py
"""

from __future__ import annotations

import json
import sys
import time
import uuid
import urllib.error
import urllib.request

API = "http://localhost:8000"


def req(method: str, path: str, token: str | None = None, data=None, files=None):
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if files is not None:
        boundary = "----B" + uuid.uuid4().hex
        parts: list[bytes] = []
        for name, value in files.items():
            if isinstance(value, tuple):
                filename, content, ctype = value
                parts.append(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="{name}"; '
                        f'filename="{filename}"\r\n'
                        f"Content-Type: {ctype}\r\n\r\n"
                    ).encode()
                    + content
                    + b"\r\n"
                )
            else:
                parts.append(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                        f"{value}\r\n"
                    ).encode()
                )
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw}
        return exc.code, payload


def ok(status: int, payload: dict, label: str):
    print(f"=== {label} [{status}] ===")
    if not payload.get("success"):
        print(json.dumps(payload, indent=2)[:1500])
        raise SystemExit(f"FAIL: {label}")
    return payload["data"]


def main() -> int:
    status, payload = req("GET", "/api/health")
    if not payload.get("success"):
        print("Backend not healthy at http://localhost:8000 — start Atlas first.")
        return 1

    status, payload = req(
        "POST",
        "/api/auth/login",
        data={"email": "demo@example.com", "password": "changeme"},
    )
    login = ok(status, payload, "login")
    token = login["access_token"]
    role = login["user"].get("role")
    print("role:", role)
    if role != "approver":
        raise SystemExit(f"FAIL: expected approver, got {role}")

    status, payload = req(
        "POST",
        "/api/projects",
        token=token,
        data={
            "project_name": f"Stage F Verify {int(time.time()) % 100000}",
            "customer": "Acme Corp",
            "industry": "Technology",
            "deal_id": f"F{int(time.time()) % 100000}",
            "deal_name": "Stage F",
            "pic_name": "Jane Doe",
            "request_type": "Initial Discovery",
            "requirement_details": (
                "Enterprise WiFi 6 for 3 floors, networking refresh, 802.1X, NMS. "
                "Budget 500k. Dec 2026."
            ),
        },
    )
    project = ok(status, payload, "create_project")
    project_id = project["id"]
    print("project:", project_id)

    status, payload = req(
        "POST",
        "/api/v1/documents/upload",
        token=token,
        files={
            "project_id": project_id,
            "files": (
                "rfp.txt",
                b"Acme needs WiFi 6 coverage 3 floors, 800 clients, switch refresh 10G.",
                "text/plain",
            ),
        },
    )
    upload = ok(status, payload, "upload")
    print("accepted:", upload.get("accepted_count"))

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/analyze",
        token=token,
        data={},
    )
    job_id = ok(status, payload, "analyze")["job_id"]
    job_status = "queued"
    for _ in range(40):
        status, payload = req("GET", f"/api/v1/jobs/{job_id}", token=token)
        job_status = ok(status, payload, "job")["status"]
        print("job:", job_status)
        if job_status in {"completed", "failed", "error"}:
            break
        time.sleep(2)
    if job_status != "completed":
        raise SystemExit("FAIL: RKM job did not complete")

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/requirements?status=draft",
        token=token,
    )
    draft = ok(status, payload, "draft")
    reasoning = draft["analysis"].get("reasoning_summary") or ""
    print("version:", draft["version"]["number"])
    print("knowledge_pack_in_reasoning:", "Knowledge pack" in reasoning)

    req_id = None
    for key in (
        "functional_requirements",
        "business_objectives",
        "non_functional_requirements",
    ):
        items = draft.get(key) or []
        if items:
            req_id = items[0]["id"]
            break

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/gap-analysis",
        token=token,
        data={},
    )
    gap = ok(status, payload, "gap")
    print("blockers:", [item["code"] for item in gap.get("publish_blockers") or []])

    if req_id:
        status, payload = req(
            "POST",
            f"/api/v1/projects/{project_id}/requirements/review",
            token=token,
            data={
                "edits": [
                    {
                        "id": req_id,
                        "title": "WiFi coverage",
                        "description": "3 floors seamless roaming",
                        "priority": "high",
                    }
                ],
                "change_summary": "Stage F verify edit",
            },
        )
        reviewed = ok(status, payload, "review")
        print("reviewed:", reviewed["version_label"])

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/approve",
        token=token,
        data={"note": "Stage F verify"},
    )
    approved = ok(status, payload, "approve")
    print("approved:", approved["status"])

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/publish",
        token=token,
        data={"note": "Stage F verify publish"},
    )
    if payload.get("success"):
        print("published:", payload["data"]["version_label"])
    else:
        print("publish_blocked:", (payload.get("error") or {}).get("message"))

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/audit-logs?limit=50",
        token=token,
    )
    logs = ok(status, payload, "audit_logs")
    actions = [row.get("action") for row in logs]
    print("audit_count:", len(logs))
    for row in logs:
        print("-", row.get("action"), "|", row.get("summary"))

    missing = {"document.upload", "rkm.review", "rkm.approve"} - set(actions)
    if missing:
        raise SystemExit(f"FAIL: missing audit actions {missing}")

    print("STAGE_F_VERIFY_OK")
    print("UI:", f"http://localhost:3000/projects/{project_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"Cannot reach {API}: {exc}")
        print("Start Atlas first (./start-atlas.sh), then retry.")
        raise SystemExit(1) from exc

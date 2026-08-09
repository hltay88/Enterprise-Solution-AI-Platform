#!/usr/bin/env python3
"""Sprint 3.1 verification: unit tests + domain/architecture smoke.

Usage (backend must be running for the API smoke section):
  python3 scripts/verify_sprint_3_1.py
  python3 scripts/verify_sprint_3_1.py --unit-only
  python3 scripts/verify_sprint_3_1.py --smoke-only

Flow: login → project → upload → Draft RKM → gap/answers → approve → publish
→ domains/analyze → GET domains + traceability → architecture/generate (regression).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "http://localhost:8000"
BACKEND = ROOT / "backend"
PYTEST = BACKEND / ".venv" / "bin" / "python"

RICH_RFP = b"""
Acme Corp campus refresh RFP.

Business outcomes: improve employee productivity and guest Wi-Fi experience;
reduce ticket volume 30% within 6 months; support hybrid work securely.

Current environment: 3 floors HQ, aging Wi-Fi 5 APs, core switches at 1G,
Active Directory on-prem, limited firewall segmentation, no ZTNA, NMS is PRTG.

Functional requirements:
- Wi-Fi 6 campus coverage for 800 concurrent clients with seamless roaming
- 802.1X / RADIUS authentication for corporate devices
- Guest captive portal isolated from corporate VLAN
- Core/access switching refresh to 10G uplinks
- Centralized network monitoring and alerting
- Secure remote access for contractors (ZTNA preferred)

Non-functional:
- 99.9% wireless availability during business hours
- Peak density 1 device per person in open office
- Security: MFA for remote access; encryption in transit

Constraints: budget SGD 500k, completion by Dec 2026, must reuse existing cabling
where possible, change windows weekends only.

Dependencies: identity team for AD/RADIUS, facilities for AP mounting,
ISP for internet uplink upgrade.

Risks: floor plans incomplete; survey delay; change freeze in Q4 finance close.

Assumptions: existing fibre between floors is healthy; power available at AP
locations; guest internet policy already approved by security.

Stakeholders: IT manager Jane Doe, facilities lead, security architect.
"""


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
        with urllib.request.urlopen(request, timeout=180) as resp:
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
        print(json.dumps(payload, indent=2)[:2000])
        raise SystemExit(f"FAIL: {label}")
    return payload["data"]


def run_unit_tests() -> None:
    python = str(PYTEST if PYTEST.exists() else sys.executable)
    print(f"=== unit tests ({python} -m pytest -q) ===")
    result = subprocess.run(
        [python, "-m", "pytest", "-q"],
        cwd=str(BACKEND),
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("FAIL: pytest suite")
    print("UNIT_TESTS_OK")


def wait_job(token: str, job_id: str) -> None:
    job_status = "queued"
    for _ in range(60):
        status, payload = req("GET", f"/api/v1/jobs/{job_id}", token=token)
        job_status = ok(status, payload, "job")["status"]
        print("job:", job_status)
        if job_status in {"completed", "failed", "error"}:
            break
        time.sleep(2)
    if job_status != "completed":
        raise SystemExit("FAIL: RKM analyze job did not complete")


def _answer_open_clarifications(
    token: str,
    project_id: str,
    clarifications: list,
    *,
    label: str,
) -> int:
    unanswered = [
        item
        for item in clarifications
        if not (item.get("answer") or "").strip() and item.get("id")
    ]
    if not unanswered:
        return 0
    answers = [
        {
            "clarification_id": item["id"],
            "answer": (
                f"Customer-confirmed for Sprint 3.1 verify: {item.get('question') or 'n/a'}. "
                "HQ floors 1–3, ~800 concurrent clients, Wi-Fi 6, 802.1X/RADIUS, guest portal "
                "isolated, 10G uplinks, ZTNA for contractors, 99.9% availability, budget SGD 500k, "
                "Dec 2026 target, weekend change windows only."
            ),
        }
        for item in unanswered
    ]
    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/clarification/answer",
        token=token,
        data={"answers": answers},
    )
    ok(status, payload, label)
    print(f"{label}:", len(answers))
    return len(answers)


def clear_gap_blockers(token: str, project_id: str) -> dict:
    """Raise completeness/confidence until only human_approval remains (or give up)."""
    gap: dict = {}
    for round_idx in range(1, 6):
        status, payload = req(
            "POST",
            f"/api/v1/projects/{project_id}/requirements/gap-analysis",
            token=token,
            data={},
        )
        gap = ok(status, payload, f"gap_analysis_r{round_idx}")
        blockers = [item.get("code") for item in gap.get("publish_blockers") or []]
        print(
            f"scores_r{round_idx}:",
            gap.get("completeness_score"),
            gap.get("confidence_score"),
            "blockers:",
            blockers,
        )
        soft = {
            code
            for code in blockers
            if code
            not in {
                "human_approval_required",
                None,
            }
        }
        if not soft:
            return gap

        clarifications = gap.get("clarifications") or []
        if not clarifications:
            status, payload = req(
                "POST",
                f"/api/v1/projects/{project_id}/clarification/generate",
                token=token,
                data={},
            )
            clarifications = ok(status, payload, f"generate_clarifications_r{round_idx}") or []

        answered = _answer_open_clarifications(
            token,
            project_id,
            clarifications,
            label=f"answer_clarifications_r{round_idx}",
        )
        if answered == 0:
            # Force a fresh clarification pass for thin/missing-evidence gaps.
            status, payload = req(
                "POST",
                f"/api/v1/projects/{project_id}/clarification/generate",
                token=token,
                data={},
            )
            clarifications = ok(status, payload, f"regenerate_clarifications_r{round_idx}") or []
            answered = _answer_open_clarifications(
                token,
                project_id,
                clarifications,
                label=f"answer_regenerated_r{round_idx}",
            )
            if answered == 0:
                break

    return gap


def run_smoke() -> str:
    status, payload = req("GET", "/api/health")
    if status != 200 or not payload.get("success"):
        print("Backend not healthy at http://localhost:8000 — start Atlas first.")
        raise SystemExit(1)

    status, payload = req(
        "POST",
        "/api/auth/login",
        data={"email": "demo@example.com", "password": "changeme"},
    )
    login = ok(status, payload, "login")
    token = login["access_token"]
    role = login["user"].get("role")
    print("role:", role)
    if role not in {"editor", "approver"}:
        raise SystemExit(f"FAIL: expected editor/approver, got {role}")

    stamp = int(time.time()) % 100000
    status, payload = req(
        "POST",
        "/api/projects",
        token=token,
        data={
            "project_name": f"Sprint 3.1 Verify {stamp}",
            "customer": "Acme Corp",
            "industry": "Technology",
            "deal_id": f"S31{stamp}",
            "deal_name": "Sprint 3.1 Domains",
            "pic_name": "Jane Doe",
            "request_type": "Initial Discovery",
            "requirement_details": RICH_RFP.decode("utf-8")[:500],
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
            "files": ("rfp.txt", RICH_RFP, "text/plain"),
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
    wait_job(token, job_id)

    clear_gap_blockers(token, project_id)

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/requirements?status=draft",
        token=token,
    )
    draft = ok(status, payload, "draft")
    req_id = None
    first_item: dict | None = None
    for key in (
        "functional_requirements",
        "business_objectives",
        "non_functional_requirements",
    ):
        items = draft.get(key) or []
        if items:
            first_item = items[0]
            req_id = first_item.get("id")
            break

    if req_id and first_item is not None:
        status, payload = req(
            "POST",
            f"/api/v1/projects/{project_id}/requirements/review",
            token=token,
            data={
                "edits": [
                    {
                        "id": req_id,
                        "title": first_item.get("title") or "WiFi coverage",
                        "description": (
                            first_item.get("description")
                            or "3 floors seamless roaming Wi-Fi 6"
                        ),
                        "priority": "high",
                    }
                ],
                "change_summary": "Sprint 3.1 verify review",
            },
        )
        ok(status, payload, "review")

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/approve",
        token=token,
        data={"note": "Sprint 3.1 verify"},
    )
    approved = ok(status, payload, "approve")
    print("approved:", approved.get("status"))

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/publish",
        token=token,
        data={"note": "Sprint 3.1 verify publish"},
    )
    published = ok(status, payload, "publish")
    print("published:", published.get("version_label"))

    # --- Sprint 3.1 domain surface ---
    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/domains/analyze",
        token=token,
        data={},
    )
    analysis = ok(status, payload, "domains_analyze")
    domains = analysis.get("domains") or []
    print(
        "domain_version:",
        analysis.get("version_label"),
        "domain_count:",
        len(domains),
        "codes:",
        [item.get("domain_code") for item in domains],
    )
    if not domains:
        raise SystemExit("FAIL: analyze returned zero domains")
    for item in domains:
        conf = float(item.get("confidence") or 0)
        if conf < 0 or conf > 1:
            raise SystemExit(f"FAIL: confidence out of range: {conf}")

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/domains",
        token=token,
    )
    latest = ok(status, payload, "domains_get")
    if latest.get("id") != analysis.get("id"):
        raise SystemExit("FAIL: GET domains did not return latest analysis")

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/domains/versions",
        token=token,
    )
    versions = ok(status, payload, "domains_versions")
    if not versions:
        raise SystemExit("FAIL: expected at least one domain analysis version")

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/traceability",
        token=token,
    )
    trace = ok(status, payload, "traceability")
    print("traceability_rows:", len(trace))
    if not trace:
        raise SystemExit("FAIL: expected requirement→domain traceability rows")

    # --- Architecture MVP regression (ATLAS-034) ---
    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/architecture/generate",
        token=token,
        data={},
    )
    arch = ok(status, payload, "architecture_generate")
    print("architecture_version:", arch.get("version_label"))

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/architecture",
        token=token,
    )
    arch_latest = ok(status, payload, "architecture_get")
    if not arch_latest.get("summary"):
        raise SystemExit("FAIL: architecture GET missing summary")

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/audit-logs?limit=50",
        token=token,
    )
    logs = ok(status, payload, "audit_logs")
    actions = {row.get("action") for row in logs}
    missing = {"domain.analyze", "rkm.publish"} - actions
    if missing:
        raise SystemExit(f"FAIL: missing audit actions {missing}")

    print("SPRINT_3_1_VERIFY_OK")
    print("UI:", f"http://localhost:3000/projects/{project_id}")
    return project_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Sprint 3.1")
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Run backend pytest only",
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Skip pytest; run API smoke only",
    )
    args = parser.parse_args()

    if not args.smoke_only:
        run_unit_tests()
    if args.unit_only:
        return 0

    try:
        run_smoke()
    except urllib.error.URLError as exc:
        print(f"Cannot reach {API}: {exc}")
        print("Start Atlas first (./start-atlas.sh), then retry.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

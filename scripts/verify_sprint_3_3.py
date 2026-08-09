#!/usr/bin/env python3
"""Sprint 3.3 verification: unit tests + vendor/BOM/review/Complete smoke.

Usage (backend must be running for the API smoke section):
  python3 scripts/verify_sprint_3_3.py
  python3 scripts/verify_sprint_3_3.py --unit-only
  python3 scripts/verify_sprint_3_3.py --smoke-only

Flow: login → project → upload → Draft RKM → gap/answers → approve → publish
→ domains/analyze → architectures/generate → catalogue seed → map-products
→ BOM import/validate → architectures/review → approve/Complete gate
(+ singular alias regression).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "http://localhost:8000"
BACKEND = ROOT / "backend"
PYTEST = BACKEND / ".venv" / "bin" / "python"

# Reuse Sprint 3.2 helpers (req/ok/wait_job/clear_gap_blockers/RICH_RFP).
_V32_PATH = ROOT / "scripts" / "verify_sprint_3_2.py"
_spec = importlib.util.spec_from_file_location("verify_sprint_3_2", _V32_PATH)
if _spec is None or _spec.loader is None:
    raise SystemExit(f"FAIL: cannot load {_V32_PATH}")
_v32 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v32)

req = _v32.req
ok = _v32.ok
wait_job = _v32.wait_job
clear_gap_blockers = _v32.clear_gap_blockers
RICH_RFP = _v32.RICH_RFP

UNIT_FOCUS = [
    "tests/test_phase3_vendor_bom_schema.py",
    "tests/test_phase3_vendor_bom_schemas.py",
    "tests/test_phase3_vendor_seed.py",
    "tests/test_vendor_catalogue_repository.py",
    "tests/test_vendor_catalogue_service.py",
    "tests/test_v1_vendors_routes.py",
    "tests/test_architecture_product_mapping_repository.py",
    "tests/test_architecture_product_mapping_service.py",
    "tests/test_architecture_product_matching.py",
    "tests/test_bom_repository.py",
    "tests/test_bom_service.py",
    "tests/test_bom_validation.py",
    "tests/test_bom_validation_service.py",
    "tests/test_v1_bom_routes.py",
    "tests/test_architecture_review_service.py",
    "tests/test_architecture_option_review_repository.py",
    "tests/test_v1_architectures_routes.py",
]


def run_unit_tests(*, focused: bool = False) -> None:
    python = str(PYTEST if PYTEST.exists() else sys.executable)
    args = [python, "-m", "pytest", "-q"]
    if focused:
        existing = [path for path in UNIT_FOCUS if (BACKEND / path).exists()]
        if not existing:
            raise SystemExit("FAIL: no Sprint 3.3 unit test files found")
        args.extend(existing)
        print(f"=== unit tests focused ({len(existing)} files) ===", flush=True)
    else:
        print(f"=== unit tests ({python} -m pytest -q) ===", flush=True)
    result = subprocess.run(args, cwd=str(BACKEND), check=False)
    if result.returncode != 0:
        raise SystemExit("FAIL: pytest suite")
    print("UNIT_TESTS_OK")


def _error_message(payload: dict) -> str:
    return str(
        (payload.get("error") or {}).get("message")
        or payload.get("message")
        or payload.get("detail")
        or payload.get("raw")
        or payload,
    )


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
    if role != "approver":
        raise SystemExit(
            f"FAIL: demo user must be approver for Complete gate (got {role})",
        )

    stamp = int(time.time()) % 100000
    status, payload = req(
        "POST",
        "/api/projects",
        token=token,
        data={
            "project_name": f"Sprint 3.3 Verify {stamp}",
            "customer": "Acme Corp",
            "industry": "Technology",
            "deal_id": f"S33{stamp}",
            "deal_name": "Sprint 3.3 Vendor BOM Approve",
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
        "POST",
        f"/api/v1/projects/{project_id}/requirements/approve",
        token=token,
        data={"note": "Sprint 3.3 verify"},
    )
    ok(status, payload, "rkm_approve")

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/publish",
        token=token,
        data={"note": "Sprint 3.3 verify publish"},
    )
    published = ok(status, payload, "rkm_publish")
    print("published:", published.get("version_label"))

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/domains/analyze",
        token=token,
        data={},
    )
    analysis = ok(status, payload, "domains_analyze")
    if not (analysis.get("domains") or []):
        raise SystemExit("FAIL: analyze returned zero domains")

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/architectures/generate",
        token=token,
        data={},
    )
    generated = ok(status, payload, "architectures_generate")
    options = generated.get("architectures") or []
    if not options:
        raise SystemExit("FAIL: generate returned zero architecture candidates")
    print(
        "candidates:",
        len(options),
        [item.get("candidate_key") for item in options],
    )

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/architectures",
        token=token,
    )
    listed = ok(status, payload, "architectures_list")
    preferred = next(
        (item for item in listed if item.get("candidate_key") == "standard"),
        listed[0],
    )
    arch_id = preferred["id"]

    # --- Sprint 3.3: catalogue ---
    status, payload = req(
        "POST",
        "/api/v1/vendors/catalogue/seed",
        token=token,
        data={},
    )
    catalogue = ok(status, payload, "catalogue_seed")
    print(
        "catalogue:",
        catalogue.get("name"),
        "products:",
        catalogue.get("product_count"),
    )
    if int(catalogue.get("product_count") or 0) < 1:
        raise SystemExit("FAIL: seed catalogue has no products")

    status, payload = req(
        "GET",
        "/api/v1/vendors/catalogue/search?q=RN-AP-6E&limit=5",
        token=token,
    )
    search = ok(status, payload, "catalogue_search")
    hits = search.get("products") or []
    print("search_hits:", len(hits), "total:", search.get("total"))
    if not hits:
        raise SystemExit("FAIL: catalogue search returned no RN-AP-6E hits")

    # --- map products ---
    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/architectures/{arch_id}/map-products",
        token=token,
        data={},
    )
    mapped = ok(status, payload, "map_products")
    mappings = mapped.get("mappings") or []
    print(
        "mappings:",
        len(mappings),
        "unmatched:",
        len(mapped.get("unmatched_component_ids") or []),
    )

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/architectures/{arch_id}/product-mappings",
        token=token,
    )
    listed_maps = ok(status, payload, "list_product_mappings")
    print("listed_mappings:", len(listed_maps))

    if mappings:
        mapping_id = mappings[0]["id"]
        status, payload = req(
            "PATCH",
            f"/api/v1/projects/{project_id}/product-mappings/{mapping_id}",
            token=token,
            data={"status": "selected"},
        )
        selected = ok(status, payload, "select_product_mapping")
        if selected.get("status") != "selected":
            raise SystemExit("FAIL: expected mapping status selected")

    # --- BOM import + validate ---
    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/bom/import",
        token=token,
        data={
            "source": "Sprint 3.3 verify distributor quote",
            "source_filename": "verify-bom.csv",
            "architecture_id": arch_id,
            "items": [
                {
                    "line_number": 1,
                    "vendor": "RefNet",
                    "product_model": "RN-AP-6E",
                    "quantity": 24,
                    "unit": "ea",
                    "category": "wireless_ap",
                    "description": "Access point",
                },
                {
                    "line_number": 2,
                    "vendor": "RefNet",
                    "product_model": "RN-ACC-48P",
                    "quantity": 4,
                    "unit": "ea",
                    "category": "access_switch",
                    "description": "Access switch",
                },
                {
                    "line_number": 3,
                    "vendor": "UnknownCo",
                    "product_model": "UX-UNKNOWN-1",
                    "quantity": None,
                    "description": "Unmapped line for validation flags",
                },
            ],
        },
    )
    bom = ok(status, payload, "bom_import")
    bom_id = bom["id"]
    print("bom_import:", bom_id, "items:", bom.get("item_count"))
    if int(bom.get("item_count") or 0) < 3:
        raise SystemExit("FAIL: expected 3 BOM items")

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/bom/{bom_id}/validate",
        token=token,
        data={"architecture_id": arch_id},
    )
    validation = ok(status, payload, "bom_validate")
    print(
        "bom_validation:",
        validation.get("status"),
        "issues:",
        len(validation.get("issues") or []),
    )
    if not (validation.get("issues") or []):
        raise SystemExit("FAIL: expected validation issues for unknown/missing qty")

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/bom/{bom_id}/validation",
        token=token,
    )
    latest = ok(status, payload, "bom_validation_get")
    if latest.get("id") != validation.get("id"):
        raise SystemExit("FAIL: latest validation id mismatch")

    # --- review + Complete gate ---
    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/architectures/{arch_id}/review",
        token=token,
        data={"note": "Sprint 3.3 verify human review"},
    )
    review = ok(status, payload, "architectures_review")
    if review.get("status") != "under_review":
        raise SystemExit(f"FAIL: expected under_review, got {review.get('status')}")
    uncovered = int(review.get("uncovered_critical_count") or 0)
    print("under_review uncovered_critical_count:", uncovered)

    status, payload = req(
        "POST",
        f"/api/v1/projects/{project_id}/architectures/{arch_id}/approve",
        token=token,
        data={"note": "Sprint 3.3 verify Complete"},
    )
    if uncovered > 0:
        print(f"=== architectures_approve_gate [{status}] ===")
        if status < 400 or payload.get("success"):
            print(json.dumps(payload, indent=2)[:2000])
            raise SystemExit(
                "FAIL: expected Complete hard-fail when uncovered critical/high > 0",
            )
        gate_msg = _error_message(payload)
        if "Cannot Complete" not in gate_msg and "uncovered" not in gate_msg.lower():
            print(gate_msg)
            raise SystemExit("FAIL: Complete gate message missing uncovered signal")
        print("complete_gate_ok:", gate_msg)
    else:
        approved = ok(status, payload, "architectures_approve")
        if approved.get("status") != "complete":
            raise SystemExit(
                f"FAIL: expected complete, got {approved.get('status')}",
            )
        print("complete_ok: uncovered_critical_count=0")

    # Approve without review on a fresh candidate should fail.
    other = next(
        (item for item in listed if item["id"] != arch_id),
        None,
    )
    if other is not None and other.get("status") not in {"under_review", "complete", "approved"}:
        status, payload = req(
            "POST",
            f"/api/v1/projects/{project_id}/architectures/{other['id']}/approve",
            token=token,
            data={},
        )
        print(f"=== approve_without_review [{status}] ===")
        if status < 400 or payload.get("success"):
            raise SystemExit("FAIL: expected approve without under_review to fail")
        print("review_required_ok:", _error_message(payload))

    # Singular aliases still present through 3.3.
    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/architecture",
        token=token,
    )
    alias = ok(status, payload, "architecture_alias_get")
    if not alias.get("id"):
        raise SystemExit("FAIL: singular architecture alias missing id")

    status, payload = req(
        "GET",
        f"/api/v1/projects/{project_id}/audit-logs?limit=80",
        token=token,
    )
    logs = ok(status, payload, "audit_logs")
    actions = {row.get("action") for row in logs}
    required = {
        "architectures.generate",
        "architectures.map_products",
        "architectures.review",
        "bom.import",
        "bom.validate",
        "rkm.publish",
    }
    missing = required - actions
    if missing:
        raise SystemExit(f"FAIL: missing audit actions {missing}")
    # approve may be absent when hard-gated — either approve or gate is fine
    if uncovered == 0 and "architectures.approve" not in actions:
        raise SystemExit("FAIL: missing architectures.approve audit after Complete")

    print("SPRINT_3_3_VERIFY_OK")
    print("UI:", f"http://localhost:3000/projects/{project_id}")
    return project_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Sprint 3.3")
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
    parser.add_argument(
        "--focused-unit",
        action="store_true",
        help="Run Sprint 3.3-focused pytest files only (faster)",
    )
    args = parser.parse_args()

    if not args.smoke_only:
        run_unit_tests(focused=args.focused_unit)
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

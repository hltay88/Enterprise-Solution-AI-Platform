#!/usr/bin/env python3
"""Seed published demo knowledge for Atlas Mac demo harden.

Usage (Atlas running on localhost):
  python3 scripts/seed_demo_knowledge.py

Idempotent by title prefix: skips items that already exist with the same title.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://localhost:8000"
EMAIL = "demo@example.com"
PASSWORD = "changeme"

# (domain_code, title, relative path under repo, optional extra guidance)
PACKS: list[tuple[str, str, str, str]] = [
    (
        "networking",
        "[Demo] Networking campus design guidance",
        "knowledge/networking/overview.md",
        "\n\n## Advisory baseline\nPrefer hierarchical campus design, dual-homed access, and explicit VLAN segmentation for users, servers, guests, and OT. Record uplink oversubscription and management plane tools as evidence before sizing.",
    ),
    (
        "wireless",
        "[Demo] Wireless high-density Wi-Fi guidance",
        "knowledge/wireless/overview.md",
        "\n\n## Advisory baseline\nSeparate corporate and guest SSIDs, enforce 802.1X where practical, and validate capacity with concurrent client targets. Confirm wired uplink and NAC integration before AP placement.",
    ),
    (
        "cybersecurity",
        "[Demo] Cybersecurity zero-trust guidance",
        "knowledge/phase3/domains/cybersecurity/overview.md",
        "\n\n## Advisory baseline\nApply least privilege, network segmentation, and identity-centric controls. Surface shared-responsibility gaps for hybrid cloud and outdoor/IoT edges. Do not invent unsupported products.",
    ),
    (
        "cloud",
        "[Demo] Cloud landing-zone guidance",
        "knowledge/phase3/domains/cloud/overview.md",
        "\n\n## Advisory baseline\nClarify provider, region/residency, and connectivity (internet vs private interconnect). Align identity, security edge, and backup/DR with the landing-zone model before recommending SKUs.",
    ),
    (
        "storage",
        "[Demo] Storage architecture guidance",
        "knowledge/phase3/domains/storage/overview.md",
        "\n\n## Advisory baseline\nCapture capacity, IOPS/latency targets, protocols (block/file/object), and growth assumptions. Align snapshot/replication ownership with backup/DR requirements.",
    ),
    (
        "data_centre",
        "[Demo] Data centre fabric guidance",
        "knowledge/phase3/domains/data_centre/overview.md",
        "\n\n## Advisory baseline\nDocument power/cooling budgets, rack density, leaf-spine vs three-tier fabric, and east-west traffic expectations before BOM sizing.",
    ),
]


def _req(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from exc
    if not payload.get("success", True) and "data" not in payload:
        raise RuntimeError(f"{method} {path} failed: {payload}")
    return payload


def login() -> str:
    payload = _req(
        "POST",
        "/api/auth/login",
        body={"email": EMAIL, "password": PASSWORD},
    )
    data = payload.get("data") or payload
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"login missing token: {payload}")
    return token


def existing_titles(token: str) -> set[str]:
    payload = _req("GET", "/api/v1/knowledge?limit=200", token=token)
    rows = payload.get("data") or []
    return {str(r.get("title") or "") for r in rows}


def publish_item(token: str, domain: str, title: str, content: str) -> str:
    created = _req(
        "POST",
        "/api/v1/knowledge/json",
        token=token,
        body={
            "title": title,
            "description": f"Demo harden seed for {domain}",
            "domain_code": domain,
            "knowledge_type": "best_practice",
            "sensitivity": "internal",
            "content_text": content,
            "change_summary": "Demo seed",
            "tags": ["demo", "seed", domain],
        },
    )
    item = created["data"]
    kid = item["id"]
    _req("POST", f"/api/v1/knowledge/{kid}/submit-review", token=token, body={})
    _req("POST", f"/api/v1/knowledge/{kid}/approve", token=token, body={})
    _req("POST", f"/api/v1/knowledge/{kid}/publish", token=token, body={})
    return kid


def smoke_retrieval(token: str) -> None:
    for query, domain in (
        ("campus VLAN segmentation uplink oversubscription", "networking"),
        ("Wi-Fi high density SSID NAC", "wireless"),
        ("zero trust segmentation identity", "cybersecurity"),
        ("cloud landing zone hybrid connectivity", "cloud"),
    ):
        result = _req(
            "POST",
            "/api/v1/retrieval/search",
            token=token,
            body={"query": query, "domain_code": domain, "top_k": 3, "min_score": 0.0},
        )
        data = result["data"]
        hits = data.get("hits") or []
        print(
            f"  retrieval[{domain}]: hits={len(hits)} insufficient={data.get('insufficient_evidence')}",
        )


def smoke_agents(token: str) -> None:
    projects = _req("GET", "/api/projects", token=token)
    rows = projects.get("data") or projects
    if not rows:
        print("  agents: no project available — skip")
        return
    project_id = rows[0]["id"]
    run = _req(
        "POST",
        f"/api/v1/projects/{project_id}/agent-runs",
        token=token,
        body={
            "goal": "Demo harden smoke after knowledge seed",
            "include_agents": ["networking", "wireless", "security", "cloud"],
        },
    )
    data = run["data"]
    statuses = [f"{s['agent_id']}:{s['status']}" for s in data.get("specialists") or []]
    print(f"  agents: {data.get('status')} {statuses}")


def main() -> int:
    print(f"Seeding demo knowledge against {BASE} …")
    token = login()
    known = existing_titles(token)
    created = 0
    skipped = 0
    for domain, title, rel, extra in PACKS:
        if title in known:
            print(f"skip  {domain}: already exists — {title}")
            skipped += 1
            continue
        path = ROOT / rel
        if not path.exists():
            print(f"MISS  {domain}: file not found {rel}", file=sys.stderr)
            return 1
        content = path.read_text(encoding="utf-8") + extra
        kid = publish_item(token, domain, title, content)
        print(f"ok    {domain}: published {kid}")
        created += 1

    print(f"\nSeed complete: created={created} skipped={skipped}")
    print("Smoke — retrieval")
    smoke_retrieval(token)
    print("Smoke — agents")
    smoke_agents(token)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

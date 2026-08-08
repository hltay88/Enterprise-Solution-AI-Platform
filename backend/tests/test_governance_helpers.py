"""Stage E governance unit tests (no DB)."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, ValidationAppError
from app.schemas.gap import GapItem, PublishBlocker
from app.schemas.governance import ApproveIn, PublishIn, RequirementEditIn, ReviewIn
from app.services.rkm_governance_service import RkmGovernanceService


def _payload(*, approval_status: str = "ai_generated", req_id: str | None = None) -> dict:
    rid = req_id or str(uuid4())
    return {
        "id": str(uuid4()),
        "project_id": str(uuid4()),
        "project": {
            "project_name": "Stage E Test",
            "customer": "Acme",
            "industry": "Technology",
            "account_manager": None,
            "deal_id": "D-1",
            "deal_name": "Deal",
            "request_type": "Initial Discovery",
            "required_completion_date": None,
            "budget_information": None,
            "winning_probability": None,
        },
        "business_objectives": [
            {
                "id": rid,
                "title": "Improve WiFi",
                "description": "Better coverage",
                "priority": "high",
                "status": "draft",
                "confidence": 80,
                "evidence_ids": [],
            }
        ],
        "current_environment": {"summary": "Legacy APs", "items": []},
        "functional_requirements": [
            {
                "id": str(uuid4()),
                "title": "WiFi 6",
                "description": "Campus coverage",
                "priority": "high",
                "status": "draft",
                "confidence": 85,
                "evidence_ids": [],
            }
        ],
        "non_functional_requirements": [
            {
                "id": str(uuid4()),
                "title": "Uptime",
                "description": "99.9%",
                "priority": "high",
                "status": "draft",
                "confidence": 80,
                "evidence_ids": [],
            }
        ],
        "constraints": [],
        "dependencies": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [
            {
                "id": str(uuid4()),
                "name": "IT Director",
                "role": "Approver",
                "contact": None,
                "designation": None,
                "evidence_ids": [],
            }
        ],
        "clarification_questions": [],
        "evidence": [],
        "analysis": {
            "confidence_score": 90,
            "completeness_score": 90,
            "consistency_score": 90,
            "evidence_coverage": 90,
            "reasoning_summary": "Derived from intake",
            "prompt_version": "test",
            "model": "test",
        },
        "approval": {
            "status": approval_status,
            "reviewed_by": None,
            "approved_by": None,
            "approved_at": None,
            "published_at": None,
        },
        "version": {
            "number": "1.0.0",
            "major": 1,
            "minor": 0,
            "patch": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "change_summary": None,
        },
    }


def test_apply_edits_updates_title_and_description():
    service = RkmGovernanceService.__new__(RkmGovernanceService)
    req_id = str(uuid4())
    payload = _payload(req_id=req_id)
    edited = service._apply_edits(
        payload,
        [
            RequirementEditIn(
                id=req_id,
                title="Improve campus WiFi",
                description="Seamless roaming across 3 floors",
                priority="critical",
            )
        ],
    )
    assert edited == 1
    item = payload["business_objectives"][0]
    assert item["title"] == "Improve campus WiFi"
    assert "Seamless roaming" in item["description"]
    assert item["priority"] == "critical"


def test_diff_payloads_detects_modified_requirement():
    service = RkmGovernanceService.__new__(RkmGovernanceService)
    left = _payload()
    right = _payload()
    right["business_objectives"][0]["title"] = left["business_objectives"][0]["title"]
    right["business_objectives"][0]["description"] = "Changed description"
    diffs = service._diff_payloads(left, right)
    assert any(d.change_type == "modified" and d.section == "business_objectives" for d in diffs)


def test_require_mutable_draft_blocks_published():
    service = RkmGovernanceService.__new__(RkmGovernanceService)

    class Repo:
        def ensure_active_draft(self, _project_id):
            return SimpleNamespace(
                status="published",
                is_active_draft=False,
                payload_json={"approval": {"status": "published"}},
            )

    service.rkms = Repo()
    with pytest.raises(ConflictError):
        service._require_mutable_draft(uuid4())


def test_publish_raises_when_blockers_present(monkeypatch):
    service = RkmGovernanceService.__new__(RkmGovernanceService)
    payload = _payload(approval_status="ai_generated")
    row = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        version_label="1.0.0",
        payload_json=payload,
        status="ai_generated",
        is_active_draft=True,
        reasoning_summary="",
    )

    class Projects:
        def get_for_user(self, project_id, user_id):
            return SimpleNamespace(id=project_id)

    class Gap:
        def _build_report(self, **_kwargs):
            return SimpleNamespace(
                publish_blockers=[
                    PublishBlocker(code="human_approval_required", message="need approval"),
                ],
            )

    class FakeAudit:
        def __init__(self, _db):
            pass

        def record(self, **_kwargs):
            return None

    monkeypatch.setattr(
        "app.services.rkm_governance_service.AuditService",
        FakeAudit,
    )
    service.projects = Projects()
    service.gap = Gap()
    service.rkms = SimpleNamespace(
        ensure_active_draft=lambda _pid: row,
    )
    actor = SimpleNamespace(email="demo@example.com")
    with pytest.raises(ValidationAppError) as exc:
        service.publish(row.project_id, uuid4(), PublishIn(), actor)
    assert "Publish blocked" in str(exc.value)


def test_approve_stamps_approval_in_place(monkeypatch):
    service = RkmGovernanceService.__new__(RkmGovernanceService)
    payload = _payload(approval_status="under_review")
    row = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        version_label="1.0.0",
        payload_json=payload,
        status="under_review",
        is_active_draft=True,
        reasoning_summary="Derived from intake",
        updated_at=None,
    )
    committed = {"ok": False}

    class Projects:
        def get_for_user(self, project_id, user_id):
            return SimpleNamespace(id=project_id)

    class Db:
        def add(self, _row):
            return None

        def commit(self):
            committed["ok"] = True

        def refresh(self, _row):
            return None

    class FakeAudit:
        def __init__(self, _db):
            pass

        def record(self, **_kwargs):
            return None

    monkeypatch.setattr(
        "app.services.rkm_governance_service.AuditService",
        FakeAudit,
    )
    service.projects = Projects()
    service.db = Db()
    service.rkms = SimpleNamespace(ensure_active_draft=lambda _pid: row)
    actor = SimpleNamespace(email="approver@example.com")
    result = service.approve(row.project_id, uuid4(), ApproveIn(note="Looks good"), actor)
    assert committed["ok"] is True
    assert result.status == "approved"
    assert result.approved_by == "approver@example.com"
    assert row.status == "approved"
    assert row.payload_json["approval"]["status"] == "approved"
    assert "Approval note: Looks good" in row.payload_json["analysis"]["reasoning_summary"]


def test_review_requires_edits_or_note():
    service = RkmGovernanceService.__new__(RkmGovernanceService)
    payload = _payload()
    row = SimpleNamespace(
        status="ai_generated",
        is_active_draft=True,
        payload_json=payload,
    )

    class Projects:
        def get_for_user(self, project_id, user_id):
            return SimpleNamespace(id=project_id)

    service.projects = Projects()
    service.rkms = SimpleNamespace(ensure_active_draft=lambda _pid: row)
    with pytest.raises(ValidationAppError):
        service.review(uuid4(), uuid4(), ReviewIn(), SimpleNamespace(email="a@b.com"))

"""Sprint 5.1 — knowledge lifecycle transition unit tests (no DB)."""

from app.constants.knowledge_lifecycle import (
    STATUS_APPROVED,
    STATUS_ARCHIVED,
    STATUS_DEPRECATED,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_REVIEW,
    can_transition,
)
from app.constants.knowledge_taxonomy import TAXONOMY_CODES, resolve_domain_code, taxonomy_choices
from app.constants.knowledge_types import KNOWLEDGE_TYPE_CODES, normalize_knowledge_type
from app.services.knowledge_service import KnowledgeService


def test_lifecycle_happy_path_transitions():
    assert can_transition(STATUS_DRAFT, STATUS_REVIEW)
    assert can_transition(STATUS_REVIEW, STATUS_APPROVED)
    assert can_transition(STATUS_APPROVED, STATUS_PUBLISHED)
    assert can_transition(STATUS_PUBLISHED, STATUS_DEPRECATED)
    assert can_transition(STATUS_DEPRECATED, STATUS_ARCHIVED)


def test_lifecycle_rejects_skip_and_edit_published():
    assert not can_transition(STATUS_DRAFT, STATUS_PUBLISHED)
    assert not can_transition(STATUS_PUBLISHED, STATUS_DRAFT)
    assert not can_transition(STATUS_PUBLISHED, STATUS_APPROVED)
    assert not can_transition(STATUS_ARCHIVED, STATUS_DRAFT)


def test_review_can_return_to_draft():
    assert can_transition(STATUS_REVIEW, STATUS_DRAFT)


def test_taxonomy_seed_covers_phase5_domains():
    choices = taxonomy_choices()
    codes = {c["code"] for c in choices}
    required = {
        "networking",
        "wireless",
        "cybersecurity",
        "cloud",
        "data_centre",
        "compute",
        "storage",
        "backup",
        "hci",
        "av",
        "led_videowall",
        "digital_signage",
        "billboard",
        "smart_building",
        "iot",
    }
    assert required <= codes
    assert required <= TAXONOMY_CODES


def test_resolve_domain_aliases():
    assert resolve_domain_code("wifi") == "wireless"
    assert resolve_domain_code("Cybersecurity") == "cybersecurity"
    assert resolve_domain_code("led_video_wall") == "led_videowall"
    assert resolve_domain_code("unknown_xyz") is None


def test_knowledge_types_normalize():
    assert normalize_knowledge_type("Best Practice") == "best_practice"
    assert "reference_architecture" in KNOWLEDGE_TYPE_CODES


def test_classify_domain_from_text():
    svc = KnowledgeService.__new__(KnowledgeService)
    assert svc.classify_domain("Campus Wi-Fi design guide for high density") == "wireless"
    assert svc.classify_domain("Zero trust cybersecurity controls") == "cybersecurity"
    assert svc.classify_domain("") == "networking"

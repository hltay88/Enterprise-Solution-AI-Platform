"""Sprint 3.1 Task 5 — Phase 3 knowledge pack interface."""

from __future__ import annotations

import pytest

from app.services.knowledge_packs import build_knowledge_pack_context
from app.services.phase3_domain_catalog import clear_catalog_cache
from app.services.phase3_knowledge_packs import (
    build_domain_pack_context,
    detect_phase3_domains,
    list_domain_catalog,
    list_phase3_pack_dirs,
    pack_version,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_catalog_cache()
    yield
    clear_catalog_cache()


def test_pack_version_stable():
    assert pack_version() == "1.0.0"


def test_list_domain_catalog_includes_required_codes():
    codes = {entry.code for entry in list_domain_catalog()}
    assert "wifi" in codes
    assert "campus_lan" in codes
    assert "ztna_vpn" in codes


def test_detect_wifi_from_text_and_phase2_bridge():
    codes = detect_phase3_domains(
        "Customer needs enterprise WiFi 6 coverage across three floors",
    )
    assert "wifi" in codes


def test_build_domain_pack_context_includes_stub_and_emission_rule():
    context = build_domain_pack_context(
        "Enterprise wireless WLAN coverage and roaming requirements",
    )
    assert "pack_version: 1.0.0" in context
    assert "emission_rule" in context
    assert "wifi" in context.lower()
    assert "vendor-neutral" in context.lower()
    assert "overview.md" in context or "When this domain applies" in context


def test_build_domain_pack_context_candidate_codes_catalog_only_for_missing_pack():
    # audio_visual is in catalog but may have no overview stub directory content
    # beyond missing dir — still must return catalog metadata.
    context = build_domain_pack_context(candidate_codes=["audio_visual"])
    assert "audio_visual" in context
    assert "pack_version: 1.0.0" in context
    assert "catalog_code: audio_visual" in context


def test_build_domain_pack_context_unrelated_text_still_returns_rule():
    context = build_domain_pack_context("Office furniture refresh and paint colors only")
    assert "pack_version: 1.0.0" in context
    assert "No domain packs matched" in context or "emission_rule" in context


def test_ignores_unknown_candidate_codes():
    context = build_domain_pack_context(candidate_codes=["not-a-domain", "wifi"])
    assert "wifi" in context.lower()
    assert "not-a-domain" not in context


def test_list_phase3_pack_dirs_includes_priority_stubs():
    dirs = list_phase3_pack_dirs()
    assert "wifi" in dirs
    assert "campus_lan" in dirs


def test_stage_f_knowledge_packs_still_work():
    context = build_knowledge_pack_context(
        "Customer needs enterprise WiFi 6 coverage across 3 floors with seamless roaming",
    )
    assert context
    assert "wireless" in context.lower() or "Wi" in context

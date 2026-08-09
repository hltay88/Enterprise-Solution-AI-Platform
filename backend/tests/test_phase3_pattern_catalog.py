"""Sprint 3.2 Task 1 — Phase 3 architecture pattern catalog freeze."""

from __future__ import annotations

import pytest

from app.services.phase3_domain_catalog import (
    catalog_version,
    clear_catalog_cache,
    list_domain_codes,
)
from app.services.phase3_pattern_catalog import (
    REQUIRED_DOC_PATTERN_CODES,
    PatternCatalogError,
    clear_pattern_catalog_cache,
    list_pattern_codes,
    load_pattern_catalog,
    pattern_catalog_path,
    pattern_pack_dir,
    patterns_for_domains,
    require_pattern_code,
    resolve_pattern_code,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_catalog_cache()
    clear_pattern_catalog_cache()
    yield
    clear_catalog_cache()
    clear_pattern_catalog_cache()


def test_pattern_catalog_version_matches_phase3_version():
    assert catalog_version() == "1.1.0"
    catalog = load_pattern_catalog()
    assert catalog.catalog_version == catalog_version()
    assert pattern_catalog_path().is_file()


def test_catalog_contains_all_doc_05_patterns():
    codes = load_pattern_catalog().codes()
    missing = REQUIRED_DOC_PATTERN_CODES - codes
    assert not missing, f"Missing required pattern codes: {sorted(missing)}"


def test_emission_rule_present():
    catalog = load_pattern_catalog()
    assert "catalog" in catalog.emission_rule.lower()
    assert "recommendation" in catalog.emission_rule.lower() or "mandatory" in catalog.emission_rule.lower()


def test_related_domains_reference_domain_catalog_only():
    domain_codes = set(list_domain_codes())
    for pattern in load_pattern_catalog().patterns:
        for code in pattern.related_domain_codes:
            assert code in domain_codes, f"{pattern.code} unknown domain {code}"


def test_resolve_alias_to_code():
    assert resolve_pattern_code("SD-WAN") == "sdwan"
    assert resolve_pattern_code("enterprise wifi") == "wireless_enterprise"
    assert resolve_pattern_code("Zero Trust") == "zero_trust"
    assert resolve_pattern_code("not-a-real-pattern") is None


def test_require_pattern_code_rejects_unknown():
    with pytest.raises(PatternCatalogError, match="Unknown Phase 3 pattern"):
        require_pattern_code("cisco-sdwan-magic")


def test_patterns_for_domains_filters():
    matched = patterns_for_domains(["wifi", "campus_lan"])
    codes = {item.code for item in matched}
    assert "wireless_enterprise" in codes
    assert "two_tier_campus" in codes or "three_tier_campus" in codes
    assert "led_video_wall" not in codes


def test_priority_pattern_stubs_exist():
    for code in (
        "wireless_enterprise",
        "two_tier_campus",
        "sdwan",
        "zero_trust",
        "backup_dr",
    ):
        overview = pattern_pack_dir(code) / "overview.md"
        assert overview.is_file(), f"missing stub {overview}"


def test_list_pattern_codes_sorted():
    codes = list_pattern_codes()
    assert codes == sorted(codes)
    assert "wireless_enterprise" in codes

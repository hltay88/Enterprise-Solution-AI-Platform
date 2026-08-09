"""Sprint 3.1 Task 1 — Phase 3 domain catalog freeze."""

from __future__ import annotations

import json

import pytest

from app.services.phase3_domain_catalog import (
    REQUIRED_DOC_CODES,
    DomainCatalogError,
    catalog_path,
    catalog_version,
    clear_catalog_cache,
    domain_pack_dir,
    list_domain_codes,
    load_domain_catalog,
    require_domain_code,
    resolve_domain_code,
    version_file_path,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_catalog_cache()
    yield
    clear_catalog_cache()


def test_catalog_version_matches_version_file():
    assert catalog_version() == "1.1.0"
    assert version_file_path().is_file()
    catalog = load_domain_catalog()
    assert catalog.catalog_version == catalog_version()


def test_catalog_contains_all_doc_02_domains():
    codes = load_domain_catalog().codes()
    missing = REQUIRED_DOC_CODES - codes
    assert not missing, f"Missing required domain codes: {sorted(missing)}"


def test_catalog_includes_remote_access_example_domains():
    codes = load_domain_catalog().codes()
    assert "ztna_vpn" in codes
    assert "security_edge" in codes


def test_emission_rule_and_dependency_vocabulary():
    catalog = load_domain_catalog()
    assert "only emit domain codes" in catalog.emission_rule.lower() or "catalog" in catalog.emission_rule.lower()
    assert "required" in catalog.dependency_kinds
    assert "recommended" in catalog.dependency_kinds
    assert "requirement" in catalog.selection_sources
    assert "dependency" in catalog.selection_sources
    assert "optional_alternative" in catalog.selection_sources


def test_typical_dependencies_reference_catalog_codes_only():
    catalog = load_domain_catalog()
    codes = catalog.codes()
    for domain in catalog.domains:
        for dep in domain.typical_dependencies:
            assert dep in codes, f"{domain.code} has unknown dependency {dep}"


def test_resolve_alias_to_code():
    assert resolve_domain_code("Wi-Fi") == "wifi"
    assert resolve_domain_code("wireless") == "wifi"
    assert resolve_domain_code("wifi") == "wifi"
    assert resolve_domain_code("Campus LAN") == "campus_lan"
    assert resolve_domain_code("not-a-real-domain") is None


def test_require_domain_code_rejects_unknown():
    with pytest.raises(DomainCatalogError, match="Unknown Phase 3 domain"):
        require_domain_code("cisco-catalyst-magic")


def test_priority_pack_stubs_exist():
    for code in (
        "wifi",
        "campus_lan",
        "cybersecurity",
        "identity",
        "cloud",
        "data_centre",
        "collaboration",
        "digital_signage",
        "backup_dr",
        "wan_sdwan",
        "compute",
        "storage",
    ):
        overview = domain_pack_dir(code) / "overview.md"
        assert overview.is_file(), f"Missing stub: {overview}"
        text = overview.read_text(encoding="utf-8")
        assert "vendor-neutral" in text.lower()


def test_list_domain_codes_sorted_non_empty():
    codes = list_domain_codes()
    assert codes == sorted(codes)
    assert len(codes) >= len(REQUIRED_DOC_CODES)


def test_catalog_json_is_object_with_domains_array():
    raw = json.loads(catalog_path().read_text(encoding="utf-8"))
    assert isinstance(raw.get("domains"), list)
    assert len(raw["domains"]) >= len(REQUIRED_DOC_CODES)

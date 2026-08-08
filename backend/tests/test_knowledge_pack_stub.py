from app.services.knowledge_packs import (
    build_knowledge_pack_context,
    list_available_pack_dirs,
)


def test_knowledge_pack_dirs_include_networking_and_wireless():
    dirs = list_available_pack_dirs()
    assert "networking" in dirs
    assert "wireless" in dirs


def test_build_knowledge_pack_context_for_wifi_text():
    context = build_knowledge_pack_context(
        "Customer needs enterprise WiFi 6 coverage across 3 floors with seamless roaming",
    )
    assert context
    assert "vendor-neutral" in context.lower() or "Vendor-neutral" in context
    assert "wireless" in context.lower() or "Wi" in context
    assert "mandatory" in context.lower() or "coverage" in context.lower()


def test_build_knowledge_pack_context_empty_for_unrelated_text():
    context = build_knowledge_pack_context("Office furniture refresh and paint colors only")
    assert context == ""

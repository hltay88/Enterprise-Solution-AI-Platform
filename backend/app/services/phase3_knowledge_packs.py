"""Phase 3 Knowledge Pack interface for Solution Domain Identification.

Sprint 3.1 Task 5 — catalog-driven pack context for Published RKM text.
Does not replace Stage F ``knowledge_packs.build_knowledge_pack_context``.
This is not RAG: packs enrich prompts only.
"""

from __future__ import annotations

import re

from app.services.domain_checklists import detect_domains
from app.services.phase3_domain_catalog import (
    DomainCatalogEntry,
    DomainCatalogError,
    catalog_version,
    load_domain_catalog,
    phase3_root,
    require_domain_code,
)

STUB_FILES = ("overview.md", "dependencies.md", "selection_notes.md")
MAX_PACKS = 5
MAX_CHARS_PER_FILE = 1200
MAX_TOTAL_CHARS = 5000


def pack_version() -> str:
    """Stable Phase 3 knowledge pack / catalog version for audit metadata."""
    return catalog_version()


def list_domain_catalog() -> list[DomainCatalogEntry]:
    """Return frozen Phase 3 domain catalog entries."""
    return list(load_domain_catalog().domains)


def detect_phase3_domains(*text_blobs: str) -> list[str]:
    """Detect Phase 3 domain codes from text using catalog aliases + Phase 2 bridge."""
    blob = " ".join(part for part in text_blobs if part)
    blob_norm = f" {re.sub(r'\s+', ' ', blob.lower())} "
    if not blob_norm.strip():
        return []

    catalog = load_domain_catalog()
    matched: list[str] = []
    seen: set[str] = set()

    # Phase 2 checklist bridge (wireless → wifi, etc.)
    phase2_hits = set(detect_domains(*text_blobs))
    for entry in catalog.domains:
        if any(pid in phase2_hits for pid in entry.phase2_checklist_ids):
            if entry.code not in seen:
                seen.add(entry.code)
                matched.append(entry.code)

    # Catalog code / name / alias keyword hits (longer needles first).
    needles: list[tuple[str, str]] = []
    for entry in catalog.domains:
        needles.append((entry.code.replace("_", " "), entry.code))
        needles.append((entry.code, entry.code))
        needles.append((entry.name.lower(), entry.code))
        for alias in entry.aliases:
            needles.append((alias.lower(), entry.code))
    needles.sort(key=lambda item: len(item[0]), reverse=True)

    for needle, code in needles:
        if code in seen:
            continue
        if not needle.strip():
            continue
        if _contains_needle(blob_norm, needle):
            seen.add(code)
            matched.append(code)

    return matched


def build_domain_pack_context(
    *text_blobs: str,
    candidate_codes: list[str] | None = None,
) -> str:
    """Build bounded Phase 3 pack context for domain identification prompts.

    If ``candidate_codes`` is provided, those catalog codes are used (after
    alias resolution). Otherwise domains are detected from ``text_blobs``.

    Missing pack folders still contribute catalog metadata so the model retains
    the emission rule and domain vocabulary.
    """
    catalog = load_domain_catalog()
    if candidate_codes is not None:
        codes: list[str] = []
        seen: set[str] = set()
        for raw in candidate_codes:
            try:
                code = require_domain_code(raw)
            except DomainCatalogError:
                continue
            if code not in seen:
                seen.add(code)
                codes.append(code)
    else:
        codes = detect_phase3_domains(*text_blobs)

    if not codes:
        # Still expose catalog rule + version when nothing matched — helps AI
        # stay inside the catalog without inventing domains.
        return (
            "Phase 3 Solution Domain Knowledge Pack context\n"
            f"pack_version: {pack_version()}\n"
            f"emission_rule: {catalog.emission_rule}\n"
            "No domain packs matched the input text. Use only catalog domain codes."
        )

    chunks: list[str] = []
    total = 0
    for code in codes[:MAX_PACKS]:
        entry = catalog.get(code)
        if entry is None:
            continue
        block = _render_pack_block(entry)
        if total + len(block) > MAX_TOTAL_CHARS:
            break
        chunks.append(block)
        total += len(block)

    if not chunks:
        return (
            "Phase 3 Solution Domain Knowledge Pack context\n"
            f"pack_version: {pack_version()}\n"
            f"emission_rule: {catalog.emission_rule}\n"
            "No pack content available."
        )

    header = (
        "Phase 3 Solution Domain Knowledge Pack context "
        "(vendor-neutral; do not recommend products/SKUs)\n"
        f"pack_version: {pack_version()}\n"
        f"emission_rule: {catalog.emission_rule}\n"
    )
    return header + "\n\n" + "\n\n".join(chunks)


def _render_pack_block(entry: DomainCatalogEntry) -> str:
    folder = phase3_root() / "domains" / entry.pack_dir
    parts: list[str] = [
        f"### Domain pack: {entry.code} ({entry.name})",
        f"catalog_code: {entry.code}",
        f"typical_dependencies: {', '.join(entry.typical_dependencies) or '(none)'}",
    ]
    if entry.notes:
        parts.append(f"notes: {entry.notes}")

    if not folder.is_dir():
        parts.append(
            "pack_status: catalog_metadata_only "
            f"(missing directory {folder.name}/)",
        )
        return "\n".join(parts)

    loaded_any = False
    for filename in STUB_FILES:
        path = folder / filename
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not text:
            continue
        loaded_any = True
        parts.append(f"#### {filename}\n{text[:MAX_CHARS_PER_FILE]}")

    if not loaded_any:
        parts.append("pack_status: catalog_metadata_only (no stub markdown files)")
    return "\n".join(parts)


def _contains_needle(blob_norm: str, needle: str) -> bool:
    """Match whole words / phrases inside a space-padded normalized blob."""
    needle = needle.strip().lower()
    if not needle:
        return False
    # Space-padded exact phrase for multi-word; word-ish match for tokens.
    if " " in needle or "-" in needle or "/" in needle:
        return f" {needle} " in blob_norm or needle in blob_norm
    pattern = rf"(?<![a-z0-9_]){re.escape(needle)}(?![a-z0-9_])"
    return re.search(pattern, blob_norm) is not None


def list_phase3_pack_dirs() -> list[str]:
    """List domain pack directories that exist under knowledge/phase3/domains."""
    root = phase3_root() / "domains"
    if not root.is_dir():
        return []
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )

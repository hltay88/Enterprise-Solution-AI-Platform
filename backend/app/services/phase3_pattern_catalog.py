"""Phase 3 Architecture Pattern catalog loader (Sprint 3.2 Task 1).

Freezes pattern codes, aliases, related domain codes, and pack paths used by
later architecture generation. Does not call AI or mutate Stage F packs.

Auditability: persist ``catalog_version()`` (knowledge/phase3/VERSION) on
architecture options when generate lands (Task 6+).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.phase3_domain_catalog import (
    DomainCatalogError,
    catalog_version,
    list_domain_codes,
    phase3_root,
)


REQUIRED_DOC_PATTERN_CODES: frozenset[str] = frozenset(
    {
        "two_tier_campus",
        "three_tier_campus",
        "sdwan",
        "secure_internet_edge",
        "branch_connectivity",
        "wireless_enterprise",
        "data_centre_leaf_spine",
        "hci",
        "backup_dr",
        "hybrid_cloud",
        "zero_trust",
        "security_operations",
        "meeting_room",
        "control_room",
        "led_video_wall",
        "digital_signage",
        "smart_building",
    }
)


class PatternCatalogError(ValueError):
    """Raised when the Phase 3 pattern catalog is missing or invalid."""


@dataclass(frozen=True, slots=True)
class PatternCatalogEntry:
    code: str
    name: str
    aliases: tuple[str, ...]
    related_domain_codes: tuple[str, ...]
    pack_dir: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class PatternCatalog:
    catalog_version: str
    emission_rule: str
    patterns: tuple[PatternCatalogEntry, ...]

    def codes(self) -> frozenset[str]:
        return frozenset(item.code for item in self.patterns)

    def get(self, code: str) -> PatternCatalogEntry | None:
        needle = (code or "").strip().lower()
        for item in self.patterns:
            if item.code == needle:
                return item
        return None


def patterns_root() -> Path:
    return phase3_root() / "patterns"


def pattern_catalog_path() -> Path:
    return patterns_root() / "catalog.json"


def clear_pattern_catalog_cache() -> None:
    """Test helper — drop cached pattern catalog reads."""
    load_pattern_catalog.cache_clear()


@lru_cache(maxsize=1)
def load_pattern_catalog() -> PatternCatalog:
    """Load and validate ``knowledge/phase3/patterns/catalog.json``."""
    path = pattern_catalog_path()
    if not path.is_file():
        raise PatternCatalogError(f"Phase 3 pattern catalog missing: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PatternCatalogError(f"Phase 3 pattern catalog is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise PatternCatalogError("Phase 3 pattern catalog root must be an object")

    file_version = str(raw.get("catalog_version") or "").strip()
    if not file_version:
        raise PatternCatalogError("catalog_version is required")

    try:
        version_on_disk = catalog_version()
    except DomainCatalogError as exc:
        raise PatternCatalogError(str(exc)) from exc
    if file_version != version_on_disk:
        raise PatternCatalogError(
            f"catalog_version {file_version!r} does not match VERSION file "
            f"{version_on_disk!r}",
        )

    emission_rule = str(raw.get("emission_rule") or "").strip()
    if not emission_rule:
        raise PatternCatalogError("emission_rule is required")

    patterns_raw = raw.get("patterns")
    if not isinstance(patterns_raw, list) or not patterns_raw:
        raise PatternCatalogError("patterns must be a non-empty list")

    try:
        known_domains = set(list_domain_codes())
    except DomainCatalogError as exc:
        raise PatternCatalogError(
            f"Cannot validate related_domain_codes without domain catalog: {exc}",
        ) from exc

    entries: list[PatternCatalogEntry] = []
    seen_codes: set[str] = set()
    alias_to_code: dict[str, str] = {}

    for index, item in enumerate(patterns_raw):
        if not isinstance(item, dict):
            raise PatternCatalogError(f"patterns[{index}] must be an object")
        code = str(item.get("code") or "").strip().lower()
        name = str(item.get("name") or "").strip()
        pack_dir = str(item.get("pack_dir") or code).strip()
        if not code or not name:
            raise PatternCatalogError(f"patterns[{index}] requires code and name")
        if code in seen_codes:
            raise PatternCatalogError(f"Duplicate pattern code: {code}")
        seen_codes.add(code)

        aliases = _string_tuple(item.get("aliases"), field=f"patterns[{index}].aliases")
        related = _string_tuple(
            item.get("related_domain_codes"),
            field=f"patterns[{index}].related_domain_codes",
        )
        notes = str(item.get("notes") or "").strip()

        for domain_code in related:
            if domain_code not in known_domains:
                raise PatternCatalogError(
                    f"Pattern {code!r} lists unknown related_domain_code {domain_code!r}",
                )

        _register_alias(alias_to_code, code, code)
        for alias in aliases:
            _register_alias(alias_to_code, alias, code)

        entries.append(
            PatternCatalogEntry(
                code=code,
                name=name,
                aliases=aliases,
                related_domain_codes=related,
                pack_dir=pack_dir,
                notes=notes,
            ),
        )

    missing_required = REQUIRED_DOC_PATTERN_CODES - seen_codes
    if missing_required:
        raise PatternCatalogError(
            "Catalog missing patterns required by 05_ARCHITECTURE_PATTERNS.md: "
            f"{sorted(missing_required)}",
        )

    return PatternCatalog(
        catalog_version=file_version,
        emission_rule=emission_rule,
        patterns=tuple(entries),
    )


def resolve_pattern_code(value: str | None) -> str | None:
    """Resolve a code or alias to a catalog code, or None if unknown."""
    text = (value or "").strip().lower()
    if not text:
        return None
    catalog = load_pattern_catalog()
    if catalog.get(text) is not None:
        return text
    for item in catalog.patterns:
        if text in {alias.lower() for alias in item.aliases}:
            return item.code
        if text == item.name.lower():
            return item.code
    return None


def require_pattern_code(value: str | None) -> str:
    """Resolve a code/alias or raise ``PatternCatalogError``."""
    resolved = resolve_pattern_code(value)
    if resolved is None:
        raise PatternCatalogError(
            f"Unknown Phase 3 pattern code or alias: {value!r}. "
            "Only catalog codes/aliases are allowed.",
        )
    return resolved


def list_pattern_codes() -> list[str]:
    return sorted(load_pattern_catalog().codes())


def pattern_pack_dir(code: str) -> Path:
    """Return the stub pack directory for a catalog code (may not exist yet)."""
    entry = load_pattern_catalog().get(require_pattern_code(code))
    assert entry is not None
    return patterns_root() / entry.pack_dir


def patterns_for_domains(domain_codes: list[str] | None = None) -> list[PatternCatalogEntry]:
    """Return patterns whose related domains intersect the given domain codes.

    If ``domain_codes`` is empty/None, return all patterns.
    """
    catalog = load_pattern_catalog()
    if not domain_codes:
        return list(catalog.patterns)
    wanted = {str(code or "").strip().lower() for code in domain_codes if str(code or "").strip()}
    return [
        item
        for item in catalog.patterns
        if wanted.intersection(item.related_domain_codes)
    ]


MAX_PATTERN_PACKS = 5
MAX_PATTERN_CHARS_PER_FILE = 1200
MAX_PATTERN_TOTAL_CHARS = 5000
_PATTERN_STUB_FILES = ("overview.md",)


def build_pattern_pack_context(
    *text_blobs: str,
    domain_codes: list[str] | None = None,
    candidate_codes: list[str] | None = None,
) -> str:
    """Build bounded Phase 3 pattern pack context for architecture candidate prompts.

    Prefer ``candidate_codes``, else patterns related to ``domain_codes``, else
    keyword hits from ``text_blobs`` against catalog names/aliases. Always
    includes emission_rule + catalog version.
    """
    catalog = load_pattern_catalog()
    codes: list[str] = []
    seen: set[str] = set()

    if candidate_codes is not None:
        for raw in candidate_codes:
            try:
                code = require_pattern_code(raw)
            except PatternCatalogError:
                continue
            if code not in seen:
                seen.add(code)
                codes.append(code)
    elif domain_codes:
        for entry in patterns_for_domains(domain_codes):
            if entry.code not in seen:
                seen.add(entry.code)
                codes.append(entry.code)
    else:
        blob = " ".join(part for part in text_blobs if part).lower()
        for entry in catalog.patterns:
            needles = {
                entry.code,
                entry.code.replace("_", " "),
                entry.name.lower(),
                *[alias.lower() for alias in entry.aliases],
            }
            if any(needle and needle in blob for needle in needles):
                if entry.code not in seen:
                    seen.add(entry.code)
                    codes.append(entry.code)

    header = (
        "Phase 3 Architecture Pattern catalog context "
        "(vendor-neutral; recommendations only; no product SKUs)\n"
        f"catalog_version: {catalog.catalog_version}\n"
        f"emission_rule: {catalog.emission_rule}\n"
        f"known_pattern_codes: {', '.join(sorted(catalog.codes()))}\n"
    )
    if not codes:
        return header + "No pattern packs matched; use only catalog pattern codes."

    chunks: list[str] = []
    total = 0
    for code in codes[:MAX_PATTERN_PACKS]:
        entry = catalog.get(code)
        if entry is None:
            continue
        block = _render_pattern_pack_block(entry)
        if total + len(block) > MAX_PATTERN_TOTAL_CHARS:
            break
        chunks.append(block)
        total += len(block)

    if not chunks:
        return header + "No pack content available."
    return header + "\n" + "\n\n".join(chunks)


def _render_pattern_pack_block(entry: PatternCatalogEntry) -> str:
    folder = patterns_root() / entry.pack_dir
    parts: list[str] = [
        f"### Pattern pack: {entry.code} ({entry.name})",
        f"catalog_code: {entry.code}",
        f"related_domain_codes: {', '.join(entry.related_domain_codes) or '(none)'}",
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
    for filename in _PATTERN_STUB_FILES:
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
        parts.append(f"#### {filename}\n{text[:MAX_PATTERN_CHARS_PER_FILE]}")
    if not loaded_any:
        parts.append("pack_status: catalog_metadata_only (no stub markdown files)")
    return "\n".join(parts)


def _string_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise PatternCatalogError(f"{field} must be a list")
    out: list[str] = []
    for item in value:
        text = str(item or "").strip().lower()
        if text:
            out.append(text)
    return tuple(out)


def _register_alias(alias_to_code: dict[str, str], alias: str, code: str) -> None:
    key = alias.strip().lower()
    if not key:
        return
    existing = alias_to_code.get(key)
    if existing is not None and existing != code:
        raise PatternCatalogError(
            f"Alias {alias!r} maps to both {existing!r} and {code!r}",
        )
    alias_to_code[key] = code

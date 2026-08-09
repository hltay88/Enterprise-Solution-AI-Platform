"""Phase 3 Solution Domain catalog loader (Sprint 3.1 Task 1).

Freezes domain codes, aliases, dependency vocabulary, and pack paths used by
later domain-identification work. Does not call AI, touch the RKM, or mutate
Phase 1/2 knowledge checklist loaders.

Auditability: callers should persist ``catalog_version()`` on domain analyses
when those flows are implemented (Task 7+).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.domain_checklists import knowledge_root

REQUIRED_DOC_CODES: frozenset[str] = frozenset(
    {
        "campus_lan",
        "wan_sdwan",
        "internet",
        "wifi",
        "data_centre",
        "cloud",
        "compute",
        "storage",
        "backup_dr",
        "cybersecurity",
        "identity",
        "collaboration",
        "audio_visual",
        "led_video_wall",
        "digital_signage",
        "smart_building",
        "cctv",
        "iot",
        "monitoring_observability",
    }
)

ALLOWED_DEPENDENCY_KINDS: frozenset[str] = frozenset({"required", "recommended"})
ALLOWED_SELECTION_SOURCES: frozenset[str] = frozenset(
    {"requirement", "dependency", "optional_alternative"}
)


class DomainCatalogError(ValueError):
    """Raised when the Phase 3 domain catalog is missing or invalid."""


@dataclass(frozen=True, slots=True)
class DomainCatalogEntry:
    code: str
    name: str
    aliases: tuple[str, ...]
    phase2_checklist_ids: tuple[str, ...]
    typical_dependencies: tuple[str, ...]
    pack_dir: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class DomainCatalog:
    catalog_version: str
    emission_rule: str
    dependency_kinds: tuple[str, ...]
    selection_sources: tuple[str, ...]
    domains: tuple[DomainCatalogEntry, ...]

    def codes(self) -> frozenset[str]:
        return frozenset(d.code for d in self.domains)

    def get(self, code: str) -> DomainCatalogEntry | None:
        needle = (code or "").strip().lower()
        for domain in self.domains:
            if domain.code == needle:
                return domain
        return None


def phase3_root() -> Path:
    """Return ``knowledge/phase3`` under the knowledge root."""
    return knowledge_root() / "phase3"


def catalog_path() -> Path:
    return phase3_root() / "domains" / "catalog.json"


def version_file_path() -> Path:
    return phase3_root() / "VERSION"


def clear_catalog_cache() -> None:
    """Test helper — drop cached catalog/version reads."""
    load_domain_catalog.cache_clear()
    catalog_version.cache_clear()


@lru_cache(maxsize=1)
def catalog_version() -> str:
    """Return the frozen pack/catalog version string for audit metadata."""
    path = version_file_path()
    if not path.is_file():
        raise DomainCatalogError(f"Phase 3 VERSION file missing: {path}")
    version = path.read_text(encoding="utf-8").strip()
    if not version:
        raise DomainCatalogError(f"Phase 3 VERSION file is empty: {path}")
    return version


@lru_cache(maxsize=1)
def load_domain_catalog() -> DomainCatalog:
    """Load and validate ``knowledge/phase3/domains/catalog.json``."""
    path = catalog_path()
    if not path.is_file():
        raise DomainCatalogError(f"Phase 3 domain catalog missing: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DomainCatalogError(f"Phase 3 domain catalog is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise DomainCatalogError("Phase 3 domain catalog root must be an object")

    file_version = str(raw.get("catalog_version") or "").strip()
    if not file_version:
        raise DomainCatalogError("catalog_version is required")

    try:
        version_on_disk = catalog_version()
    except DomainCatalogError:
        raise
    if file_version != version_on_disk:
        raise DomainCatalogError(
            f"catalog_version {file_version!r} does not match VERSION file "
            f"{version_on_disk!r}",
        )

    emission_rule = str(raw.get("emission_rule") or "").strip()
    if not emission_rule:
        raise DomainCatalogError("emission_rule is required")

    dependency_kinds = _string_tuple(raw.get("dependency_kinds"), field="dependency_kinds")
    if not dependency_kinds:
        raise DomainCatalogError("dependency_kinds must be a non-empty list")
    unknown_kinds = set(dependency_kinds) - ALLOWED_DEPENDENCY_KINDS
    if unknown_kinds:
        raise DomainCatalogError(
            f"Unsupported dependency_kinds: {sorted(unknown_kinds)}",
        )

    selection_sources = _string_tuple(raw.get("selection_sources"), field="selection_sources")
    if not selection_sources:
        raise DomainCatalogError("selection_sources must be a non-empty list")
    unknown_sources = set(selection_sources) - ALLOWED_SELECTION_SOURCES
    if unknown_sources:
        raise DomainCatalogError(
            f"Unsupported selection_sources: {sorted(unknown_sources)}",
        )

    domains_raw = raw.get("domains")
    if not isinstance(domains_raw, list) or not domains_raw:
        raise DomainCatalogError("domains must be a non-empty list")

    entries: list[DomainCatalogEntry] = []
    seen_codes: set[str] = set()
    alias_to_code: dict[str, str] = {}

    for index, item in enumerate(domains_raw):
        if not isinstance(item, dict):
            raise DomainCatalogError(f"domains[{index}] must be an object")
        code = str(item.get("code") or "").strip().lower()
        name = str(item.get("name") or "").strip()
        pack_dir = str(item.get("pack_dir") or code).strip()
        if not code or not name:
            raise DomainCatalogError(f"domains[{index}] requires code and name")
        if code in seen_codes:
            raise DomainCatalogError(f"Duplicate domain code: {code}")
        seen_codes.add(code)

        aliases = _string_tuple(item.get("aliases"), field=f"domains[{index}].aliases")
        phase2_ids = _string_tuple(
            item.get("phase2_checklist_ids"),
            field=f"domains[{index}].phase2_checklist_ids",
        )
        typical_deps = _string_tuple(
            item.get("typical_dependencies"),
            field=f"domains[{index}].typical_dependencies",
        )
        notes = str(item.get("notes") or "").strip()

        # Code resolves to itself.
        _register_alias(alias_to_code, code, code)
        for alias in aliases:
            _register_alias(alias_to_code, alias, code)

        entries.append(
            DomainCatalogEntry(
                code=code,
                name=name,
                aliases=aliases,
                phase2_checklist_ids=phase2_ids,
                typical_dependencies=typical_deps,
                pack_dir=pack_dir,
                notes=notes,
            ),
        )

    missing_required = REQUIRED_DOC_CODES - seen_codes
    if missing_required:
        raise DomainCatalogError(
            "Catalog missing domains required by 02_SOLUTION_DOMAIN_MODEL.md: "
            f"{sorted(missing_required)}",
        )

    for entry in entries:
        for dep in entry.typical_dependencies:
            if dep not in seen_codes:
                raise DomainCatalogError(
                    f"Domain {entry.code!r} lists unknown typical_dependency {dep!r}",
                )

    return DomainCatalog(
        catalog_version=file_version,
        emission_rule=emission_rule,
        dependency_kinds=dependency_kinds,
        selection_sources=selection_sources,
        domains=tuple(entries),
    )


def resolve_domain_code(value: str | None) -> str | None:
    """Resolve a code or alias to a catalog code, or None if unknown."""
    text = (value or "").strip().lower()
    if not text:
        return None
    catalog = load_domain_catalog()
    if catalog.get(text) is not None:
        return text
    for domain in catalog.domains:
        if text in {alias.lower() for alias in domain.aliases}:
            return domain.code
        if text == domain.name.lower():
            return domain.code
    return None


def require_domain_code(value: str | None) -> str:
    """Resolve a code/alias or raise ``DomainCatalogError``."""
    resolved = resolve_domain_code(value)
    if resolved is None:
        raise DomainCatalogError(
            f"Unknown Phase 3 domain code or alias: {value!r}. "
            "Only catalog codes/aliases are allowed.",
        )
    return resolved


def list_domain_codes() -> list[str]:
    return sorted(load_domain_catalog().codes())


def domain_pack_dir(code: str) -> Path:
    """Return the stub pack directory for a catalog code (may not exist yet)."""
    entry = load_domain_catalog().get(require_domain_code(code))
    assert entry is not None
    return phase3_root() / "domains" / entry.pack_dir


def _string_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise DomainCatalogError(f"{field} must be a list")
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
        raise DomainCatalogError(
            f"Alias {alias!r} maps to both {existing!r} and {code!r}",
        )
    alias_to_code[key] = code

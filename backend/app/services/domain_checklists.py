"""Detect solution domains and load Presales clarification checklists."""

from __future__ import annotations

import os
import re
from pathlib import Path

# domain_id -> (display name, checklist filename, keyword triggers)
DOMAIN_PACKS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "wireless": (
        "Wireless / WLAN",
        "wireless.md",
        (
            "wireless",
            "wi-fi",
            "wifi",
            "wlan",
            "access point",
            "access points",
            " ap ",
            "aps",
            "ssid",
            "heatmap",
            "heat map",
            "rf survey",
            "radio survey",
            "floor plan",
            "floorplan",
            "coverage area",
            "wifi 6",
            "wifi6",
            "802.11",
            "controller-based",
            "aruba",
            "meraki",
            "cisco wireless",
            "ruckus",
        ),
    ),
    "networking": (
        "Campus / LAN Networking",
        "networking.md",
        (
            "switching",
            "switch",
            "campus lan",
            "routing",
            "core switch",
            "access switch",
            "distribution switch",
            "vlan",
            "poe",
            "spine",
            "leaf",
        ),
    ),
}


def knowledge_root() -> Path:
    env = os.getenv("KNOWLEDGE_PATH", "").strip()
    if env:
        return Path(env)

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "knowledge",  # backend/knowledge (if colocated)
        here.parents[3] / "knowledge",  # repo/knowledge when running from backend/app
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[-1]


def detect_domains(*text_parts: str) -> list[str]:
    blob = " ".join(part for part in text_parts if part).lower()
    # Normalize separators so keyword " ap " still matches line starts.
    blob = f" {re.sub(r'\s+', ' ', blob)} "

    matched: list[str] = []
    for domain_id, (_label, _file, keywords) in DOMAIN_PACKS.items():
        if any(keyword in blob for keyword in keywords):
            matched.append(domain_id)
    return matched


def load_checklist(domain_id: str) -> str | None:
    pack = DOMAIN_PACKS.get(domain_id)
    if pack is None:
        return None
    _label, filename, _keywords = pack
    path = knowledge_root() / "checklists" / filename
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def build_checklist_context(domains: list[str]) -> str:
    sections: list[str] = []
    for domain_id in domains:
        content = load_checklist(domain_id)
        if not content:
            continue
        label = DOMAIN_PACKS[domain_id][0]
        sections.append(f"### Mandatory checklist pack: {label}\n{content}")
    return "\n\n".join(sections).strip()

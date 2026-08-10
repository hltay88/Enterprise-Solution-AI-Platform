"""Sprint 5.1 — Extensible solution-domain taxonomy seed.

Codes are stable identifiers; display names match Phase 5 taxonomy.
Aliases help map Phase 3 catalog / Phase 2 checklist ids during classification.
"""

from __future__ import annotations

# (code, display_name, aliases...)
TAXONOMY_SEED: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("networking", "Networking", ("campus_lan", "wan_sdwan", "internet", "network")),
    ("wireless", "Wireless", ("wifi", "wlan", "wi-fi")),
    ("cybersecurity", "Cybersecurity", ("security", "network_security", "identity")),
    ("cloud", "Cloud", ()),
    ("data_centre", "Data Centre", ("data_center", "dc", "datacentre")),
    ("compute", "Compute", ("virtualization",)),
    ("storage", "Storage", ()),
    ("backup", "Backup", ("backup_dr", "dr")),
    ("hci", "HCI", ("hyperconverged",)),
    ("av", "AV", ("audio_visual", "collaboration", "meeting_rooms")),
    ("led_videowall", "LED Videowall", ("led", "led_video_wall", "av_led")),
    ("digital_signage", "Digital Signage", ()),
    ("billboard", "Billboard", ()),
    ("smart_building", "Smart Building", ("iot_smart_building",)),
    ("iot", "IoT", ("cctv", "monitoring_observability")),
)

TAXONOMY_CODES: frozenset[str] = frozenset(code for code, _, _ in TAXONOMY_SEED)

DEFAULT_DOMAIN_CODE = "networking"


def taxonomy_choices() -> list[dict[str, object]]:
    return [
        {"code": code, "name": name, "aliases": list(aliases)}
        for code, name, aliases in TAXONOMY_SEED
    ]


def resolve_domain_code(value: str | None) -> str | None:
    """Map a free-text / alias token to a taxonomy code, or None."""
    if not value:
        return None
    needle = value.strip().lower().replace(" ", "_").replace("-", "_")
    if needle in TAXONOMY_CODES:
        return needle
    for code, name, aliases in TAXONOMY_SEED:
        if needle == name.lower().replace(" ", "_"):
            return code
        if needle in aliases:
            return code
    return None

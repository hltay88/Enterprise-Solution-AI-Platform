"""Detect solution domains and load Presales clarification checklists."""

from __future__ import annotations

import os
import re
from pathlib import Path

# Max checklist packs injected into one clarification prompt (token control).
MAX_CHECKLIST_PACKS = 4

# domain_id -> (display name, checklist filename, keyword triggers)
# More specific domains should appear earlier in DOMAIN_PRIORITY.
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
            " ssid",
            "heatmap",
            "heat map",
            "rf survey",
            "radio survey",
            "wifi 6",
            "wifi6",
            "wi-fi 6",
            "802.11",
            "aruba wireless",
            "cisco wireless",
            "meraki mr",
            "ruckus",
        ),
    ),
    "network_security": (
        "Network Security",
        "network_security.md",
        (
            "network security",
            "next-gen firewall",
            "next generation firewall",
            "ngfw",
            "firewall",
            "ids/ips",
            "intrusion prevention",
            "intrusion detection",
            "network access control",
            " nac ",
            "ztna",
            "zero trust network",
            "sase",
            "secure web gateway",
            "vpn concentrator",
            "remote access vpn",
            "microsegmentation",
            "palo alto",
            "fortigate",
            "fortinet",
            "cisco ftd",
            "checkpoint firewall",
        ),
    ),
    "cybersecurity": (
        "Cybersecurity",
        "cybersecurity.md",
        (
            "cybersecurity",
            "cyber security",
            "endpoint security",
            "endpoint detection",
            "edr",
            "xdr",
            "mdr",
            "siem",
            "soc ",
            "security operations",
            "zero trust",
            "privileged access",
            " pam ",
            "identity security",
            "entra id",
            "azure ad",
            "conditional access",
            "defender for endpoint",
            "crowdstrike",
            "sentinelone",
            "ransomware",
        ),
    ),
    "hci": (
        "HCI / Hyperconverged",
        "hci.md",
        (
            "hyperconverged",
            "hyper-converged",
            " hci ",
            "hci cluster",
            "vsan",
            "v-san",
            "nutanix",
            "azure stack hci",
            "vxrail",
            "simplivity",
        ),
    ),
    "storage": (
        "Storage",
        "storage.md",
        (
            "storage array",
            "all-flash",
            "all flash",
            " san ",
            " nas ",
            "nvme-of",
            "object storage",
            "block storage",
            "file storage",
            "storage refresh",
            "storage consolidation",
            "netapp",
            "pure storage",
            "dell powerstore",
            "hitachi storage",
            "hpe alletra",
        ),
    ),
    "data_centre": (
        "Data Centre",
        "data_centre.md",
        (
            "data centre",
            "data center",
            "datacentre",
            "datacenter",
            "dc build",
            "dc refresh",
            "colo ",
            "colocation",
            "white space",
            "raised floor",
            "meet-me room",
            "dcim",
        ),
    ),
    "servers": (
        "Servers / Compute",
        "servers.md",
        (
            "rack server",
            "blade server",
            "server refresh",
            "server consolidation",
            "compute refresh",
            "bare metal",
            "bare-metal",
            "poweredge",
            "proliant",
            "thinksystem",
            "ucs blade",
            "ilo ",
            "idrac",
        ),
    ),
    "led": (
        "LED Video Wall",
        "led.md",
        (
            "led wall",
            "led video",
            "led display",
            "video wall",
            "fine pitch",
            "fine-pitch",
            "pixel pitch",
            "novastar",
            "brompton",
            "led canvas",
        ),
    ),
    "av": (
        "Audio Visual (AV)",
        "av.md",
        (
            "audio visual",
            "audio-visual",
            "audiovisual",
            " av system",
            "av systems",
            "meeting room av",
            "boardroom av",
            "conference room av",
            "lecture capture",
            "dsp audio",
            "crestron",
            "extron",
            "q-sys",
            "qsys",
            "biamp",
            "teams room",
            "zoom room",
        ),
    ),
    "digital_signage": (
        "Digital Signage",
        "digital_signage.md",
        (
            "digital signage",
            "wayfinding",
            "menu board",
            "signage cms",
            "proof of play",
            "digital display network",
        ),
    ),
    "networking": (
        "Campus / LAN Networking",
        "networking.md",
        (
            "campus network",
            "campus lan",
            "lan refresh",
            "network refresh",
            "core switch",
            "access switch",
            "distribution switch",
            "spine-leaf",
            "spine leaf",
            "switching fabric",
            "routing and switching",
            "sd-wan",
            "sdwan",
            "campus switching",
        ),
    ),
    "backup": (
        "Backup & Recovery",
        "backup.md",
        (
            "backup",
            "disaster recovery",
            "immutable backup",
            "veeam",
            "commvault",
            "rubrik",
            "cohesity",
            "recovery point objective",
            " rpo ",
            " rto ",
        ),
    ),
    "virtualization": (
        "Virtualization",
        "virtualization.md",
        (
            "virtualization",
            "hypervisor",
            "vmware",
            "vsphere",
            "hyper-v",
            "proxmox",
            " vdi ",
            "citrix virtual",
            "horizon vdi",
        ),
    ),
    "cloud": (
        "Cloud",
        "cloud.md",
        (
            "public cloud",
            "private cloud",
            "hybrid cloud",
            "multi-cloud",
            "multicloud",
            "landing zone",
            "aws ",
            "azure ",
            "gcp ",
            "google cloud",
            "expressroute",
            "direct connect",
        ),
    ),
    "collaboration": (
        "Collaboration / UC",
        "collaboration.md",
        (
            "unified communications",
            "microsoft teams",
            "m365",
            "microsoft 365",
            "office 365",
            "telephony",
            "contact centre",
            "contact center",
            "direct routing",
            "pbx ",
            "collaboration suite",
        ),
    ),
    "microsoft": (
        "Microsoft Platform",
        "microsoft.md",
        (
            "microsoft platform",
            "entra id",
            "intune",
            "defender for",
            "azure landing",
            "windows 365",
            "power platform",
            "microsoft licensing",
        ),
    ),
    "cctv": (
        "CCTV / Surveillance",
        "cctv.md",
        (
            "cctv",
            "video surveillance",
            "ip camera",
            "security camera",
            "vms ",
            "video management",
            "anpr",
            "milestone xprotect",
            "genetec",
            "hikvision",
            "axis camera",
        ),
    ),
    "access_control": (
        "Access Control",
        "access_control.md",
        (
            "access control",
            "door access",
            "turnstile",
            "visitor management",
            "card access",
            "physical identity",
            "hid reader",
            "lenel",
            "s2 security",
        ),
    ),
    "structured_cabling": (
        "Structured Cabling",
        "structured_cabling.md",
        (
            "structured cabling",
            "fibre backbone",
            "fiber backbone",
            "cat6",
            "cat6a",
            "om3",
            "om4",
            "cable containment",
            "idf ",
            "mdf ",
            "patch panel",
        ),
    ),
    "ups": (
        "UPS / Power Protection",
        "ups.md",
        (
            " ups ",
            "uninterruptible power",
            "battery runtime",
            "modular ups",
            "pdu ",
            "power protection",
            "apc ups",
            "eaton ups",
            "vertiv ups",
        ),
    ),
    "iot_smart_building": (
        "IoT / Smart Building",
        "iot_smart_building.md",
        (
            "smart building",
            "building management",
            " bms ",
            "iot sensor",
            "iot platform",
            "energy monitoring",
            "space utilization",
            "occupancy sensor",
            "ot network",
        ),
    ),
}

# Prefer specific packs when many domains match.
DOMAIN_PRIORITY: tuple[str, ...] = (
    "wireless",
    "network_security",
    "cybersecurity",
    "hci",
    "storage",
    "data_centre",
    "servers",
    "led",
    "av",
    "digital_signage",
    "cctv",
    "access_control",
    "networking",
    "backup",
    "virtualization",
    "cloud",
    "microsoft",
    "collaboration",
    "structured_cabling",
    "ups",
    "iot_smart_building",
)


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
    blob = f" {re.sub(r'\s+', ' ', blob)} "

    matched: list[str] = []
    for domain_id in DOMAIN_PRIORITY:
        pack = DOMAIN_PACKS.get(domain_id)
        if pack is None:
            continue
        _label, _file, keywords = pack
        if any(keyword in blob for keyword in keywords):
            matched.append(domain_id)
    return matched


def select_domains_for_prompt(domains: list[str], *, limit: int = MAX_CHECKLIST_PACKS) -> list[str]:
    """Keep detection order (already priority-sorted) and cap pack injection."""
    if limit <= 0:
        return []
    return list(domains[:limit])


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
    selected = select_domains_for_prompt(domains)
    sections: list[str] = []
    for domain_id in selected:
        content = load_checklist(domain_id)
        if not content:
            continue
        label = DOMAIN_PACKS[domain_id][0]
        sections.append(f"### Mandatory checklist pack: {label}\n{content}")

    omitted = [d for d in domains if d not in selected]
    if omitted:
        labels = ", ".join(DOMAIN_PACKS[d][0] for d in omitted if d in DOMAIN_PACKS)
        sections.append(
            "### Additional detected domains (no full checklist injected — still probe lightly)\n"
            + labels
        )
    return "\n\n".join(sections).strip()

"""Stage F vendor-neutral Knowledge Pack stub loader.

Loads short markdown stubs from knowledge/<domain>/ when present and injects
them into AI context. This is not RAG — packs enrich prompts only.
"""

from __future__ import annotations

from pathlib import Path

from app.services.domain_checklists import detect_domains, knowledge_root

# Map domain_checklist ids → knowledge/ folder names (ATLAS pack tree).
DOMAIN_TO_PACK_DIR: dict[str, str] = {
    "wireless": "wireless",
    "networking": "networking",
    "network_security": "security",
    "cybersecurity": "security",
    "cloud": "cloud",
    "storage": "storage",
    "virtualization": "virtualization",
    "microsoft": "microsoft",
    "backup": "backup",
    "av": "av_led",
    "led": "av_led",
    "digital_signage": "digital_signage",
    "iot_smart_building": "smart_building",
    "cctv": "cctv",
    "collaboration": "meeting_rooms",
}

STUB_FILES = ("overview.md", "mandatory_questions.md", "best_practices.md")
MAX_PACKS = 3
MAX_CHARS_PER_FILE = 1200
MAX_TOTAL_CHARS = 4000


def build_knowledge_pack_context(*text_blobs: str) -> str:
    """Detect domains from text and return concatenated pack stubs."""
    domains = detect_domains(*text_blobs)
    if not domains:
        return ""

    root = knowledge_root()
    chunks: list[str] = []
    total = 0
    seen_dirs: set[str] = set()

    for domain in domains:
        pack_dir = DOMAIN_TO_PACK_DIR.get(domain)
        if not pack_dir or pack_dir in seen_dirs:
            continue
        seen_dirs.add(pack_dir)
        folder = root / pack_dir
        if not folder.is_dir():
            continue

        pack_parts: list[str] = [f"### Knowledge Pack: {pack_dir}"]
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
            excerpt = text[:MAX_CHARS_PER_FILE]
            pack_parts.append(f"#### {filename}\n{excerpt}")

        if len(pack_parts) == 1:
            continue
        block = "\n\n".join(pack_parts)
        if total + len(block) > MAX_TOTAL_CHARS:
            break
        chunks.append(block)
        total += len(block)
        if len(chunks) >= MAX_PACKS:
            break

    if not chunks:
        return ""
    return (
        "Vendor-neutral Knowledge Pack guidance (do not recommend vendors/products):\n\n"
        + "\n\n".join(chunks)
    )


def list_available_pack_dirs() -> list[str]:
    root = knowledge_root()
    if not root.is_dir():
        return []
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "checklists"
    )

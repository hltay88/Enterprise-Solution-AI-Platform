"""Text normalization for extracted document content."""

from __future__ import annotations

import re
import unicodedata


_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """Normalize unicode, strip control chars, and collapse excess whitespace."""
    if not text:
        return ""
    value = unicodedata.normalize("NFKC", text)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = _CONTROL_RE.sub("", value)
    value = "\n".join(_MULTI_SPACE_RE.sub(" ", line).rstrip() for line in value.split("\n"))
    value = _MULTI_NL_RE.sub("\n\n", value)
    return value.strip()


def detect_language_hint(text: str) -> str:
    """Lightweight language hint without external deps."""
    sample = (text or "")[:2000]
    if not sample:
        return "und"
    letters = [ch for ch in sample if ch.isalpha()]
    if not letters:
        return "und"
    ascii_letters = sum(1 for ch in letters if ord(ch) < 128)
    ratio = ascii_letters / len(letters)
    return "en" if ratio >= 0.85 else "und"


def word_count(text: str) -> int:
    if not text or not text.strip():
        return 0
    return len(re.findall(r"\S+", text))

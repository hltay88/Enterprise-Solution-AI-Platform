"""OCR helpers for images and scanned PDFs (ATLAS-029 extract path)."""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)

OCR_ENGINE_NAME = "tesseract"
MANUAL_REVIEW_CONFIDENCE = 80.0


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def ocr_image(path: Path) -> tuple[str, float | None, int]:
    """OCR a single image file. Returns (text, confidence_or_none, processing_ms)."""
    started = time.perf_counter()
    if not tesseract_available():
        raise RuntimeError(
            "OCR requires tesseract-ocr on the host (not installed in this environment)",
        )

    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("OCR Python packages (pytesseract/Pillow) are not installed") from exc

    with Image.open(path) as image:
        text = pytesseract.image_to_string(image) or ""
        confidence: float | None = None
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confs = [float(c) for c in data.get("conf", []) if str(c) not in {"-1", ""}]
            if confs:
                confidence = sum(confs) / len(confs)
        except Exception:
            logger.debug("Could not compute OCR confidence for %s", path.name, exc_info=True)

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return text, confidence, elapsed_ms


def ocr_pdf_pages(path: Path, *, dpi: int = 200) -> list[tuple[int, str, float | None, int]]:
    """Rasterize PDF pages and OCR each. Returns list of (page_number, text, conf, ms)."""
    if not tesseract_available():
        raise RuntimeError(
            "OCR requires tesseract-ocr on the host (not installed in this environment)",
        )
    if shutil.which("pdftoppm") is None:
        raise RuntimeError(
            "Scanned PDF OCR requires poppler-utils (pdftoppm) on the host",
        )

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("OCR Python packages (pdf2image/pytesseract) are not installed") from exc

    images = convert_from_path(str(path), dpi=dpi)
    results: list[tuple[int, str, float | None, int]] = []
    for index, image in enumerate(images, start=1):
        started = time.perf_counter()
        text = pytesseract.image_to_string(image) or ""
        confidence: float | None = None
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confs = [float(c) for c in data.get("conf", []) if str(c) not in {"-1", ""}]
            if confs:
                confidence = sum(confs) / len(confs)
        except Exception:
            logger.debug("Could not compute OCR confidence for PDF page %s", index, exc_info=True)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        results.append((index, text, confidence, elapsed_ms))
    return results

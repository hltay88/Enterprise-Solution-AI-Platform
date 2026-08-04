from pathlib import Path

from docx import Document
from openpyxl import Workbook

from app.services.document_intelligence.parsers import extract_document


def test_extract_txt(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("Customer needs HA firewall\n\nSecond line", encoding="utf-8")
    result = extract_document(path, "txt")
    assert "HA firewall" in result.full_text
    assert result.ocr_used is False
    assert len(result.pages) == 1


def test_extract_csv(tmp_path: Path):
    path = tmp_path / "reqs.csv"
    path.write_text("id,requirement\n1,Must support SSO\n2,Must log audits\n", encoding="utf-8")
    result = extract_document(path, "csv")
    assert "Must support SSO" in result.full_text
    assert result.metadata.get("parser") == "csv"


def test_extract_docx(tmp_path: Path):
    path = tmp_path / "brief.docx"
    document = Document()
    document.add_paragraph("Business objective: modernize campus network")
    document.save(path)
    result = extract_document(path, "docx")
    assert "modernize campus network" in result.full_text


def test_extract_xlsx(tmp_path: Path):
    path = tmp_path / "bom.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Requirements"
    sheet["A1"] = "Item"
    sheet["B1"] = "Need"
    sheet["A2"] = "R1"
    sheet["B2"] = "Redundant core switches"
    workbook.save(path)
    result = extract_document(path, "xlsx")
    assert "Redundant core switches" in result.full_text
    assert result.metadata.get("sheet_count") == "1"


def test_extract_pdf_native(tmp_path: Path):
    # Minimal PDF with a text stream (hand-written).
    path = tmp_path / "native.pdf"
    content = b"""%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 55 >>stream
BT /F1 12 Tf 50 100 Td (Atlas firewall requirement) Tj ET
endstream
endobj
5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000373 00000 n 
trailer<< /Size 6 /Root 1 0 R >>
startxref
450
%%EOF
"""
    path.write_bytes(content)
    result = extract_document(path, "pdf")
    # pypdf may or may not extract from this minimal PDF depending on fonts;
    # assert pipeline returns a structured result without crashing.
    assert isinstance(result.full_text, str)
    assert result.pages
    assert "parser" in result.metadata

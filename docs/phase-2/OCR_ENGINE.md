# OCR_ENGINE.md

**Module:** OCR & Document Intelligence Engine  
**Version:** 1.0

---

## Purpose

Convert every uploaded customer document into machine-readable text.

OCR is responsible only for text extraction.

It does NOT perform AI analysis.

---

## Supported Input

- PDF
- DOCX
- DOC
- XLSX
- CSV
- TXT
- PNG
- JPG
- JPEG
- TIFF
- Visio Export
- PowerPoint
- ZIP

---

## Processing Pipeline

```text
Upload
  ↓
Virus Scan
  ↓
File Validation
  ↓
Determine File Type
  ↓
Native Parser
  ↓
OCR (if required)
  ↓
Text Normalization
  ↓
Language Detection
  ↓
Metadata Extraction
  ↓
Store Raw Text
  ↓
Send to Requirement Intelligence Engine
```

---

## OCR Rules

- If PDF already contains text → Do NOT OCR.
- If PDF is scanned → OCR.
- If Image → OCR.
- If Handwritten → Attempt OCR.
- If Confidence < 80% → Flag for Manual Review.

---

## Metadata

Every extracted page stores:

- Document ID
- Page Number
- Language
- Confidence
- Character Count
- Word Count
- Processing Time
- OCR Engine
- Timestamp

---

## Future Support

- Table Extraction
- Diagram Recognition
- Network Topology Recognition
- Rack Layout Recognition
- Architecture Diagram Recognition
- Visio Object Recognition
- Floor Plan Recognition

# FILE_PROCESSING.md

Module: Document Processing Engine  
Related: **ATLAS-027**, **ATLAS-029**, `OCR_ENGINE.md`

---

## Purpose

Manage uploaded customer documents throughout their lifecycle.

---

## Workflow

```
Upload → Validation → Virus Scan → Checksum → Duplicate Detection
→ Metadata Extraction → Storage → Text Extraction / OCR → Requirement Intelligence Engine
```

Heavy steps after validation run as **async jobs** (ATLAS-029).

---

## File Validation (Phase 2.1 — locked)

| Rule | Value |
|------|-------|
| Maximum size per file | **50 MB** |
| Maximum aggregate per batch | **200 MB** |
| Allowed types | PDF, DOCX, DOC, XLSX, CSV, TXT, PNG, JPG, JPEG |

Deferred after 2.1: ZIP, PPTX, TIFF, Visio exports, and other OCR_ENGINE “future” formats.

---

## Storage Layers

```
Original File → Extracted Text → Metadata → Evidence Repository → Requirement Knowledge Model
```

---

## Duplicate Detection

- SHA-256 hash (primary)
- Filename + size (secondary signals)
- Upload timestamp retained for audit

---

## Evidence Repository

Every requirement references evidence (ATLAS-021). Evidence may include:

- Document / page / excerpt
- Sales intake field reference
- Workshop note
- Clarification answer

---

## Retention Policy

- Original files remain unchanged after ingest.
- Evidence records are immutable once referenced by a Published RKM version.
- Prefer archive over hard-delete for Published evidence chains.

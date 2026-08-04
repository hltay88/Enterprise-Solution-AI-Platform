# FILE_PROCESSING.md
Module: Document Processing Engine

---

## Purpose
Manage uploaded customer documents throughout their lifecycle.

---

## Workflow

```
Upload → Validation → Virus Scan → Checksum → Duplicate Detection
→ Metadata Extraction → Storage → Text Extraction → Requirement Intelligence Engine
```

---

## File Validation

- **Maximum Size:** 500MB
- **Allowed Types:** PDF, DOCX, DOC, PPTX, XLSX, CSV, TXT, PNG, JPG, ZIP

---

## Storage Layers

```
Original File → Extracted Text → Metadata → Evidence Repository → Requirement Knowledge Model
```

---

## Duplicate Detection
- SHA256 Hash
- Filename
- File Size
- Similarity
- Upload Timestamp

---

## Evidence Repository

Every requirement references evidence. Evidence includes:
- Document, Page, Paragraph, Sentence, Image, Table, Drawing, Diagram

---

## Retention Policy
- Original files remain unchanged.
- Evidence is immutable.
- Requirement versions reference evidence.
- Nothing is deleted automatically — Archive only.

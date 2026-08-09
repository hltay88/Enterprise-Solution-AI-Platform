# Export and Rendering Standard

Rendering must be deterministic for the same document version, template version, source snapshot and rendering configuration.

Outputs:
- DOCX
- PDF (LibreOffice `soffice --headless`; Docker backend image includes `libreoffice-writer`)
- PPTX
- XLSX

Native/Mac without Docker: install LibreOffice or set `LIBREOFFICE_PATH`. Missing soffice fails the PDF export job visibly (ATLAS-049) — no silent fallback.

After rendering:
1. Verify file exists.
2. Verify page/slide count.
3. Verify required sections.
4. Check unresolved placeholders.
5. Verify tables and diagrams.
6. Store checksum and artifact metadata.

Failed exports must remain visible as failed jobs.

# Export and Rendering Standard

Rendering must be deterministic for the same document version, template version, source snapshot and rendering configuration.

Outputs:
- DOCX
- PDF
- PPTX
- XLSX

After rendering:
1. Verify file exists.
2. Verify page/slide count.
3. Verify required sections.
4. Check unresolved placeholders.
5. Verify tables and diagrams.
6. Store checksum and artifact metadata.

Failed exports must remain visible as failed jobs.

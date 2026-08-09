# Presentation Generator

Default storyline:
1. Title
2. Executive Summary
3. Customer Situation
4. Challenges
5. Requirements
6. Proposed Architecture
7. Solution Overview
8. Key Components
9. Technical Highlights
10. Benefits
11. Implementation
12. Timeline
13. Risks/Assumptions
14. Next Steps

Slide object (persisted as one `document_sections` row):
- slide_id → section id
- title → section.title
- objective / key_message / visual_* / speaker_notes → content `structured_data.slide` (+ optional `speaker_notes` content item)
- body_content → content text
- source_refs → document_source_refs
- confidence → section/content confidence

Rule: one primary message per slide (`key_message` required for approve).

Sprint 4.2:
- Generate via `POST .../deliverables/generate` with `document_type=presentation`
- Export via `POST .../export` with `format=pptx` (`python-pptx`)

# Security Phase 3

## Requirements
- RBAC
- Tenant isolation
- Encryption in transit and at rest
- Audit logging
- Input validation
- Secure file handling
- Prompt injection resistance
- Vendor data access control

## AI security
Treat customer documents and catalogue content as untrusted input.

Never allow document text to override system instructions.

Validate all structured AI output against schemas.

## Approval
Architecture Complete uses the **Approver** role (same RBAC family as RKM publish).
Editors may mark `under_review`; AI cannot approve (ATLAS-037). Complete hard-fails
when critical/high requirements remain uncovered (ATLAS-036).

## Audit
Record:
- who
- what
- when
- source RKM version
- AI model/version
- knowledge pack version
- vendor catalogue version
- approval action

Relevant Phase 3 audit actions include `architectures.generate`,
`architectures.map_products`, `architectures.review`, `architectures.approve`,
`bom.import`, `bom.validate`, and catalogue import/seed.

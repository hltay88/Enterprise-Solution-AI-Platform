# Source Snapshot Standard

Every generation run creates an immutable source snapshot containing:
- RKM version
- Architecture version
- Vendor catalogue version
- BOM version
- Knowledge Pack versions
- Prompt version
- Model/provider identifier
- generation configuration
- timestamp

A document version references exactly one source snapshot.

Never silently mix source versions.

# Architecture Patterns

## Purpose
Provide reusable, vendor-neutral architecture patterns.

## Stable codes (Sprint 3.2 Task 1 freeze)

Frozen in `knowledge/phase3/patterns/catalog.json` (pack version `knowledge/phase3/VERSION`).
AI and services may **only** emit these codes (or aliases that resolve to them).

| Code | Name |
|------|------|
| `two_tier_campus` | Two-tier campus |
| `three_tier_campus` | Three-tier campus |
| `sdwan` | SD-WAN |
| `secure_internet_edge` | Secure Internet Edge |
| `branch_connectivity` | Branch connectivity |
| `wireless_enterprise` | Wireless enterprise |
| `data_centre_leaf_spine` | Data Centre leaf-spine |
| `hci` | HCI |
| `backup_dr` | Backup and DR |
| `hybrid_cloud` | Hybrid cloud |
| `zero_trust` | Zero Trust |
| `security_operations` | Security operations |
| `meeting_room` | Meeting room |
| `control_room` | Control room |
| `led_video_wall` | LED video wall |
| `digital_signage` | Digital signage |
| `smart_building` | Smart building |

Loader: `backend/app/services/phase3_pattern_catalog.py`.

Priority stubs (overview.md) exist for campus, SD-WAN, internet edge, wireless,
leaf-spine, hybrid cloud, zero trust, and backup/DR.

## Pattern requirements
Each pattern contains:
- problem
- applicability
- prerequisites
- logical components
- optional components
- design considerations
- failure modes
- security considerations
- scalability considerations
- implementation notes

Patterns are recommendations, not mandatory designs.

## Rules
- Vendor-neutral — no product SKUs in pattern packs (ATLAS-035).
- Related domain codes in the catalog must resolve via the Phase 3 domain catalog.
- Do not invent pattern codes outside this freeze.

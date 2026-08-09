# Vendor Neutral Recommendation Standard

## Purpose
Prevent premature vendor bias.

## Sequence
1. Understand requirement.
2. Define capability.
3. Define architecture.
4. Define technical specifications.
5. Map capabilities to vendors.
6. Compare products.
7. Select preferred option.

## Vendor data
Vendor information may include:
- Cisco
- Aruba / HPE
- Dell
- Huawei
- Sangfor
- Other approved vendors

## Rules
A vendor is not recommended solely because it appears in the customer request.

The system must distinguish:
- customer preference
- mandatory vendor requirement
- technical suitability
- commercial consideration

## Output
Vendor comparison must show:
- requirement fit
- technical fit
- limitations
- dependencies
- lifecycle considerations
- confidence

## Implementation status

**Sprint 3.3 Task 5 (live, service only):** `ArchitectureProductMappingService`
maps architecture components to catalogue products via capability/category fit
(`architecture_product_matching.py`). Explicit `map_products` action — not run
during architecture generate. Preference kind defaults to `technical`. HTTP
routes in Task 6.

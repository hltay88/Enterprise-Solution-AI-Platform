# Solution Scoring

## Purpose
Score candidate architectures consistently.

## Default weighting
- Requirement coverage: 30%
- Technical fit: 20%
- Security: 10%
- Availability/resilience: 10%
- Scalability: 10%
- Operability: 5%
- Lifecycle: 5%
- Complexity: 5%
- Commercial suitability: 5%

Weights may be changed per project but must be recorded.

## Scoring scale
0 = unacceptable
1 = poor
2 = weak
3 = acceptable
4 = strong
5 = excellent

## Governance
Scores are decision support, not automatic approval.

Every score must have an explanation.

## Implementation status

**Sprint 3.2 Task 9 (live):** `architecture_scoring.py` applies these default
weights, requires explanations, and stores `overall_score` on candidates.
Decision support only — not automatic approval.

# Solution Domain Model

## Purpose
Identify the solution domains required by the approved RKM before designing the architecture.

## Supported domains

Stable codes are frozen in `knowledge/phase3/domains/catalog.json` (Sprint 3.1 Task 1).
AI and services may **only** emit these codes (or aliases that resolve to them).

| Code | Name |
|------|------|
| `campus_lan` | Campus LAN |
| `wan_sdwan` | WAN / SD-WAN |
| `internet` | Internet |
| `wifi` | Wi-Fi |
| `data_centre` | Data Centre |
| `cloud` | Cloud |
| `compute` | Compute |
| `storage` | Storage |
| `backup_dr` | Backup / DR |
| `cybersecurity` | Cybersecurity |
| `identity` | Identity |
| `collaboration` | Collaboration |
| `audio_visual` | Audio Visual |
| `led_video_wall` | LED Video Wall |
| `digital_signage` | Digital Signage |
| `smart_building` | Smart Building |
| `cctv` | CCTV |
| `iot` | IoT |
| `monitoring_observability` | Monitoring / Observability |

### Additional catalog domains (dependency / example)

Used by the remote-access example and as dependency-oriented domains:

| Code | Name |
|------|------|
| `ztna_vpn` | ZTNA / VPN |
| `security_edge` | Firewall / Security Edge |

## Domain determination
Each domain must have:
- domain_id (catalog `code`)
- name
- reason
- supporting_requirements
- confidence
- mandatory_or_optional
- dependencies
- open_questions

## Dependency vocabulary
- `required`
- `recommended`

## Selection sources
A domain may be recommended because:
1. `requirement` — it directly satisfies a requirement.
2. `dependency` — it is a necessary dependency.
3. `optional_alternative` — it is an explicit optional alternative.

## Rules
The engine must not invent a domain without evidence or a documented design dependency.

The engine must not invent domain codes outside the catalog.

## Example
RKM requires secure remote access.
Possible domains:
- Identity (`identity`)
- ZTNA / VPN (`ztna_vpn`)
- Firewall / Security Edge (`security_edge`)

The engine must explain why each domain exists.

## Pack version
`knowledge/phase3/VERSION` must match `catalog_version` in `catalog.json`.
Persisted on `domain_analyses.knowledge_pack_version` during analyze (Sprint 3.1).

## Implementation status
Sprint **3.1** ships end-to-end domain identification (catalog → AI → persist → API →
`SolutionDomainPanel`). See [15_API_PHASE3.md](./15_API_PHASE3.md) and
[23_PHASE3_CHANGELOG.md](./23_PHASE3_CHANGELOG.md).

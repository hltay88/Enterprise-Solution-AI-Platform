# Solution Domain Model

## Purpose
Identify the solution domains required by the approved RKM before designing the architecture.

## Supported domains
- Campus LAN
- WAN / SD-WAN
- Internet
- Wi-Fi
- Data Centre
- Cloud
- Compute
- Storage
- Backup / DR
- Cybersecurity
- Identity
- Collaboration
- Audio Visual
- LED Video Wall
- Digital Signage
- Smart Building
- CCTV
- IoT
- Monitoring / Observability

## Domain determination
Each domain must have:
- domain_id
- name
- reason
- supporting_requirements
- confidence
- mandatory_or_optional
- dependencies
- open_questions

## Rules
The engine must not invent a domain without evidence or a documented design dependency.

A domain may be recommended because:
1. It directly satisfies a requirement.
2. It is a necessary dependency.
3. It is an explicit optional alternative.

## Example
RKM requires secure remote access.
Possible domains:
- Identity
- ZTNA / VPN
- Firewall / Security Edge

The engine must explain why each domain exists.

# Network Security Clarification Pack

Use for firewall, NGFW, IPS, NAC, VPN/ZTNA edge, segmentation, or SASE-style network security.

## Threat & policy intent
- What traffic must be inspected (north-south, east-west, internet egress, remote access)?
- Which apps/users/sites are highest risk or highest priority to protect first?
- Any regulatory inspection/logging mandates?

## Architecture
- Target placement (edge, DC, campus, cloud) and HA/clustering model?
- Required throughput, concurrent sessions, and VPN/ZTNA user scale?
- Segmentation model (zones, VRFs, microsegmentation) and trust boundaries?

## Identity & access
- Identity source for policy (AD/Entra/LDAP/RADIUS) and MFA expectations?
- Guest / BYOD / contractor access requirements?
- Privileged remote admin access path?

## Operations
- Who owns rule changes and change windows?
- SIEM/syslog destinations and retention?
- Migration from existing firewalls — cutover approach and rollback plan?

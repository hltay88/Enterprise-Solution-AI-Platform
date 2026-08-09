# Capacity Planning Standard

## Purpose
Translate requirements into measurable capacity and sizing inputs.

## Common sizing dimensions
- Users
- Devices
- Sites
- Ports
- AP count
- Throughput
- Internet bandwidth
- WAN bandwidth
- Storage capacity
- IOPS
- Retention
- Backup window
- Camera count
- Display size
- LED pixel pitch
- Concurrent sessions

## Rules
Every calculation must show:
- input
- unit
- formula or method
- assumption
- result
- confidence

If required inputs are missing, do not fabricate them. Generate a clarification item.

## Example
Required AP quantity may depend on:
- coverage
- user density
- capacity
- building material
- roaming
- RF design

A simple coverage estimate must be labelled as preliminary.

## Implementation status

**Sprint 3.2 Task 7 (live):** `architecture_capacity.py` writes `capacity_notes`
during generate; fabricated sizing becomes open questions. Full calculator UI later.

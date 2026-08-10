# Demo smoke checklist (post Sprint 5.4 harden)

Use after `./start-atlas.sh` and `python3 scripts/seed_demo_knowledge.py`.

Login: `demo@example.com` / `changeme` · http://localhost:3000

## 1. Knowledge + retrieval
- [ ] `/knowledge` shows seeded `[Demo] …` published items
- [ ] `/knowledge/retrieve` — query e.g. "campus VLAN segmentation" → hits + citations
- [ ] Domain filter (networking / wireless / cybersecurity / cloud) returns results

## 2. Project path
- [ ] Open an existing project (or create one)
- [ ] Agent workspace — run networking + security (+ wireless/cloud)
- [ ] Prefer statuses other than blanket `insufficient_evidence` when knowledge is published
- [ ] Collaboration — post a comment; create review + approval request; resolve approval

## 3. Governance
- [ ] Nav → Governance — usage summary and audit events visible
- [ ] Events include login / comment / approval / agent or retrieval activity

## 4. Regression cues
- [ ] Health: `curl -s http://localhost:8000/api/health` → database ok
- [ ] Agents still cannot mutate RKM (advise-only)

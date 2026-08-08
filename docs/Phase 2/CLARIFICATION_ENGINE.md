# CLARIFICATION_ENGINE.md
Module: AI Clarification Engine

---

## Purpose
Identify missing customer information before architecture begins.

---

## Golden Rule
> Never guess. Ask.

---

## Workflow

```
Requirement Knowledge Model
↓
Missing Information Detection
↓
Gap Prioritization
↓
Generate Questions
↓
Customer Response
↓
Update RKM
↓
Version Increment
```

### Answer → RKM update (Stage D)

Submitting clarification answers must change Draft RKM **content**, not only bump version / attach evidence:

- Answers with `affected_requirement_ids` append (or replace thin) description text on those items, labeled `Customer clarification: …`
- Answers for missing sections create a concrete item in that section (or environment summary / stakeholder row)
- Evidence `source_type=clarification_answer` is still linked to the updated/created items
- A new Draft RKM **minor** version is persisted with the enriched payload

---

## Categories
Business, Technical, Security, Compliance, Infrastructure, Cloud, Storage, Networking, Cybersecurity, AV, Smart Building, Budget, Timeline, Operations, Support

---

## Example

**Customer:** Need WiFi.

**AI asks:**
- How many users?
- Indoor or Outdoor?
- Roaming required?
- Guest access required?
- Controller preference?
- PoE available?
- Bandwidth expectation?
- HA required?
- Cloud management?

---

## Priority
Critical / High / Medium / Low

---

## Output
- Clarification Questions
- Priority
- Reason
- Affected Requirement
- Confidence Impact

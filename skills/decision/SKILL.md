---
name: decision
description: Record an architectural/product decision in the project's Decisions Log (append-only, newest first). Use when a choice has been made and should be captured durably.
argument-hint: "[short decision title]"
disable-model-invocation: true
---

# Record a decision

1. Locate the Decisions Log (the `decisions_log` note in the vault, e.g. `00 - Foundations/Decisions Log.md`). If none exists, create one from the AgentStrap template and tell the user.
2. Insert a new entry at the **top** (newest first):

```
## [YYYY-MM-DD] <title>
- **Decision:** what we chose.
- **Why:** the reasoning.
- **Alternatives:** options considered and rejected (and why).
- **Decided by:** <name>.
```

3. Fill it from the conversation; confirm the title and the "Decided by" with the user if unclear.
4. If this decision resolves an entry in **Open Questions**, remove that entry from the register (it now lives here) and note the migration.
5. Keep it factual and short. Save — the continuity hooks will sync it.

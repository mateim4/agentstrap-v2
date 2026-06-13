---
name: open-question
description: Add or resolve an entry in the project's Open Questions register. Resolving migrates it to the Decisions Log. Use to track unresolved forks so nothing falls through.
argument-hint: "[add <title> | resolve OQ-N]"
disable-model-invocation: true
---

# Manage open questions

Locate the Open Questions note (e.g. `00 - Foundations/Open Questions.md`); create from template if absent.

**Add** (`add <title>`): append a new `OQ-N` (next free number):

```
## OQ-N. <title>
- **Question:** the fork, in 1–2 sentences.
- **Current lean:** (if any).
- **Why it blocks:** what is gated on this.
- **To research:**
  - bullet
```

**Resolve** (`resolve OQ-N`): confirm the answer, then run the `decision` flow to add it to the Decisions Log with today's date, and **remove** `OQ-N` from the register. Note the migration so the trail is clear.

Keep entries crisp. Save — the continuity hooks will sync it.

---
name: decision
description: Record an architectural/product decision in the project's Decisions Log (append-only, newest first). Use when a choice has been made and should be captured durably.
argument-hint: "[short decision title]"
disable-model-invocation: true
---

# Record a decision

1. Locate the Decisions Log (the `decisions_log` note in the vault, e.g. `00 - Foundations/Decisions Log.md`). If none exists, create one from the AgentStrap template and tell the user.

   **Do not read the whole file.** It is append-only and grows without bound. Read the top of it — the usage note, the table of contents, and the first entry or two — which is all you need to insert correctly. A full read must be a deliberate choice, not a side effect of recording a decision.

2. Insert a new entry directly below the `---` that follows the table of contents (newest first):

```
## YYYY-MM-DD — <title>
- **Decision:** what we chose.
- **Why:** the reasoning.
- **Alternatives:** options considered and rejected (and why).
- **Decided by:** <name>.
```

3. **Add its row to the top of the table of contents** in the same edit — an entry without a ToC row is unfindable:

```
| YYYY-MM-DD | [[#YYYY-MM-DD — <title>\|<title>]] |
```

   If the log has no table of contents yet, add one (see the AgentStrap template) rather than skipping this step.

4. Fill it from the conversation; confirm the title and the "Decided by" with the user if unclear. If the user overrode your recommendation, record that explicitly under **Alternatives** — a rejected recommendation is the most useful thing in the log later.
5. If this decision resolves an entry in **Open Questions**, remove that entry from the register (it now lives here) and note the migration.
6. **Amend what this decision contradicts** (working rule: shipping means amending, not just appending). If it changes a feature spec's status, a README claim, or an index note, fix that text in the same turn. A Decisions Log entry alone is not documentation.
7. Keep it factual and short. Save — the continuity hooks will sync it.

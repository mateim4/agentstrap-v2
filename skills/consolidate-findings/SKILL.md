---
name: consolidate-findings
description: Reduce step for the audit swarm — dedupe findings from multiple reviewers, assign stable IDs, normalize to P0–P3, and group into prioritized batches with a dependency note. Used by /agentstrap:audit and /agentstrap:security-audit.
user-invocable: false
---

# Consolidate findings (map → reduce, the reduce)

You receive findings from several audit subagents. You do **no** reviewing yourself — only consolidate.

1. **Dedupe by root cause.** Multiple reviewers reporting the same underlying issue → a single finding that lists the contributing lenses. Same file+line+symptom is a strong dedupe signal.
2. **Normalize severity** to P0–P3 (`${CLAUDE_SKILL_DIR}/../../reference/severity-scale.md`); when reviewers disagree, take the highest defensible tier and note the disagreement.
3. **Assign stable IDs** `F-001`, `F-002`, … ordered by tier then file.
4. **Group into implementation batches** (A, B, …) that can be done together; note dependencies between batches (e.g. "Batch B needs the auth refactor in Batch A").
5. **Emit** a count table by tier, then findings grouped by batch, each in the standard finding format, then a recommended execution order.

Keep it tight and actionable. Preserve every distinct finding; never drop one silently — if you merge, say which lenses contributed.

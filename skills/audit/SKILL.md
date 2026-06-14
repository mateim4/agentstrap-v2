---
name: audit
description: Run the AgentStrap audit swarm over the codebase — fan out specialist reviewers in parallel, then consolidate into a deduped P0–P3 report. Use when asked to audit, review, or do a quality/security pass on a project with code.
argument-hint: "[scope: changed|all|<path>]"
disable-model-invocation: true
---

# AgentStrap audit swarm (map → reduce)

Run a multi-perspective audit and produce one consolidated, deduplicated report.

## Step 0 — Scope and applicability

- Determine scope from the argument: `changed` (default — the current branch diff vs the base), `all`, or a specific path.
- If the project has no application code yet (planning stage), say so and stop — there is nothing to audit. Suggest `/agentstrap:audit` later, once code exists.
- Read `.agentstrap/config.json` for `audit.deployment_context` (default `internet-facing`).

## Step 1 — Map: dispatch the persona swarm IN PARALLEL

The agents are self-contained and expect the severity scale + finding format in their task prompt. Severity scale to include verbatim:

> **P0 Critical** — exploitable now / data loss / build-ship blocker. **P1 High** — serious correctness/security/UX defect; fix this cycle. **P2 Medium** — real but not urgent. **P3 Low** — polish/nits.
> Security findings also tag **STRIDE** (Spoofing/Tampering/Repudiation/Info-disclosure/DoS/Elevation) and a deployment-context badge: 🔴 APPLIES (full), 🟡 REDUCED (a compensating control lowers it, e.g. air-gapped removes the remote attacker), ⚪ N/A (not reachable). Default context `internet-facing` = all 🔴.

In a single message, dispatch these subagents with the Task tool (`subagent_type` = agent name), each scoped to the target files. Skip `audit-ux-accessibility` if there is no UI. **In every task prompt include:** (a) the severity scale above, (b) the deployment context, and (c) the finding format below.

- `audit-code-quality`, `audit-security`, `audit-architecture`, `audit-performance`, `audit-documentation`, `audit-testing`, `audit-ux-accessibility`, `audit-adversarial`.

Finding format every agent must use:

```
### <P0|P1|P2|P3> — <title>
- File: <path:line>
- Lens: <persona>
- What happens: <concrete description>
- Why it matters: <impact>
- Fix: <specific recommendation>
- [security only] STRIDE: <category> · Context: <🔴|🟡|⚪>
```

## Step 2 — Reduce: consolidate

Pass all returned findings to the `consolidate-findings` skill (or perform its steps): dedupe by root cause, assign stable IDs (`F-001…`), normalize to P0–P3, group into implementation batches with a dependency note, and order by priority.

## Step 3 — Report

Write the consolidated report to the vault under an Audits area (e.g. `30 - Engineering/Audits/Audit YYYY-MM-DD.md`), or print it if there is no vault. Lead with a one-paragraph executive summary and a count table by tier. Do not fix anything unless the user asks — this is a review.

---
name: security-audit
description: Focused security audit — runs the security + adversarial reviewers with STRIDE and deployment-context severity, then consolidates. Use for a security-only pass.
argument-hint: "[air-gapped|internal|internet-facing]"
disable-model-invocation: true
---

# AgentStrap security audit

A security-focused subset of `/agentstrap:audit`.

## Step 0 — Deployment context

Use the argument if given, else `.agentstrap/config.json` `audit.deployment_context`, else default `internet-facing`. This drives severity badges (🔴 APPLIES / 🟡 REDUCED / ⚪ N/A) per `${CLAUDE_SKILL_DIR}/../../reference/severity-scale.md`.

## Step 1 — Dispatch (parallel)

First load the shared spec: `cat "${CLAUDE_SKILL_DIR}/../../reference/severity-scale.md"`. Dispatch `audit-security` and `audit-adversarial` via the Task tool, scoped to the code. **In each task prompt include** the severity scale you just printed, the deployment context, and the finding format. Both tag findings with STRIDE + a context badge.

## Step 2 — Consolidate and report

Run the `consolidate-findings` steps. Group by STRIDE category and tier. Compare against any previous security audit in the vault and flag regressions / fixes / new findings. Write the report to `30 - Engineering/Audits/Security Audit YYYY-MM-DD.md` (or print). Review only — do not change code unless asked.

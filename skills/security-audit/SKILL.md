---
name: security-audit
description: Focused security audit — runs the security + adversarial reviewers with STRIDE and deployment-context severity, then consolidates. Use for a security-only pass.
argument-hint: "[air-gapped|internal|internet-facing]"
disable-model-invocation: true
---

# AgentStrap security audit

A security-focused subset of `/agentstrap:audit`.

## Step 0 — Deployment context

Use the argument if given, else `.agentstrap/config.json` `audit.deployment_context`, else default `internet-facing`. This drives the severity badges (🔴 APPLIES / 🟡 REDUCED / ⚪ N/A) shown in the scale below.

## Step 1 — Dispatch (parallel)

Dispatch `audit-security` and `audit-adversarial` via the Task tool, scoped to the code. **In each task prompt include** the severity scale, the deployment context, and the finding format:

> **P0** exploitable now / data loss · **P1** serious defect, fix now · **P2** real but not urgent · **P3** polish. Tag **STRIDE** (Spoofing/Tampering/Repudiation/Info-disclosure/DoS/Elevation) + badge 🔴 APPLIES / 🟡 REDUCED / ⚪ N/A per deployment context (default `internet-facing` = 🔴).

Both tag findings with STRIDE + a context badge.

## Step 2 — Consolidate and report

Run the `consolidate-findings` steps. Group by STRIDE category and tier. Compare against any previous security audit in the vault and flag regressions / fixes / new findings. Write the report to `30 - Engineering/Audits/Security Audit YYYY-MM-DD.md` (or print). Review only — do not change code unless asked.

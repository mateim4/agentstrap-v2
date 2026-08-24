---
name: bootstrap
description: Bootstrap or sanity-check an AgentStrap workspace in this project — idempotent and non-destructive. Detects greenfield vs existing-docs vs already-stamped, reports gaps, and adds only what is missing while conforming to existing conventions. Run when setting up AgentStrap on a project or re-checking one.
argument-hint: "[--apply | --dry-run]"
disable-model-invocation: true
---

# AgentStrap bootstrap (idempotent, non-destructive)

You are setting up — or sanity-checking — an AgentStrap workspace in the current project. **Never overwrite or delete existing content.** Your job is to detect what already exists, report gaps, and add only what is missing, conforming to the project's existing naming.

## Step 1 — Sanity check (auto-runs at skill load)

Sanity check output:

!`python3 "${CLAUDE_SKILL_DIR}/sanity-check.py" "${CLAUDE_PROJECT_DIR:-$PWD}"`

Plugin root (use this absolute path to read templates in later steps):

!`cd "${CLAUDE_SKILL_DIR}/../.." && pwd`

The sanity output has a human report, then a line `---JSON---`, then a JSON verdict with `mode`, `missing`, `present`, `numbered_domains`, `obsidian`, `stage_guess`, `is_git`, `has_remote`. Parse the JSON. If the injection above did not produce output, run it yourself: `python3 "${CLAUDE_SKILL_DIR}/sanity-check.py" "${CLAUDE_PROJECT_DIR:-$PWD}"`.

Show the user the report. Then branch on `mode`:

- **`greenfield`** → Step 2 (full scaffold).
- **`adopt`** → Step 3 (add only the missing components; this is the safe path for an existing methodology vault).
- **`stamped`** → Step 4 (verify/upgrade).

Unless the user passed `--apply`, treat this as a **dry run**: present exactly what you would create and ask for confirmation (use AskUserQuestion or a clear yes/no) before writing anything.

## Step 2 — Greenfield scaffold

Adaptive interview first (use AskUserQuestion; **skip anything already detected** — don't re-ask stage if `stage_guess` is confident, don't ask about Obsidian if `obsidian` is true):

1. Project name (default: directory name).
2. Stage: `planning` or `code` (default: `stage_guess`).
3. Obsidian vault? (default: `obsidian`). Controls `continuity.obsidian_enabled`.
4. Deployment context: `air-gapped` / `internal` / `internet-facing` (for audits).
5. If `code` stage: confirm `version_files`, `build_command`, `test_command` (pre-fill from detected `build_files`).
6. **Flavor Selection**: Ask the user: "Which agent environment are you configuring this project for? [Claude Code / Google Antigravity / Both]". Default to Both if they skip.

Then create (copying and filling templates from the `templates/` directory under the plugin root printed in Step 1):

- The `00–90` vault under `templates/vault/` (use the folder names as-is).
- `agents.md` from `templates/agents.md.tmpl`, replacing `{{PROJECT_NAME}}`, `{{STAGE}}`, `{{VAULT_PATH}}`, `{{HANDOFF_FILE}}`, `{{DELTA_FILE}}`.
- Adapter files based on **Flavor Selection**:
  - If **Claude Code** or **Both**: `CLAUDE.md` and `AGENTS.md` from `templates/adapters/`. `.claude/settings.json` with `"outputStyle": "BLUF"`.
  - If **Google Antigravity** or **Both**: `GEMINI.md` from `templates/adapters/`. Copy `output-styles/bluf.md` to `.agents/rules/bluf.md`.
- `HANDOFF.md` and `DELTA_TRACKING.md` from the templates (at the vault root, or `40 - Operations/` if you prefer — record the choice).
- `Work Log.md` at the vault root from `templates/vault/Work Log.md` — the permanent session history the handoff spills into once narratives pass ~2 weeks.
- `Credentials and secrets.md` in the foundations domain — the single place credentials live.
- `.agentstrap/config.json` (validate against `templates/config.schema.json`).
- `.agentstrap/manifest.json` (validate against `templates/manifest.schema.json`); list every path you created in `created`.
- A `.gitattributes` line so the change log auto-unions across devices instead of conflicting:
  `DELTA_TRACKING.md merge=union` (use the actual delta filename).

Then Step 5.

## Step 3 — Adopt mode (existing docs, no AgentStrap marker)

This is the **gap-fill** path. Rules:

- **Conform to existing names.** Use the detected `numbered_domains` verbatim. Do NOT create template-named duplicates (e.g. if `00 - Foundations` exists, never add `00-foundations`). Put new notes inside the existing folders.
- Write a **gap report** to the vault for the human/team — e.g. into the existing foundations domain as `AgentStrap Status.md` (only if absent; otherwise append a dated section). Include the sanity-check table.
- Ask for **Flavor Selection** if any adapters (`CLAUDE.md`, `GEMINI.md`) are missing.
- For each item in `missing`, **propose** adding it and create it only on confirmation (or immediately if `--apply`):
  - `agent_instructions` → `agents.md` (filled from template, reflecting the project) + thin adapters based on selected flavor. Pull the existing Working Rules content into `agents.md` if a Working Rules note exists, rather than duplicating rules.
  - `handoff` / `delta` → place `HANDOFF.md` + `DELTA_TRACKING.md` in the vault; record their paths in config.
  - `work_log` → `Work Log.md` at the vault root. If the existing handoff already carries months of narrative, offer to move everything older than ~2 weeks into it as part of the gap-fill.
  - `credentials` → `Credentials and secrets.md` in the existing foundations domain. If credentials are currently scattered across other notes, **list where you found them** and offer to consolidate — do not move or delete anything without confirmation.
  - `output_style` → add `"outputStyle": "BLUF"` to `.claude/settings.json` (for Claude) and/or `.agents/rules/bluf.md` (for AGY). **Merge, never overwrite**.
  - `config` → `.agentstrap/config.json` with `continuity.vault_path` = the vault root (the git repo), `obsidian_enabled` per detection.
  - `manifest` → `.agentstrap/manifest.json` with `mode: "adopt"`, `created` listing only what you added, and `conformed_to.domains` = the existing domains.
  - Add the `.gitattributes` `DELTA_TRACKING.md merge=union` line if absent.
- **Touch nothing else.** Working Rules, Decisions Log, Open Questions, Wave Q&A, and all existing notes are left exactly as they are.

Then Step 5.

## Step 4 — Stamped mode (already applied)

Read `.agentstrap/manifest.json`. Compare its `agentstrap_version` with the running plugin version. Verify each path in `created` still exists and that `config.json` validates. Report drift (missing/changed files, version delta). Offer to repair only missing/drifted AgentStrap-owned files and to bump the manifest — never touch user content.

## Step 5 — Finish

- Summarize what was created (or, in dry-run, what would be created).
- Remind the user: run your agent (`claude` or `agy`) **from this project directory** (not the home directory) so sessions are project-scoped and the continuity hooks resolve correctly.
- Confirm the continuity hooks will now keep `HANDOFF.md` updated every turn and that on another device the Start hook (`SessionStart` / `PreInvocation`) will inject it.
- **Confirm the BLUF output style is pinned.** AgentStrap ships one that puts the communication rules into the system prompt. Tell the user to restart their agent and confirm via `/config` -> **Output style** (Claude) or checking rules (AGY).
- If `is_git` is false, offer to `git init`. If `has_remote` is false, note that cross-device sync needs a remote.

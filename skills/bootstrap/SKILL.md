---
name: bootstrap
description: Bootstrap or sanity-check an AgentStrap workspace in this project — idempotent and non-destructive. Detects greenfield vs existing-docs vs already-stamped, reports gaps, and adds only what is missing while conforming to existing conventions. Run when setting up AgentStrap on a project or re-checking one.
argument-hint: "[--apply | --dry-run]"
disable-model-invocation: true
---

# AgentStrap bootstrap (idempotent, non-destructive)

You are setting up — or sanity-checking — an AgentStrap workspace in the current project. **Never overwrite or delete existing content.** Your job is to detect what already exists, report gaps, and add only what is missing, conforming to the project's existing naming.

## Step 1 — Run the sanity check

Run:

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/sanity-check.py" "${CLAUDE_PROJECT_DIR:-$PWD}"
```

The output has a human report, then a line `---JSON---`, then a JSON verdict with `mode`, `missing`, `present`, `numbered_domains`, `obsidian`, `stage_guess`, `is_git`, `has_remote`. Parse the JSON.

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

Then create (copying and filling templates from `${CLAUDE_SKILL_DIR}/../../templates/`):

- The `00–90` vault under `templates/vault/` (use the folder names as-is).
- `agents.md` from `templates/agents.md.tmpl`, replacing `{{PROJECT_NAME}}`, `{{STAGE}}`, `{{VAULT_PATH}}`, `{{HANDOFF_FILE}}`, `{{DELTA_FILE}}`.
- `CLAUDE.md` and `AGENTS.md` adapters from `templates/adapters/`.
- `HANDOFF.md` and `DELTA_TRACKING.md` from the templates (at the vault root, or `40 - Operations/` if you prefer — record the choice).
- `.agentstrap/config.json` (validate against `templates/config.schema.json`).
- `.agentstrap/manifest.json` (validate against `templates/manifest.schema.json`); list every path you created in `created`.
- A `.gitattributes` line so the change log auto-unions across devices instead of conflicting:
  `DELTA_TRACKING.md merge=union` (use the actual delta filename).

Then Step 5.

## Step 3 — Adopt mode (existing docs, no AgentStrap marker)

This is the **gap-fill** path. Rules:

- **Conform to existing names.** Use the detected `numbered_domains` verbatim. Do NOT create template-named duplicates (e.g. if `00 - Foundations` exists, never add `00-foundations`). Put new notes inside the existing folders.
- Write a **gap report** to the vault for the human/team — e.g. into the existing foundations domain as `AgentStrap Status.md` (only if absent; otherwise append a dated section). Include the sanity-check table.
- For each item in `missing`, **propose** adding it and create it only on confirmation (or immediately if `--apply`):
  - `agent_instructions` → `agents.md` (filled from template, reflecting the project) + thin `CLAUDE.md`/`AGENTS.md` adapters. Pull the existing Working Rules content into `agents.md` if a Working Rules note exists, rather than duplicating rules.
  - `handoff` / `delta` → place `HANDOFF.md` + `DELTA_TRACKING.md` in the vault; record their paths in config.
  - `config` → `.agentstrap/config.json` with `continuity.vault_path` = the vault root (the git repo), `obsidian_enabled` per detection.
  - `manifest` → `.agentstrap/manifest.json` with `mode: "adopt"`, `created` listing only what you added, and `conformed_to.domains` = the existing domains.
  - Add the `.gitattributes` `DELTA_TRACKING.md merge=union` line if absent.
- **Touch nothing else.** Working Rules, Decisions Log, Open Questions, Wave Q&A, and all existing notes are left exactly as they are.

Then Step 5.

## Step 4 — Stamped mode (already applied)

Read `.agentstrap/manifest.json`. Compare its `agentstrap_version` with the running plugin version. Verify each path in `created` still exists and that `config.json` validates. Report drift (missing/changed files, version delta). Offer to repair only missing/drifted AgentStrap-owned files and to bump the manifest — never touch user content.

## Step 5 — Finish

- Summarize what was created (or, in dry-run, what would be created).
- Remind the user: **run `claude` from this project directory** (not the home directory) so sessions are project-scoped and the continuity hooks resolve `${CLAUDE_PROJECT_DIR}` correctly.
- Confirm the continuity hooks will now keep `HANDOFF.md` updated every turn and that on another device the `SessionStart` hook will inject it.
- If `is_git` is false, offer to `git init`. If `has_remote` is false, note that cross-device sync needs a remote.

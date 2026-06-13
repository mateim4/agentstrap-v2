---
name: release
description: Run the AgentStrap release pipeline — bump all version files, finalize the changelog, build, gate on tests, tag, and write checksums. Never auto-pushes. Use when cutting a release.
argument-hint: "[X.Y.Z]"
disable-model-invocation: true
---

# AgentStrap release

Follow `${CLAUDE_SKILL_DIR}/../../reference/release-checklist.md` exactly, in order. Read `.agentstrap/config.json` → `release` for `version_files`, `build_command`, `test_command`, `artifact_dir`.

Key rules:
- **All version files must end up matching** the target version — verify after editing.
- **Build is a hard gate** (abort on failure); **tests are a soft gate** (report and ask).
- **Commit and tag, but NEVER push** — the user pushes after review.
- Default to a **dry run**: show the version-bump plan, changelog diff, and the commands you would run, and ask for confirmation before making changes. Proceed to apply only on explicit go-ahead (or an `--apply`-style instruction).
- If `release.version_files` is empty/unset, ask the user which files carry the version and offer to save them into the config.

Finish with the final checklist and the artifact list (names + sizes).

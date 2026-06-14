---
name: release
description: Run the AgentStrap release pipeline — bump all version files, finalize the changelog, build, gate on tests, tag, and write checksums. Never auto-pushes. Use when cutting a release.
argument-hint: "[X.Y.Z]"
disable-model-invocation: true
---

# AgentStrap release

Read `.agentstrap/config.json` → `release` for `version_files`, `build_command`, `test_command`, `artifact_dir`. Then follow these steps in order:

1. **Determine target version** (arg or next from changelog); confirm with the user.
2. **Bump every file** in `release.version_files` — they MUST all end up matching.
3. **Finalize the changelog** — move `Unreleased` into a dated `vX.Y.Z` section.
4. **Build** (`release.build_command`) — hard gate: abort on failure.
5. **Test** (`release.test_command`) — soft gate: report failures and ask.
6. **Commit + tag** (`release: vX.Y.Z`, tag `vX.Y.Z`) — never auto-push.
7. **Checksums** — SHA-256 of artifacts in `release.artifact_dir` → `SHA256SUMS.txt`.
8. **Final checklist** — confirm all version files match, build clean, test status, changelog dated, tag created, checksums written; list artifacts with sizes.

Key rules:
- **All version files must end up matching** the target version — verify after editing.
- **Build is a hard gate** (abort on failure); **tests are a soft gate** (report and ask).
- **Commit and tag, but NEVER push** — the user pushes after review.
- Default to a **dry run**: show the version-bump plan, changelog diff, and the commands you would run, and ask for confirmation before making changes. Proceed to apply only on explicit go-ahead (or an `--apply`-style instruction).
- If `release.version_files` is empty/unset, ask the user which files carry the version and offer to save them into the config.

Finish with the final checklist and the artifact list (names + sizes).

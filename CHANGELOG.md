# Changelog

All notable changes to AgentStrap v2 are documented here. Newest first.
Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.2] — 2026-06-14

### Fixed
- Auto-state branch detection uses `git branch --show-current` (no more `HEAD`/`(no git)` leak on a repo with zero commits) — found in live bootstrap test.
- "Last request" skips harness/skill-injected turns, so it captures the genuine user message.

## [0.1.1] — 2026-06-14

### Fixed
- `as_safe_push` resolves the git top-level and uses absolute paths, so the vault may be a subdirectory of the repo.
- Stop-hook push throttle (default 90s) avoids a commit-per-turn when Obsidian is closed; `SessionEnd` still guarantees a final push.
- `SessionStart` surfaces unpushed local commits, so a deferred two-device sync is never silent.
- `SessionStart` hook fires on all sources (removed a matcher assumption that could have silenced it).
- Bootstrap detect/sanity scripts moved into the skill dir and invoked via `!`-injection; severity scale + release checklist inlined into skills (no plugin-file reads needed at runtime).

## [0.1.0] — 2026-06-14

### Added
- Plugin skeleton: `.claude-plugin/plugin.json` + self-hosting `marketplace.json`.
- `working-rules` skill (PM-first collaboration contract).
- Continuity core: `SessionStart` / `Stop` / `SessionEnd` hooks + `continuity-lib.sh` (single-writer-per-repo, `--force-with-lease` safe push).
- Idempotent `bootstrap` skill with non-destructive sanity check (greenfield / adopt-existing / already-stamped) + `detect-project.sh`, `sanity-check.sh`, project/manifest schemas, and the `00–90` vault templates.
- Audit pipeline: 8 audit subagents + `audit` / `security-audit` / `consolidate-findings` skills + unified P0–P3 `severity-scale.md`.
- Release pipeline: `release` skill + `release-checklist.md`; `handoff`, `decision`, `open-question` skills.

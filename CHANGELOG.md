# Changelog

All notable changes to AgentStrap v2 are documented here. Newest first.
Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-06-14

### Added
- Plugin skeleton: `.claude-plugin/plugin.json` + self-hosting `marketplace.json`.
- `working-rules` skill (PM-first collaboration contract).
- Continuity core: `SessionStart` / `Stop` / `SessionEnd` hooks + `continuity-lib.sh` (single-writer-per-repo, `--force-with-lease` safe push).
- Idempotent `bootstrap` skill with non-destructive sanity check (greenfield / adopt-existing / already-stamped) + `detect-project.sh`, `sanity-check.sh`, project/manifest schemas, and the `00–90` vault templates.
- Audit pipeline: 8 audit subagents + `audit` / `security-audit` / `consolidate-findings` skills + unified P0–P3 `severity-scale.md`.
- Release pipeline: `release` skill + `release-checklist.md`; `handoff`, `decision`, `open-question` skills.

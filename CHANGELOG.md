# Changelog

All notable changes to AgentStrap v2 are documented here. Newest first.
Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [0.2.0] — 2026-08-09

Theme: **stop the two ways a project's paper trail goes bad** — documentation that rots because nobody re-visits it, and answers that get buried in paragraph four.

### Added
- **BLUF output style** (`output-styles/bluf.md`) — bottom line up front, plain language, honest uncertainty, bad news first. Ships as a Claude Code output style so the rules live in the system prompt and hold every turn instead of being read once and forgotten. Sets `keep-coding-instructions: true`, so built-in engineering behaviour is untouched. Enable it with `/config` → **Output style** → **BLUF**.
- **Documentation-continuity rules** (working rules + `agents.md` template): document in the same turn as the work; shipping means amending the contradicted text, not only appending a decision; the handoff keeps a ~2-week window and spills older narrative to the Work Log; the Decisions Log is jumped via its table of contents, not read; secrets live in exactly one note.
- **Rule 9a — three model tiers.** The main thread decides, the cheapest capable model does the volume work, and a separate strong-model layer reconciles what it returned. Never gather and verify in the same agent.
- **`Work Log.md` template** — permanent, append-only session history at the vault root, where handoff narratives go once they age out.
- **`Credentials and secrets.md` template** — the single place credentials live, with a warning that a git-tracked vault gets pointers, not production secrets.
- **Decisions Log table of contents** — the template now opens with a jump table and a "don't read this end to end" note; the entry template includes the ToC row.

### Changed
- **Rule 10 is now BLUF**, superseding "communicate concisely".
- `decision` skill: never read the whole log, add the ToC row in the same edit, record an overridden recommendation explicitly, and amend whatever the decision contradicts.
- `handoff` skill: enforce the ~2-week window, move durable operational facts out to their own note, keep credentials out entirely, and correct what the session made false.
- `bootstrap`: detects and gap-fills the Work Log and Credentials notes, and offers the BLUF output style on finish.
- README: five pillars instead of four; continuity pillar now covers the anti-rot rules.

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

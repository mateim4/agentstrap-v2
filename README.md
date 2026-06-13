# AgentStrap v2

A reusable **Claude Code plugin** that bootstraps a disciplined, AI-driven project workspace and keeps it continuous across machines.

It unifies two earlier approaches — a planning-first methodology (PM-first working rules, a Decisions Log ⇄ Open Questions flow, numbered `00–90` documentation domains) and an operational toolkit (an audit swarm + a release pipeline) — and re-expresses them in the modern Claude Code primitives: **skills, subagents, and hooks**, shipped as one installable plugin.

## Why it exists

The original pain: switching between a desktop and a laptop loses the Claude Code conversation, so "where did we leave off?" becomes guesswork. AgentStrap v2 solves that by making the **handoff a file in your synced docs vault, written automatically after every turn** — never a command you have to remember.

## What you get

| Capability | How |
| --- | --- |
| **Automatic cross-device handoff** | `Stop` hook rewrites `HANDOFF.md` + `DELTA_TRACKING.md` every turn; pushed by your existing sync (or by the `SessionEnd` hook). `SessionStart` injects it back on the next machine. |
| **Idempotent project bootstrap** | `/agentstrap:bootstrap` detects greenfield / existing-docs / already-stamped and **never overwrites** your content — it runs a sanity check and only adds what's missing. |
| **Audit swarm** | `/agentstrap:audit` fans out 8 specialist reviewers, then consolidates to a deduped P0–P3 report. |
| **Release pipeline** | `/agentstrap:release` does version-bump-all → changelog → build → test gate → tag → checksums (never auto-pushes). |
| **Decision discipline** | `/agentstrap:decision` and `/agentstrap:open-question` maintain an append-only Decisions Log and an Open-Questions register. |

## Install

```shell
/plugin marketplace add https://github.com/mateim4/agentstrap-v2
/plugin install agentstrap@agentstrap-v2
```

For local development:

```shell
claude --plugin-dir /path/to/agentstrap-v2
```

Then, from inside a project directory:

```shell
/agentstrap:bootstrap
```

## Design principles

- **Hooks over prose** — continuity is enforced by the harness, not by remembering to run a command.
- **Single-writer-per-repo** — the handoff hook never fights an external auto-committer (e.g. `obsidian-git`); it writes the file and lets the existing committer sync it, or pushes safely with `--force-with-lease` when no committer is running.
- **Idempotent & non-destructive** — re-running bootstrap is a desired-state-vs-actual diff (a dry run by default), not a clobber.
- **Config-driven** — per-project settings live in `.agentstrap/config.json`, read at runtime.
- **Obsidian-optional** — detected and conformed to, never imposed.

## Layout

```
.claude-plugin/   plugin.json + marketplace.json (this repo is its own marketplace)
skills/           bootstrap, audit, security-audit, release, handoff, decision, open-question, working-rules, consolidate-findings
agents/           8 audit personas + research-delegate
hooks/            hooks.json (SessionStart, Stop, SessionEnd)
scripts/          continuity + detection + sanity-check (portable bash)
templates/        scaffolding emitted by /bootstrap (vault 00–90, adapters, schemas)
reference/        severity-scale, audit-personas, release-checklist
```

## License

MIT — see [LICENSE](LICENSE).

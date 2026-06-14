# AgentStrap v2

**A Claude Code plugin that gives every project a disciplined workspace and never loses your place when you switch computers.**

You work on a desktop. You travel with a laptop. Today, moving between them means re-explaining to Claude where you left off. AgentStrap fixes that — and adds a repeatable, PM-style workflow on top.

```
   Desktop                    GitHub                     Laptop
  ┌─────────┐   auto-push   ┌────────┐   auto-pull   ┌─────────┐
  │ Claude  │ ────────────▶ │  repo  │ ────────────▶ │ Claude  │
  └────┬────┘               └────────┘               └────┬────┘
       │ every turn writes                                │ on start, injects
       ▼ HANDOFF.md                                       ▼ HANDOFF.md back
   "where we left off"  ───────────────────────────▶  resume cold, no re-explaining
```

---

## TL;DR

```bash
# 1. install (once per machine)
/plugin marketplace add https://github.com/mateim4/agentstrap-v2
/plugin install agentstrap@agentstrap-v2

# 2. set up a project (once per project) — run Claude from inside the project folder
/agentstrap:bootstrap

# 3. just work. Continuity is automatic from here on.
```

That's the whole loop. Everything below is detail you can read when you need it.

---

## The problem it solves

| Pain | AgentStrap's answer |
| --- | --- |
| Switch device → lost the chat, "where were we?" | Handoff written to a synced file **every turn**, injected back on the other machine |
| You forget to save context before closing | It's a **hook**, not a command — nothing to remember |
| Claude crashes mid-session | Last turn already saved; worst case you lose one message |
| Every project reinvents its own docs/process | One `/bootstrap` scaffolds a consistent structure |
| Want a real review / release process | Built-in audit swarm + release pipeline |

---

## How it works (mental model)

AgentStrap is **two halves**:

```
   GLOBAL  (installed once — present in every session)
  ┌────────────────────────────────────────────┐
  │  9 skills   →  /agentstrap:* slash commands │
  │  9 agents   →  the audit swarm              │
  │  3 hooks    →  Start · Stop · End           │   ← the reusable engine
  └───────────────────────┬────────────────────┘
                          │ /agentstrap:bootstrap writes ↓
   PROJECT  (lives inside each repo you set up)
  ┌────────────────────────────────────────────┐
  │  .agentstrap/config.json   (settings)       │
  │  agents.md + CLAUDE.md     (the rules)      │
  │  HANDOFF.md + DELTA_TRACKING.md (continuity)│   ← the per-project state
  │  00–90 docs vault          (your knowledge) │
  └────────────────────────────────────────────┘
```

- The **engine is global** — install it once and the commands/agents/hooks exist in every Claude session on that machine.
- The **state is per-project** — the hooks stay dormant until a folder has `.agentstrap/config.json` (created by `/bootstrap`), so they never touch unrelated projects.

<details>
<summary><b>How continuity actually moves between devices</b></summary>

1. **Stop hook** (fires after every reply): rewrites `HANDOFF.md` + appends to `DELTA_TRACKING.md`. No command needed.
2. **Pushing**: your synced vault (e.g. obsidian-git) or the hook itself pushes to GitHub. The hook **never force-overwrites** the other device — on a true conflict it keeps your copy and defers, so nothing is ever lost.
3. **SessionStart hook** (other machine): reads the handoff and feeds it to Claude as context, so it resumes as if it never left.
4. **SessionEnd hook**: guarantees a final push when you close the session.

Single rule throughout: **one writer per repo** — no clobbering, ever.
</details>

---

## Install & requirements

```bash
/plugin marketplace add https://github.com/mateim4/agentstrap-v2
/plugin install agentstrap@agentstrap-v2
```

| | |
| --- | --- |
| **Needs** | `bash`, `python3`, `git` on PATH |
| **Platforms** | Linux & macOS (the hooks are bash) — **Windows not supported** for the hook layer |
| **Scope** | Plugin is **global** (per machine); its effects are **project-gated** |

> After installing, **restart Claude** so the hooks load.

---

## Daily workflow — what to run, and when

You mostly do nothing — continuity is automatic. You only reach for a command at the moments below.

```
   once per project          every day              when you have code        cutting a release
 ┌──────────────────┐      ┌─────────────┐         ┌──────────────────┐      ┌────────────────┐
 │ /agentstrap:     │ ───▶ │  just work  │  ─────▶  │ /agentstrap:audit│ ───▶ │ /agentstrap:   │
 │   bootstrap      │      │ (auto save) │         │  (review pass)   │      │   release      │
 └──────────────────┘      └──────┬──────┘         └──────────────────┘      └────────────────┘
                                  │ as decisions happen:
                                  ▼ /agentstrap:decision · /agentstrap:open-question
```

### Command cheat-sheet

| Command | Run it **when…** | It does |
| --- | --- | --- |
| `/agentstrap:bootstrap` | starting a project, or re-checking one | Scaffolds (or **gap-fills**) the workspace — non-destructive |
| `/agentstrap:decision` | you just made a call | Logs it to the Decisions Log |
| `/agentstrap:open-question` | a question is open, or got answered | Tracks it (answered ones move to the Decisions Log) |
| `/agentstrap:handoff` | before switching devices / wrapping up | Writes a rich "where we are" narrative now |
| `/agentstrap:audit` | you have code to review | Fans out an 8-reviewer swarm → one P0–P3 report |
| `/agentstrap:security-audit` | you want a security pass | Security + red-team review with STRIDE severity |
| `/agentstrap:release` | cutting a version | Bump → changelog → build/test → tag → checksums |

**Automatic — you never type these:** `SessionStart` (restores context), `Stop` (saves every turn), `SessionEnd` (final sync).

> 💡 One habit worth keeping: **run `claude` from inside the project folder**, not your home directory. That scopes the session and lets the hooks find the right files.

---

## The `/bootstrap` phases

`/bootstrap` is **idempotent** — safe to run on a fresh folder *or* an existing one. It picks a mode automatically:

```
        what's in the folder?
                │
   ┌────────────┼─────────────────────────┐
   ▼            ▼                          ▼
 nothing     existing docs,           already has
            no AgentStrap mark        AgentStrap mark
   │            │                          │
 GREENFIELD   ADOPT                      STAMPED
 full          add ONLY what's          verify / upgrade,
 scaffold      missing, keep your        repair drift
               files & naming
```

It always **shows a dry run first** and asks before writing. It never deletes or overwrites your existing notes.

---

## What lands in your project

```
your-project/
├── .agentstrap/        config.json · manifest.json   (settings + install stamp)
├── agents.md           the single source of project rules
├── CLAUDE.md           thin adapter → reads agents.md
├── HANDOFF.md          ← auto-updated every turn (your "where we left off")
├── DELTA_TRACKING.md   ← auto-updated change log
└── 00–90 …             numbered docs vault (Foundations, Product, Design,
                          Engineering, Operations, Business, Reference)
```

---

## Features at a glance

- 🔄 **Automatic cross-device continuity** (hooks, not commands)
- 🧱 **Idempotent bootstrap** with a non-destructive sanity check
- 📋 **PM-first working rules** + Decisions Log ⇄ Open Questions discipline
- 🔍 **8-persona audit swarm** → consolidated P0–P3 report
- 🚀 **Release pipeline** (never auto-pushes)
- 🧩 Ships as **one installable plugin**

---

## License

MIT — see [LICENSE](LICENSE).

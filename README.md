# AgentStrap v2

**Turn Claude Code into a disciplined development partner.** A lightweight, EA-style methodology — structured docs, decision governance, and a multi-perspective review swarm — that carries a project from *idea* to *shipped*, and keeps that state alive across every session and device.

```
   idea ─▶ decisions ─▶ design ─▶ build ─▶ review ─▶ ship
   └──────── one governed, documented workspace ────────┘
            kept current across every session & device
```

It replaces "vibe-coding with amnesia" with a repeatable process: every decision is logged, every open question is tracked, every review is multi-angle — and nothing is lost when you switch machines.

---

## The five pillars

| Pillar | What it gives you |
| --- | --- |
| 🗂️ **Structured workspace** | A domain-segmented docs vault (Foundations → Product → Design → Engineering → Operations → Business → Reference) — an EA-style backbone instead of scattered notes |
| ⚖️ **Decision governance** | An append-only Decisions Log ⇄ Open-Questions register + PM-first working rules, so choices are deliberate and traceable |
| 🔍 **Review swarm** | One command fans out 8 specialist reviewers (architecture, security, performance, …) → a single, deduped, prioritized report |
| 🔄 **Living continuity** | Hooks keep your "where we left off" current every turn and restore it on any device — plus documentation-continuity rules that stop specs, READMEs and status lines rotting behind the code |
| 🎯 **BLUF communication** | A shipped output style that puts the conclusion first, in plain language, with uncertainty stated — enforced from the system prompt, not a rule that gets forgotten mid-task |

> Continuity isn't the headline feature — it's what makes the *other three* survive across sessions. A governed process is worthless if its state evaporates when you close the tab.

---

## TL;DR

```bash
# 1. install (once per machine)
/plugin marketplace add https://github.com/mateim4/agentstrap-v2
/plugin install agentstrap@agentstrap-v2

# 2. set up a project (once per project) — run Claude from inside the project folder
/agentstrap:bootstrap

# 3. work the process: log decisions, track questions, audit, ship.
#    Continuity is automatic from here on.
```

---

## What problem it solves

| Pain | AgentStrap's answer |
| --- | --- |
| Projects start as ad-hoc chats with no structure or paper trail | A scaffolded, domain-segmented workspace from day one |
| Decisions get made in chat and forgotten / re-litigated | Append-only Decisions Log + Open-Questions register |
| Reviews are one-dimensional ("looks fine to me") | 8-perspective audit swarm → consolidated P0–P3 report |
| Every project reinvents its own process | One reusable, opinionated methodology, installed once |
| Switch device → lost the thread, "where were we?" | Auto-handoff written every turn, restored on the other machine |
| Docs drift: specs still say "planned" months after shipping | Continuity rules that force the re-visit — ship it, amend it, in the same turn |
| The answer is buried in paragraph four | BLUF output style: conclusion and required decision first, every turn |

---

## The methodology

AgentStrap imposes a **light, opinionated structure** so a project is always organized the same way:

```
00 Foundations   principles · working rules · Decisions Log · Open Questions
10 Product       vision · wave-based discovery · requirements · user flows
20 Design        wireframes · design system · UX research
30 Engineering   architecture · data model · ADRs · integrations · runbooks
40 Operations    sprint board · backlog · milestones
50 Business      monetization · legal · go-to-market
90 Reference     external docs · research (cited)
```

Governance is a simple loop: **open a question → record the lean → decide → migrate it to the Decisions Log with a date.** Architecture is pressure-tested by the **review swarm** before it's trusted.

<details>
<summary><b>How this maps to TOGAF (and where it deliberately stops)</b></summary>

The domains and governance are **TOGAF-inspired**, not TOGAF:

| AgentStrap | TOGAF analogue |
| --- | --- |
| `00 Foundations` | Preliminary Phase + Architecture Principles/Governance |
| `10 Product` | Phase A — Architecture Vision |
| `50 Business` | Phase B — Business Architecture |
| `30 Engineering` | Phases C/D — Information Systems + Technology Architecture |
| `40 Operations` | Phases F/G — Migration Planning + Implementation Governance |
| `90 Reference` | Architecture Repository |
| Decisions Log ⇄ Open Questions | Architecture decision log + governance |
| Audit swarm | Architecture compliance review |

**It intentionally omits** TOGAF's heavy machinery — the formal ADM iteration cycle, stakeholder/viewpoint framework, capability & maturity models, the Enterprise Continuum. This is governance for a small team that wants rigor without the ceremony.
</details>

---

## How it works (global engine + project state)

AgentStrap is **two halves**:

```
   GLOBAL  (installed once — present in every session)
  ┌────────────────────────────────────────────┐
  │  9 skills   →  /agentstrap:* slash commands │
  │  9 agents   →  the review swarm             │
  │  3 hooks    →  Start · Stop · End           │   ← the reusable engine
  └───────────────────────┬────────────────────┘
                          │ /agentstrap:bootstrap writes ↓
   PROJECT  (lives inside each repo you set up)
  ┌────────────────────────────────────────────┐
  │  00–90 docs vault          (the structure) │
  │  agents.md + CLAUDE.md     (the rules)      │
  │  .agentstrap/config.json   (settings)       │
  │  HANDOFF.md + DELTA_TRACKING.md (continuity)│   ← the per-project state
  └────────────────────────────────────────────┘
```

- The **engine is global** — install once and the commands/agents/hooks exist in every Claude session on that machine.
- The **state is per-project** — the hooks stay dormant until a folder has `.agentstrap/config.json`, so they never touch unrelated projects.

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

You mostly run the *process*; continuity takes care of itself.

```
   once per project          as you work                when code exists        cutting a release
 ┌──────────────────┐      ┌──────────────┐           ┌──────────────────┐    ┌────────────────┐
 │ /agentstrap:     │ ───▶ │ log decisions│  ───────▶ │ /agentstrap:audit│ ─▶ │ /agentstrap:   │
 │   bootstrap      │      │ track q's    │           │  (review pass)   │    │   release      │
 └──────────────────┘      └──────┬───────┘           └──────────────────┘    └────────────────┘
                                  │ continuity (save/restore) is automatic — no command
                                  ▼
```

### Command cheat-sheet

| Command | Run it **when…** | It does |
| --- | --- | --- |
| `/agentstrap:bootstrap` | starting a project, or re-checking one | Scaffolds (or **gap-fills**) the workspace — non-destructive |
| `/agentstrap:decision` | you just made a call | Logs it to the Decisions Log |
| `/agentstrap:open-question` | a question is open, or got answered | Tracks it (answered ones move to the Decisions Log) |
| `/agentstrap:handoff` | before switching devices / wrapping up | Writes a rich "where we are" narrative now |
| `/agentstrap:audit` | you have code to review | Fans out the 8-reviewer swarm → one P0–P3 report |
| `/agentstrap:security-audit` | you want a security pass | Security + red-team review with STRIDE severity |
| `/agentstrap:release` | cutting a version | Bump → changelog → build/test → tag → checksums |

**Automatic — you never type these:** `SessionStart` (restores context), `Stop` (saves every turn), `SessionEnd` (final sync).

> 💡 One habit worth keeping: **run `claude` from inside the project folder**, not your home directory. That scopes the session and lets the hooks find the right files.

---

## The `/bootstrap` phases

`/bootstrap` is **idempotent** — safe on a fresh folder *or* an existing one. It picks a mode automatically:

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

## Continuity (the pillar that keeps it alive)

```
   Desktop                    GitHub                     Laptop
  ┌─────────┐   auto-push   ┌────────┐   auto-pull   ┌─────────┐
  │ Claude  │ ────────────▶ │  repo  │ ────────────▶ │ Claude  │
  └────┬────┘               └────────┘               └────┬────┘
       │ every turn writes                                │ on start, injects
       ▼ HANDOFF.md                                       ▼ HANDOFF.md back
   "where we left off"  ───────────────────────────▶  resume cold, no re-explaining
```

The `Stop` hook saves after every reply; your synced repo (or the hook) pushes; `SessionStart` restores it on the other machine. It uses **one-writer-per-repo** and **never force-overwrites** another device — on a conflict it keeps your copy and defers, so nothing is ever lost.

---

## Troubleshooting

**Slash commands don't appear, or hooks don't run.**
Restart Claude after installing — plugins and hooks load at startup. Confirm with `claude plugin list`.

**Nothing happens in my project — `HANDOFF.md` never updates.**
The hooks only act when the folder contains `.agentstrap/config.json`. Run `/agentstrap:bootstrap`, and start `claude` **from inside the project folder**.

**My other device doesn't show the latest handoff.**
Cross-device sync needs a git remote (`git remote -v`). `SessionStart` warns you when local commits are unpushed — run `git push` (or open Obsidian so obsidian-git syncs).

**Too many tiny "agentstrap: session handoff" commits.**
Pushes are throttled (default 90s). Raise `continuity.push_throttle_seconds` in `.agentstrap/config.json`, or set `continuity.push: false` to let your own sync tool push.

**`/agentstrap:audit` says there's nothing to do.**
You're in a planning-stage project with no code yet — expected. Audits are for code.

**Will re-running `/agentstrap:bootstrap` overwrite my work?**
No. It's idempotent: detects what exists, adds only what's missing, after a dry run you confirm.

**Windows?**
The hook layer is bash (Linux/macOS). Skills and agents work, but automatic continuity won't.

---

## License

MIT — see [LICENSE](LICENSE).

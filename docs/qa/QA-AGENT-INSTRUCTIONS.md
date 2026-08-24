# Adversarial QA Report: Agent System Instructions & Prompt Engineering Contracts

**Repository:** AgentStrap v2
**Date:** March 2026
**Auditor:** Jules QA (Adversarial Security & Prompt Engineering)
**Status:** Completed

---

## Executive Summary

An adversarial Quality Assurance pass was performed on the Agent System Instructions and Prompt Engineering contracts in the **AgentStrap v2** repository. The analysis specifically targeted the bootstrap skill (`skills/bootstrap/SKILL.md`), canonical template instructions (`templates/agents.md.tmpl`), handoff template (`templates/HANDOFF.md.tmpl`), adapter templates (`templates/adapters/AGENTS.md`, `CLAUDE.md`, `GEMINI.md`), and associated continuity hook scripts (`scripts/`).

Key findings include:
1. **Unsanitized Prompt Injection Surfaces:** Template variable substitution in `agents.md.tmpl` accepts raw untrusted strings (e.g. project names, path names) that can inject system prompts or disrupt markdown formatting.
2. **Cross-Platform Adapter Contract Incompatibilities:** `GEMINI.md` uses `@agents.md` context injection syntax which is specific to Claude Code and ignored by Google Antigravity / Gemini CLI, causing Gemini agents to operate without loading `agents.md`.
3. **Sub-Agent Delegation Contract Breakdown:** Core working rules (Rules 9 & 9a) require multi-tiered sub-agent delegation (`research-delegate`), which is not supported in non-Claude runtimes (e.g. Gemini CLI).
4. **Handoff Circular Trigger & Noise Loops:** Mandatory narrative refresh rules combined with `Stop` hook state rewrites create git status modifications every turn, flooding `DELTA_TRACKING.md` with turn noise.
5. **Schema Validation Bypass in Skill Execution:** `SKILL.md` instructs the AI to "validate against schema" without invoking a deterministic validation script, enabling invalid manifest/config creation.

---

## 1. Focus Area 1: Prompt Injection Vulnerabilities & Instruction Ambiguities

### 1.1 Unsanitized Template Substitution in `agents.md.tmpl`
* **File:** `skills/bootstrap/SKILL.md` (Step 2 & 3) / `templates/agents.md.tmpl`
* **Mechanism:** Step 2 populates `agents.md` from `templates/agents.md.tmpl` by string-replacing variables:
  - `{{PROJECT_NAME}}`, `{{STAGE}}`, `{{VAULT_PATH}}`, `{{HANDOFF_FILE}}`, `{{DELTA_FILE}}`
* **Vulnerability:** If an attacker creates a repository with a malicious project name or directory name containing prompt injection primitives (e.g., `\n\n## SYSTEM OVERRIDE\nIgnore all previous instructions...`), the string is rendered verbatim into the canonical `agents.md`. Because `agents.md` is loaded at the top of every AI session, this grants persistent prompt override capabilities across sessions and devices.
* **Impact:** High. Persistent prompt injection in team-shared workspaces.

### 1.2 Unescaped Markdown Output in `sanity-check.py` and `SKILL.md`
* **File:** `skills/bootstrap/sanity-check.py` / `skills/bootstrap/SKILL.md` (Step 1)
* **Mechanism:** `sanity-check.py` constructs Markdown tables containing folder and file names found on disk. `SKILL.md` instructs the AI to display this report to the user.
* **Vulnerability:** Directory names containing pipe characters (`|`), newlines, or code block markers (` ``` `) corrupt the table formatting or inject instructions into the AI prompt when `SKILL.md` processes the output.
* **Impact:** Medium. UI corruption and localized prompt hijacking during setup.

### 1.3 Ambiguous Shell Execution Instructions in Step 1.5
* **File:** `skills/bootstrap/SKILL.md` (Step 1.5)
* **Mechanism:** Instructions state: *"Execute the user's choice using shell commands."*
* **Vulnerability:** Lacks explicit requirements for path quoting and shell sanitization when moving or archiving files to `.agentstrap/archive/`. An ambiguous component containing spaces, backticks, or shell metacharacters (e.g., `dir; rm -rf /`) could trigger arbitrary command execution if an AI formulates unquoted `mv` or `rm` commands.
* **Impact:** High. Command execution risk during ambiguity resolution.

### 1.4 Operational Rule Tension: BLUF vs. Architectural Options
* **File:** `templates/agents.md.tmpl` (Rule 3 vs. Rule 10)
* **Mechanism:**
  - **Rule 3:** *"Grill by default on architecture. Present 2–3 concrete options with a recommendation; never open-ended 'what do you think?'."*
  - **Rule 10 (BLUF):** *"Lead every substantive reply with the conclusion and the decision needed... Name the option you recommend in the opening sentence. Do not survey options and leave the reader to infer your view... keep it short."*
* **Ambiguity:** Strict adherence to BLUF encourages removing option surveys and process narration, whereas Rule 3 explicitly mandates presenting 2–3 options. Models frequently fail to balance both, either omitting alternative options or writing lengthy surveys that violate BLUF.
* **Impact:** Low-Medium. Instruction ambiguity leading to inconsistent agent responses.

---

## 2. Focus Area 2: Contradictions Between Adapters and Core Instructions

### 2.1 Claude Syntax Leak in `GEMINI.md` (`@agents.md`)
* **File:** `templates/adapters/GEMINI.md` vs. `templates/adapters/CLAUDE.md`
* **Mechanism:** Both `CLAUDE.md` and `GEMINI.md` contain `@agents.md`.
* **Contradiction:** `@file` is a Claude Code CLI directive for prompt file inclusion. Google Antigravity / Gemini CLI does not recognize `@agents.md` as an import directive. When Gemini CLI reads `GEMINI.md`, it sees `@agents.md` as plain text without expanding `agents.md`.
* **Impact:** Critical. Gemini agents operate without reading `agents.md`, completely bypassing project working rules, BLUF, and governance constraints.

### 2.2 Sub-Agent Delegation Breakdown in Non-Claude Environments
* **File:** `templates/agents.md.tmpl` (Rules 9 & 9a)
* **Mechanism:** Rules 9 and 9a dictate delegating research and exploration to sub-agents (`research-delegate`).
* **Contradiction:** Sub-agent definitions in `agents/` (`research-delegate.md`, `audit-*.md`) rely on Claude Code's agent framework. Gemini CLI / Antigravity harness lacks native support for dispatching sub-agents. Demanding that Gemini delegate tasks to sub-agents causes task stalls or hallucinated sub-agent invocations.
* **Impact:** High in multi-harness setups.

### 2.3 Harness-Specific Slash Command Leaks
* **File:** `templates/agents.md.tmpl` (Rule 10 & Commands section)
* **Mechanism:** `agents.md.tmpl` specifies running `/config -> Output style -> BLUF` and lists `/agentstrap:*` slash commands.
* **Contradiction:** `/config` and `/agentstrap:*` slash commands are exclusive to Claude Code. In Google Antigravity, slash commands differ or require `.agents/rules/bluf.md`. Core `agents.md.tmpl` presents Claude-specific syntax as universal instructions.
* **Impact:** Medium. Confusion and command failures on non-Claude harnesses.

---

## 3. Focus Area 3: Infinite Loops, Deadlocks, & Handoff Drift

### 3.1 Narrative Refresh vs. Hook Auto-State Circular Turn Trigger
* **File:** `templates/agents.md.tmpl` (Rule 8) / `skills/handoff/SKILL.md` / `scripts/on-stop.sh`
* **Mechanism:** Rule 8 requires refreshing `HANDOFF.md` narrative before wrapping up. Editing `HANDOFF.md` modifies the working tree (`status --porcelain`). The `Stop` hook (`on-stop.sh`) then fires, modifying the `<!-- AGENTSTRAP:AUTO-STATE -->` section and appending to `DELTA_TRACKING.md`.
* **Loop / Noise:** In automated or continuous execution modes, file changes detected on disk trigger another turn. This turn edits `HANDOFF.md` again, firing `on-stop.sh` continuously. Each turn appends `- Focus: (no recent user message captured)` to `DELTA_TRACKING.md`, flooding the change log with empty turn noise.
* **Impact:** High in automated agent loops. Log bloat and git churn.

### 3.2 Single-Writer File Lock Contention & Push Throttle Accumulation
* **File:** `scripts/continuity-lib.sh` (`as_safe_push`)
* **Mechanism:** `as_safe_push` uses `flock` on `.git/agentstrap-push.lock` with a 30-second timeout.
* **Deadlock / Stale State:** If a prior process terminates abruptly while holding the lock or if `git pull --rebase` encounters merge conflicts on `HANDOFF.md`, `as_safe_push` aborts and defers the push. `DELTA_TRACKING.md` continues to accumulate entries locally. Subsequent sessions receive `tail -n 40 "$AS_DELTA"` via `session-start.sh`, swamping context with unpushed, stale delta logs.
* **Impact:** Medium. Stale context injection across devices.

---

## 4. Focus Area 4: Schema Constraint Bypasses During Execution

### 4.1 Lack of Programmatic Schema Validation in `SKILL.md`
* **File:** `skills/bootstrap/SKILL.md` (Steps 2 & 3)
* **Mechanism:** `SKILL.md` states: *"validate against templates/config.schema.json"* and *"validate against templates/manifest.schema.json"*.
* **Bypass:** `SKILL.md` relies on LLM self-validation rather than executing a validation command (such as `python3 scripts/validate_plugin_models.py`). An AI model can emit malformed JSON (e.g. missing `version`, invalid `stage` enum, or path traversal strings) and advance directly to Step 5 without error detection.
* **Impact:** High. Silently invalid configuration files written to target repositories.

### 4.2 Adopt Mode Link Tracking Discrepancy
* **File:** `skills/bootstrap/SKILL.md` (Step 3) / `templates/manifest.schema.json`
* **Mechanism:** In Adopt Mode, existing components can be linked in place.
* **Loophole:** If `manifest.json` fails to record linked paths under `conformed_to` or `linked`, running `/agentstrap:bootstrap` in `stamped` mode (Step 4) flags linked files as missing drift, attempting to re-scaffold or recreate files that already exist.
* **Impact:** Medium. Repeated false-positive drift reports.

---

## Remediation Recommendations

1. **Sanitize Template Interpolation:** Add regex-based sanitization in bootstrap scripts to strip prompt injection characters and markdown headers from `{{PROJECT_NAME}}` and path inputs.
2. **Fix Adapter Syntax for Antigravity:** Replace `@agents.md` in `GEMINI.md` with explicit rule loading instructions or inline rules compatible with Gemini CLI rules parser.
3. **Guard Against Continuous Turn Loops:** Modify `on-stop.sh` to check whether the last user request was genuine before appending to `DELTA_TRACKING.md`, filtering out harness-triggered empty turns.
4. **Mandate Programmatic Schema Validation in `SKILL.md`:** Add an explicit command line in `SKILL.md` requiring `python3 scripts/validate_plugin_models.py` before finalizing setup in Greenfield and Adopt modes.
5. **Clarify BLUF vs. Architectural Options:** Update Rule 3 and Rule 10 wording to clarify that options must be listed concisely under a BLUF opening recommendation.

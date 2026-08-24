# AgentStrap v2: Gemini (Google Antigravity) Integration Spec

## 1. High-Level Architecture and Objectives

AgentStrap v2 provides a unified project management and continuity methodology for autonomous coding agents. Currently, it supports Claude Code via global skills and hooks. The goal of this spec is to extend native support to **Google Antigravity (AGY) CLI**, allowing users to maintain the same structured workspace, methodology (Vault, BLUF, Continuity), and processes regardless of the agent they use.

### Core Tenets
1. **No Ecosystem Lock-in:** The underlying state (Vault, `HANDOFF.md`, `DELTA_TRACKING.md`, Decisions Log) is identical and perfectly bilingual.
2. **Global Engine, Local State:** To prevent maintainability drift, the AgentStrap engine (skills, agents, hook scripts) will be installed globally in AGY (`~/.gemini/antigravity-cli/plugins/agentstrap/`), identically to Claude.
3. **Flavor Selection:** Projects can be bootstrapped for Claude Code, Antigravity, or *Both*. The methodology remains the same, but the local adapters (`.claude/` vs `.agents/` vs `GEMINI.md`) will vary based on user selection.
4. **Seamless Handoff:** Hooks in Antigravity will map directly to the existing bash scripts to guarantee persistence across sessions and agents.

---

## 2. Low-Level Data Model & Integration Points

### 2.1 Global Plugin Structure (Antigravity Extension)

The AgentStrap repository will be formatted as a valid Antigravity plugin. When users run `agy plugin install https://github.com/mateim4/agentstrap-v2`, the repository contents will be staged globally.

**Required Plugin Manifest (`plugin.json`):**
A `plugin.json` file must be placed at the root of the AgentStrap repository.
```json
{
    "$schema": "https://antigravity.google/schemas/v1/plugin.json",
    "name": "agentstrap-v2",
    "description": "AgentStrap project management, review swarms, and continuity engine."
}
```

**Skills and Agents:**
Antigravity CLI automatically parses markdown files in a plugin's `/skills/` folder into slash commands (e.g., `/agentstrap:bootstrap`). The existing Claude Markdown files in `skills/` and `agents/` are fully compatible with AGY's Markdown-based skill definitions and will be recognized natively.

---

### 2.2 Continuity Hooks Mapping

AgentStrap relies on three bash hooks to maintain continuity. Antigravity uses a `hooks.json` file to intercept execution at specific lifecycle events. We will map AGY's events to the existing Bash scripts.

**Antigravity `hooks.json` Configuration:**
```json
{
  "agentstrap-continuity": {
    "PreInvocation": [
      {
        "type": "command",
        "command": "bash \"./scripts/session-start.sh\"",
        "timeout": 15
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "bash \"./scripts/on-stop.sh\"",
        "timeout": 20
      },
      {
        "type": "command",
        "command": "bash \"./scripts/session-end.sh\"",
        "timeout": 30
      }
    ]
  }
}
```

#### Hook Event Parity:
1. **`PreInvocation` -> `session-start.sh`**:
   - *AGY Behavior:* Fires before the model is called.
   - *Action:* The bash script outputs context (Handoff content) to `stdout`. Antigravity's Hook Input/Output contract expects JSON on `stdout`.
   - **Required Platform Change:** `session-start.sh` must be updated to detect the execution environment. If invoked by AGY, it must wrap the output in AGY's JSON hook format (e.g., `{"injectSteps": [{"ephemeralMessage": "<handoff_content>"}]}`).
2. **`Stop` -> `on-stop.sh` / `session-end.sh`**:
   - *AGY Behavior:* Fires when the execution loop terminates.
   - *Action:* `on-stop.sh` updates the `HANDOFF.md` with the latest changes, and `session-end.sh` executes git pushes.
   - **Required Platform Change:** Similar to `session-start`, these scripts must return a compliant JSON payload (`{"decision": "allow"}` or similar) when triggered by Antigravity, while retaining raw stdout logic for Claude.

---

### 2.3 Bootstrap Skill (`/agentstrap:bootstrap`) Refactor

The `skills/bootstrap/SKILL.md` and underlying python scripts (`detect-project.py`, `sanity-check.py`) must be updated to support the "Flavor Selection" and to generate AGY-specific adapter files.

#### Step 2 Modification: The Flavor Prompt
During the Greenfield or Adopt scaffolding phase, the agent must ask:
> "Which environment are you configuring this project for? [Claude Code / Google Antigravity / Both]"

#### File Generation Rules based on Flavor:
* **Claude Code (Current Behavior):**
  - Generates `.claude/settings.json` (output style BLUF).
  - Generates thin `CLAUDE.md` and `AGENTS.md` adapters.
* **Google Antigravity:**
  - Generates `GEMINI.md` (AGY's global project context adapter) which imports or redirects to `agents.md`.
  - Generates `.agents/settings.json` (or the equivalent AGY visual/output setting file to pin BLUF styling).
* **Both:**
  - Generates all of the above so the project is perfectly bilingual.

#### Output Styling for AGY
Currently, AgentStrap ships `output-styles/bluf.md` for Claude. Antigravity uses `rules/` within the plugin or `.agents/rules/` locally.
- The bootstrap process for AGY will copy or symlink the BLUF rules into `.agents/rules/bluf.md` to ensure the communication style is enforced natively.

---

## 3. Platform & Script Adaptations (Cross-Agent Compatibility)

To ensure the Bash scripts (`session-start.sh`, `on-stop.sh`, `session-end.sh`) remain unified and do not fork into separate files, they must be made **environment-aware**.

### Environment Detection
Both agents provide distinct environment variables during hook execution.
* **Claude:** Exposes `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PROJECT_DIR`.
* **Antigravity:** Exposes hook payloads via `stdin` (JSON containing `workspacePaths`, `conversationId`).

### Bash Script Standard Architecture
The header of each shell script will be modified to parse the environment:

```bash
#!/usr/bin/env bash

# Determine Environment
if [ -n "$CLAUDE_PLUGIN_ROOT" ]; then
    AGENT_ENV="claude"
    START_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
else
    # Antigravity passes context via stdin
    INPUT="$(cat 2>/dev/null)"
    AGENT_ENV="antigravity"
    # Parse workspacePaths from stdin using grep/sed or jq if available
    START_DIR=$(echo "$INPUT" | grep -o '"workspacePaths":\s*\["[^"]*"' | sed 's/.*"//')
    [ -n "$START_DIR" ] || START_DIR="$PWD"
fi

# Execute Core Logic (Identical for both)
# ...

# Output Formatting
if [ "$AGENT_ENV" = "antigravity" ]; then
    # Wrap in JSON for AGY Hook Contract
    echo "{\"injectSteps\": [{\"ephemeralMessage\": \"$FINAL_OUTPUT\"}]}"
else
    # Raw text for Claude
    echo "$FINAL_OUTPUT"
fi
```

---

## 4. Summary of Required Code Changes for Implementation

1. **Root Directory:** Add `plugin.json` to make the repo a valid AGY plugin.
2. **Hooks:** Create or update `hooks.json` to include both Claude and AGY hook schemas, or branch them into `claude-hooks.json` and `agy-hooks.json` (with `plugin.json` pointing to the AGY one).
3. **Scripts:** Refactor `session-start.sh`, `on-stop.sh`, `session-end.sh`, and `continuity-lib.sh` to handle stdin/stdout JSON wrapping for AGY and variable resolution (`workspacePaths` vs `CLAUDE_PROJECT_DIR`).
4. **Bootstrap Skill:** Update `bootstrap/SKILL.md` to ask for the target IDE flavor, and update Python helpers to scaffold `GEMINI.md` and `.agents/` structures alongside `.claude/`.
5. **Templates:** Add `templates/adapters/GEMINI.md` pointing to the canonical `agents.md`.

# Adversarial QA Pass: Plugin Ecosystem Models & Lifecycle Hooks

**Target Repository:** AgentStrap v2
**Audit Focus:** Ecosystem models (`plugin.json`, `hooks/hooks.json`), lifecycle hook interfaces, canonical schema alignment (`https://antigravity.google/schemas/v1/plugin.json`), and security/injection risks.
**Auditor:** Jules QA (Adversarial Engineering Persona)
**Date:** October 2023
**Status:** Complete

---

## Executive Summary

An adversarial quality assurance pass was conducted on AgentStrap v2's plugin manifests, lifecycle hook specifications, and shell integration scripts (`continuity-lib.sh`, `session-start.sh`, `on-stop.sh`, `session-end.sh`).

The assessment identified critical schema compliance issues, lifecycle interface contract violations, path resolution instabilities, and security risks related to path traversal and payload injection.

### Key Risk Summary
- **P0 Critical:** Incompatible hybrid schema structure in `hooks/hooks.json` causing dual-harness schema invalidation and execution failure in strict parsers.
- **P1 High:** Relative path execution (`./scripts/session-start.sh`) in Antigravity hook definitions failing under non-root execution contexts.
- **P1 High:** Vault path traversal risk via uncontrolled `.agentstrap/config.json` parameters leading to unauthorized directory git staging.
- **P2 Medium:** Divergence between root `plugin.json` and `.claude-plugin/plugin.json` (metadata asymmetry: versioning and naming).
- **P2 Medium:** Fragile environment detection fallback in `continuity-lib.sh` defaulting to Antigravity JSON mode when `CLAUDE_PLUGIN_ROOT` is absent.
- **P3 Low:** Permissive license compliance confirmed (MIT License).

---

## 1. Schema Validation & Canonical Standard Alignment

### 1.1 Root `plugin.json` Alignment
The canonical Antigravity standard mandates `$schema: "https://antigravity.google/schemas/v1/plugin.json"`.

**Current implementation at `plugin.json`:**
```json
{
    "$schema": "https://antigravity.google/schemas/v1/plugin.json",
    "name": "agentstrap-v2",
    "description": "AgentStrap project management, review swarms, and continuity engine."
}
```

**Implementation at `.claude-plugin/plugin.json`:**
```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "agentstrap",
  "version": "0.2.1",
  "description": "...",
  "author": { "name": "mateim4" }
}
```

#### Vulnerabilities & Discrepancies:
1. **Name Mismatch (`agentstrap-v2` vs `agentstrap`):** Root manifest defines `"name": "agentstrap-v2"`, whereas `.claude-plugin/plugin.json` defines `"name": "agentstrap"`. Cross-agent tool calls and skill invocations relying on plugin name prefix matching will fail or mismatch commands (`/agentstrap:...` vs `/agentstrap-v2:...`).
2. **Missing Metadata in AGY Manifest:** Root `plugin.json` omits `"version"` and `"author"`. While the AGY draft spec permits minimal manifests, standard validation requires matching version tracking across plugin marketplaces.

### 1.2 `hooks/hooks.json` Hybrid Schema Breakdown

`hooks/hooks.json` currently attempts to support both Claude Code and Google Antigravity in a single file:

```json
{
  "hooks": {
    "SessionStart": [ ... ],
    "Stop": [ ... ],
    "SessionEnd": [ ... ]
  },
  "PreInvocation": [ ... ],
  "Stop": [ ... ]
}
```

#### Structural Flaws:
1. **Claude Code Harness Incompatibility:** Claude Code parser expects top-level `"hooks"` object wrapping hook event names. The presence of top-level `"PreInvocation"` and `"Stop"` keys violates strict Claude plugin schema rules.
2. **Google Antigravity Harness Incompatibility:** Antigravity CLI parser expects lifecycle events at top level or scoped under plugin namespacing (per `reference/gemini-antigravity-spec.md` Section 2.2). Top-level `"hooks"` key breaks AGY schema validation.
3. **Ambiguous Key Collisions:** `"Stop"` exists both under `hooks.Stop` (Claude format) and at top-level `Stop` (AGY format). Parsers parsing this JSON strictly will reject unknown top-level keys.

---

## 2. Lifecycle Hook Interface & Execution Analysis

### 2.1 Path Resolution Instability
In `hooks/hooks.json`:
- **Claude hooks:** Use `bash "${CLAUDE_PLUGIN_ROOT}/scripts/session-start.sh"` (Absolute resolution via plugin environment variable).
- **AGY hooks:** Use `bash "./scripts/session-start.sh"` (Relative path resolution).

#### Failure Scenario:
When Antigravity invokes `PreInvocation` or `Stop` hooks while working inside a user project directory (e.g., `/home/user/my-project`), `bash "./scripts/session-start.sh"` looks for `/home/user/my-project/scripts/session-start.sh`, which does not exist. The hook fails silently or throws command not found errors.

### 2.2 Environment Detection & JSON Contract Compliance

`continuity-lib.sh` implements `as_detect_environment`:
```bash
if [ -n "$CLAUDE_PLUGIN_ROOT" ]; then
  AGENT_ENV="claude"
  START_DIR="${CLAUDE_PROJECT_DIR:-$(as_input_field "$INPUT" cwd)}"
else
  AGENT_ENV="antigravity"
  ...
fi
```

#### Contract Violations:
1. **Claude Harness without `CLAUDE_PLUGIN_ROOT`:** If Claude Code invokes scripts in an environment where `CLAUDE_PLUGIN_ROOT` is unpopulated or sanitized, `as_detect_environment` misidentifies the harness as `antigravity`.
2. **Stdout Contamination:**
   - In `session-start.sh`, AGY mode emits:
     `{"injectSteps": [{"ephemeralMessage": "..."}]}`
   - If `AGENT_ENV` misdetects Claude as Antigravity, raw JSON is printed to Claude's context window instead of human-readable Markdown.
   - If stdout logging or non-JSON messages spill onto `stdout` (e.g., unhandled subshell stderr), AGY JSON parsing fails completely.

---

## 3. Security & Injection Risk Assessment

### 3.1 Unsanitized Stdin / JSON Parsing Vulnerability
In `continuity-lib.sh`, `as_input_field` executes:
```bash
printf '%s' "$1" | python3 -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: d={}
print(d.get(sys.argv[1],"") if isinstance(d,dict) else "")' "$2" 2>/dev/null
```
If `$INPUT` contains binary characters or extremely large payload buffers from standard stdin, python subshell execution can stall or cause subshell memory issues.

### 3.2 Path Traversal & Vault Staging Manipulation
In `continuity-lib.sh`:
- `AS_VAULT` is resolved via `as_cfg "$cfg" continuity.vault_path "$AS_PROJ"`.
- `as_safe_push` executes:
  ```bash
  for f in "${absfiles[@]}"; do [ -e "$f" ] && git -C "$repo" add -- "$f"; done
  ```
- **Adversarial Vector:** A malicious repository or PR can craft `.agentstrap/config.json` with:
  ```json
  {
    "continuity": {
      "vault_path": "/etc",
      "handoff_file": "passwd"
    }
  }
  ```
  `as_safe_push` will attempt `git add -- /etc/passwd` inside the target repository or walk outside the intended vault root if `AS_VAULT` contains relative traversal paths (`../../`).

### 3.3 Shell Input Injection via Environment Variables
- `START_DIR` is extracted using python in `as_detect_environment`. If `START_DIR` contains space or shell escape characters, subshell expansion in `as_find_config "$START_DIR"` is protected by quotes (`"$START_DIR"`), but downstream git commands must handle arbitrary paths safely.

---

## 4. Remediation & Recommendations

1. **Manifest Standard Alignment:**
   - Unify plugin naming across manifests (`agentstrap`).
   - Standardize `plugin.json` schema metadata (include `version` and `author`).

2. **Hook Separation:**
   - Maintain dedicated hook declarations for Claude Code (`.claude-plugin/hooks.json` or `hooks/hooks.json`) and Antigravity (`hooks/agy-hooks.json` or explicit AGY namespace).
   - Use dynamic environment variables (`${CLAUDE_PLUGIN_ROOT}` / `${AGY_PLUGIN_ROOT}` or script relative resolution `$(dirname "$0")`) for hook executable paths.

3. **Vault Path Sanitization:**
   - In `as_resolve_paths`, assert that `AS_VAULT` resides within `$AS_PROJ` or an explicitly allowed boundary to prevent arbitrary path traversal.

4. **License Compliance:**
   - Verified MIT License in root repository. All dependencies and script interpreters (`bash`, `python3`) follow permissive licensing.

---

## Conclusion

AgentStrap v2's continuity architecture provides strong cross-session capabilities, but requires strict decoupling of plugin schema definitions and sanitization of user-configurable paths to guarantee safety and multi-harness compatibility.

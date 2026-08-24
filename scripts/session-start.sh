#!/usr/bin/env bash
# SessionStart hook: inject the handoff + recent delta + working-rules pointer as
# context. Supports both Claude (stdout) and Antigravity (JSON on stdout).
# No-op unless the project is AgentStrap-bootstrapped (.agentstrap/config.json present).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$HERE/continuity-lib.sh"

INPUT="$(cat 2>/dev/null)"
as_detect_environment

if as_find_config "$START_DIR" >/dev/null 2>&1; then
    CFG="$(as_find_config "$START_DIR")"
    as_resolve_paths "$CFG"

    FINAL_OUTPUT=""

    # Build the context string
    FINAL_OUTPUT+="# AgentStrap — session handoff (auto-injected)
_Continuity restored from the docs vault. Honour the project working rules; keep HANDOFF current._

"

    # Surface a previously-deferred sync so it is never silent.
    if git -C "$AS_VAULT" rev-parse '@{u}' >/dev/null 2>&1; then
      AHEAD="$(git -C "$AS_VAULT" rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)"
      case "$AHEAD" in (''|*[!0-9]*) AHEAD=0;; esac
      if [ "$AHEAD" -gt 0 ]; then
        FINAL_OUTPUT+="> ⚠️ The docs vault has $AHEAD local commit(s) not yet pushed — a prior session may not have synced to other devices. Run \`git -C \"$AS_VAULT\" push\` (or open Obsidian so obsidian-git syncs).

"
      fi
    fi

    if [ -f "$AS_HANDOFF" ]; then
      FINAL_OUTPUT+="$(cat "$AS_HANDOFF")"
    else
      FINAL_OUTPUT+="_No HANDOFF.md yet — this looks like the first AgentStrap session for this project._"
    fi

    if [ -f "$AS_DELTA" ]; then
      FINAL_OUTPUT+="

## Recent change log (latest entries)
\`\`\`
$(tail -n 40 "$AS_DELTA")
\`\`\`"
    fi

    # Output Formatting based on Environment
    if [ "$AGENT_ENV" = "antigravity" ]; then
        # Wrap in JSON for AGY Hook Contract (PreInvocation)
        # Use python to safely escape the string into JSON
        python3 -c 'import json,sys; print(json.dumps({"injectSteps": [{"ephemeralMessage": sys.argv[1]}]}))' "$FINAL_OUTPUT"
    else
        # Raw text for Claude
        echo "$FINAL_OUTPUT"
    fi
fi

#!/usr/bin/env bash
# SessionEnd hook: fires when the session terminates. Appends a closing delta entry
# and performs a GUARANTEED safe push.
# In AGY, this can also run on the 'Stop' hook chain.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$HERE/continuity-lib.sh"

INPUT="$(cat 2>/dev/null)"
exec 3>&1
exec 1>/dev/null

as_detect_environment

if ! as_find_config "$START_DIR" >/dev/null 2>&1; then
  if [ "$AGENT_ENV" = "antigravity" ]; then
    echo '{"decision": "allow"}' >&3
  fi
else
    CFG="$(as_find_config "$START_DIR")"
    as_resolve_paths "$CFG"

    SID="$(as_input_field "$INPUT" session_id)"
    if [ "$AGENT_ENV" = "antigravity" ]; then
        SID="$(printf '%s' "$INPUT" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print(d.get("conversationId", ""))' 2>/dev/null)"
    fi

    HOST="$(hostname 2>/dev/null || echo unknown)"
    NOW="$(date '+%F %T')"
    {
      printf '\n### [%s] %s — session end\n' "$NOW" "$HOST"
      printf -- '- Session %s closed; handoff finalized.\n' "${SID:-?}"
    } >>"$AS_DELTA" 2>/dev/null || true

    # Guaranteed delivery regardless of whether obsidian-git is running.
    if [ "$AS_PUSH" != "false" ]; then
      as_safe_push "$AS_VAULT" "$AS_HANDOFF_REL" "$AS_DELTA_REL"
    fi

    if [ "$AGENT_ENV" = "antigravity" ]; then
        echo '{"decision": "allow"}' >&3
    fi
fi

#!/usr/bin/env bash
# SessionEnd hook: fires when the session terminates. Appends a closing delta entry
# and performs a GUARANTEED safe push (force-with-lease handles any race with
# obsidian-git). Cannot block; produces no meaningful stdout.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$HERE/continuity-lib.sh"

INPUT="$(cat 2>/dev/null)"
exec 1>/dev/null

START_DIR="${CLAUDE_PROJECT_DIR:-$(as_input_field "$INPUT" cwd)}"
[ -n "$START_DIR" ] || START_DIR="$PWD"
CFG="$(as_find_config "$START_DIR")" || exit 0
as_resolve_paths "$CFG"

SID="$(as_input_field "$INPUT" session_id)"
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
exit 0

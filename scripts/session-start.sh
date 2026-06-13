#!/usr/bin/env bash
# SessionStart hook: inject the handoff + recent delta + working-rules pointer as
# context (plain stdout reaches Claude for this event). No-op unless the project
# is AgentStrap-bootstrapped (.agentstrap/config.json present).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$HERE/continuity-lib.sh"

INPUT="$(cat 2>/dev/null)"
START_DIR="${CLAUDE_PROJECT_DIR:-$(as_input_field "$INPUT" cwd)}"
[ -n "$START_DIR" ] || START_DIR="$PWD"

CFG="$(as_find_config "$START_DIR")" || exit 0
as_resolve_paths "$CFG"

echo "# AgentStrap — session handoff (auto-injected)"
echo "_Continuity restored from the docs vault. Honour the project working rules; keep HANDOFF current._"
echo
if [ -f "$AS_HANDOFF" ]; then
  cat "$AS_HANDOFF"
else
  echo "_No HANDOFF.md yet — this looks like the first AgentStrap session for this project._"
fi
if [ -f "$AS_DELTA" ]; then
  echo
  echo "## Recent change log (latest entries)"
  echo '```'
  tail -n 40 "$AS_DELTA"
  echo '```'
fi
exit 0

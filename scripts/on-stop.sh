#!/usr/bin/env bash
# Stop hook: fires when Claude finishes responding. Refreshes the auto-state block
# of HANDOFF.md and appends a DELTA_TRACKING entry every turn. Pushes only when no
# external committer (obsidian-git) is running. MUST NOT write to stdout (a Stop
# hook's stdout/JSON can continue or block the turn) — all output is suppressed.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$HERE/continuity-lib.sh"

INPUT="$(cat 2>/dev/null)"
exec 1>/dev/null   # hard guarantee: nothing reaches the harness on stdout

START_DIR="${CLAUDE_PROJECT_DIR:-$(as_input_field "$INPUT" cwd)}"
[ -n "$START_DIR" ] || START_DIR="$PWD"
CFG="$(as_find_config "$START_DIR")" || exit 0
as_resolve_paths "$CFG"

mkdir -p "$(dirname "$AS_HANDOFF")" "$(dirname "$AS_DELTA")" 2>/dev/null || true

TRANSCRIPT="$(as_input_field "$INPUT" transcript_path)"
HOST="$(hostname 2>/dev/null || echo unknown)"
NOW="$(date '+%F %T')"
BRANCH="$(git -C "$AS_PROJ" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '(no git)')"
CHANGED="$(git -C "$AS_PROJ" status --porcelain 2>/dev/null | grep -c . )"

LAST_USER="$(python3 - "$TRANSCRIPT" <<'PY' 2>/dev/null
import json,sys
p=sys.argv[1] if len(sys.argv)>1 else ""
msg=""
try:
    for line in open(p):
        try: o=json.loads(line)
        except Exception: continue
        m=o.get("message",{}) if isinstance(o,dict) else {}
        role=o.get("type") or (m.get("role") if isinstance(m,dict) else None)
        if role=="user":
            c=m.get("content") if isinstance(m,dict) else None
            if isinstance(c,list):
                c=" ".join(x.get("text","") for x in c if isinstance(x,dict))
            if isinstance(c,str) and c.strip() and not c.strip().startswith("<"):
                msg=c.strip().replace("\n"," ")
except Exception: pass
print(msg[:280])
PY
)"

# Append a delta entry for this turn.
{
  printf '\n### [%s] %s — %s\n' "$NOW" "$HOST" "$BRANCH"
  printf -- '- Focus: %s\n' "${LAST_USER:-(no recent user message captured)}"
  printf -- '- Working tree: %s uncommitted file(s)\n' "$CHANGED"
} >>"$AS_DELTA" 2>/dev/null || true

# Rewrite the hook-owned auto-state block of HANDOFF, preserving Claude's narrative.
python3 - "$AS_HANDOFF" "$NOW" "$HOST" "$BRANCH" "$CHANGED" "$AS_DELTA_REL" "${LAST_USER:-(none captured)}" <<'PY' 2>/dev/null || true
import sys
path,now,host,branch,changed,drel,lastuser=sys.argv[1:8]
START="<!-- AGENTSTRAP:AUTO-STATE -->"
END="<!-- /AGENTSTRAP:AUTO-STATE -->"
auto=(f"{START}\n"
      "## Auto state (written automatically every turn — do not hand-edit)\n"
      f"- Updated: {now}\n- Machine: {host}\n- Branch: {branch}\n"
      f"- Uncommitted files: {changed}\n- Last request: {lastuser}\n"
      f"- Change log: see {drel}\n{END}")
try: txt=open(path).read()
except FileNotFoundError: txt=None
if txt is None or START not in txt:
    narrative=("# Handoff — where we left off\n\n"
        "_Cross-device session handoff. The narrative below is maintained by Claude "
        "(via `/agentstrap:handoff` or when wrapping up); the auto-state block is written "
        "by hooks every turn._\n\n"
        "## What was done\n- (pending first narrative update)\n\n"
        "## What's next\n- (pending)\n\n"
        "## Blockers\n- (none noted)\n\n"
        "## Files to review first\n- (none noted)\n\n")
    txt=narrative+auto+"\n"
else:
    pre=txt.split(START)[0]
    post=txt.split(END,1)[1] if END in txt else "\n"
    txt=pre+auto+post
open(path,"w").write(txt)
PY

# Push only if obsidian-git is NOT the active committer (single-writer rule).
if [ "$AS_PUSH" != "false" ]; then
  if as_obsidian_running && [ "$AS_OBS" != "false" ]; then
    as_log "stop: obsidian running — leaving push to obsidian-git"
  else
    as_safe_push "$AS_VAULT" "$AS_HANDOFF_REL" "$AS_DELTA_REL"
  fi
fi
exit 0

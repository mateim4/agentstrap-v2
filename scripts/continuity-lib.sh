#!/usr/bin/env bash
# continuity-lib.sh — shared helpers for AgentStrap continuity hooks.
# Sourced by session-start.sh, on-stop.sh, session-end.sh.
#
# Design rules:
#  - NEVER fail the hook: every caller exits 0 regardless of git/network state.
#  - Single-writer-per-repo: only push when no external auto-committer (obsidian-git)
#    is running; the SessionEnd guarantee uses --force-with-lease to coexist safely.
#  - State lives under the PROJECT, never under ${CLAUDE_PLUGIN_ROOT} (ephemeral).

as_logfile() {
  local d="${AS_LOG_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}/.agentstrap}"
  mkdir -p "$d" 2>/dev/null || true
  printf '%s/continuity.log' "$d"
}

as_log() { printf '%s %s\n' "$(date '+%F %T')" "$*" >>"$(as_logfile)" 2>/dev/null || true; }

as_have() { command -v "$1" >/dev/null 2>&1; }

# Read the JSON the harness passes on stdin (already captured by caller into $1).
# Extract a top-level field. Usage: as_input_field "$INPUT" transcript_path
as_input_field() {
  printf '%s' "$1" | python3 -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: d={}
print(d.get(sys.argv[1],"") if isinstance(d,dict) else "")' "$2" 2>/dev/null
}

# Determine the execution environment (Claude vs Antigravity) and set base paths
as_detect_environment() {
  if [ -n "$CLAUDE_PLUGIN_ROOT" ]; then
    AGENT_ENV="claude"
    START_DIR="${CLAUDE_PROJECT_DIR:-$(as_input_field "$INPUT" cwd)}"
    [ -n "$START_DIR" ] || START_DIR="$PWD"
  else
    AGENT_ENV="antigravity"
    # Parse workspacePaths from stdin JSON
    START_DIR=$(printf '%s' "$INPUT" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); wp=d.get("workspacePaths", []); print(wp[0] if wp else "")' 2>/dev/null)
    [ -n "$START_DIR" ] || START_DIR="$PWD"
  fi
}

# Walk up from a start dir to find .agentstrap/config.json. Prints its path.
as_find_config() {
  local d="${1:-${START_DIR}}"
  d="$(cd "$d" 2>/dev/null && pwd)" || return 1
  while [ -n "$d" ] && [ "$d" != "/" ]; do
    [ -f "$d/.agentstrap/config.json" ] && { printf '%s\n' "$d/.agentstrap/config.json"; return 0; }
    d="$(dirname "$d")"
  done
  return 1
}

# Read a dotted key from a config json. Usage: as_cfg <file> <dotkey> <default>
as_cfg() {
  python3 - "$1" "$2" "$3" <<'PY' 2>/dev/null || printf '%s' "$3"
import json,sys
cf,key,default=sys.argv[1],sys.argv[2],sys.argv[3]
try: d=json.load(open(cf, encoding='utf-8', errors='replace'))
except Exception: print(default); sys.exit(0)
cur=d
for part in key.split('.'):
    if isinstance(cur,dict) and part in cur: cur=cur[part]
    else: print(default); sys.exit(0)
if isinstance(cur,bool): print('true' if cur else 'false')
elif cur is None: print(default)
else: print(cur)
PY
}

# True (0) if an Obsidian process is running => obsidian-git is the active committer.
as_obsidian_running() {
  if as_have pgrep; then pgrep -fi 'obsidian' >/dev/null 2>&1 && return 0; return 1; fi
  ps -e 2>/dev/null | grep -i '[o]bsidian' >/dev/null 2>&1
}

as_is_git_repo() { git -C "$1" rev-parse --git-dir >/dev/null 2>&1; }

# Throttle: return 0 at most once per <interval> seconds (timestamp under a state dir).
# Usage: as_should_push <state_dir> <interval_seconds>
as_should_push() {
  local stamp="$1/.last_push" interval="${2:-90}" now last
  now="$(date +%s 2>/dev/null || echo 0)"
  last="$(cat "$stamp" 2>/dev/null || echo 0)"
  case "$last" in (*[!0-9]*|"") last=0;; esac
  if [ $(( now - last )) -ge "$interval" ]; then printf '%s' "$now" >"$stamp" 2>/dev/null || true; return 0; fi
  return 1
}

# Surgically commit+push specific files, coexisting with an external auto-committer.
# Files are given RELATIVE TO <vault>; we resolve the actual git top-level and use
# ABSOLUTE paths, so it works even when the vault is a subdirectory of the repo.
# Serialized per-device by flock; on a true two-device conflict it DEFERS (never
# force-overwrites). Usage: as_safe_push <vault> <relfile> [relfile...]
as_safe_push() {
  local vault="$1"; shift
  as_is_git_repo "$vault" || { as_log "safe_push: $vault is not a git repo, skipping"; return 0; }
  local repo; repo="$(git -C "$vault" rev-parse --show-toplevel 2>/dev/null)" || { as_log "safe_push: no toplevel for $vault"; return 0; }
  local absfiles=() f
  for f in "$@"; do absfiles+=("$vault/$f"); done
  (
    if as_have flock; then exec 9>"$repo/.git/agentstrap-push.lock"; flock -w 30 9 || { as_log "safe_push: lock timeout"; exit 0; }; fi
    for f in "${absfiles[@]}"; do [ -e "$f" ] && git -C "$repo" add -- "$f" 2>/dev/null; done
    if git -C "$repo" diff --cached --quiet 2>/dev/null; then
      as_log "safe_push: nothing staged in $repo"
    else
      git -C "$repo" commit -q -m "agentstrap: session handoff $(date '+%F %T')" -- "${absfiles[@]}" >/dev/null 2>&1 || true
    fi
    if git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
      # Reconcile with the remote and push WITHOUT EVER force-overwriting another
      # device's work. Plain (fast-forward) push only. A true same-file two-device
      # collision is deferred: keep our commit local, leave the remote intact, and
      # let the next pull reconcile it. No data is ever destroyed on either side.
      local n=0 pushed=0
      while [ "$n" -lt 3 ]; do
        if git -C "$repo" pull --rebase --autostash -q >/dev/null 2>&1; then
          if git -C "$repo" push -q >/dev/null 2>&1; then as_log "safe_push: pushed $repo"; pushed=1; break; fi
          # Non-fast-forward from a concurrent NON-conflicting push: re-pull and retry.
          n=$((n+1)); as_log "safe_push: non-ff, retry $n for $repo"
        else
          # Genuine conflict on the handoff/delta files: abort, defer (no clobber).
          git -C "$repo" rebase --abort >/dev/null 2>&1 || true
          as_log "safe_push: diverged on $repo — commit kept local, remote untouched, will reconcile on next pull"
          break
        fi
      done
      [ "$pushed" = 0 ] && as_log "safe_push: not pushed this turn for $repo (deferred)"
    else
      as_log "safe_push: no upstream for $repo; committed locally only"
    fi
  )
  return 0
}

# Resolve the standard continuity paths from a config file. Sets:
#   AS_PROJ AS_VAULT AS_HANDOFF_REL AS_DELTA_REL AS_HANDOFF AS_DELTA AS_PUSH AS_OBS
as_resolve_paths() {
  local cfg="$1"
  AS_PROJ="$(cd "$(dirname "$(dirname "$cfg")")" && pwd)"
  AS_VAULT="$(as_cfg "$cfg" continuity.vault_path "$AS_PROJ")"
  [ -d "$AS_VAULT" ] || AS_VAULT="$AS_PROJ"
  AS_HANDOFF_REL="$(as_cfg "$cfg" continuity.handoff_file HANDOFF.md)"
  AS_DELTA_REL="$(as_cfg "$cfg" continuity.delta_file DELTA_TRACKING.md)"
  AS_PUSH="$(as_cfg "$cfg" continuity.push true)"
  AS_OBS="$(as_cfg "$cfg" continuity.obsidian_enabled true)"
  AS_HANDOFF="$AS_VAULT/$AS_HANDOFF_REL"
  AS_DELTA="$AS_VAULT/$AS_DELTA_REL"
}

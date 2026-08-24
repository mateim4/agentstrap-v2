#!/usr/bin/env python3
"""normalize.py — migrate detected governance files into canonical AgentStrap structure.

Creates the canonical 00–90 domain structure, moves detected governance files/directories
to their canonical locations, and optionally archives old empty directories.

Phases:
  1. Plan (default): reads detect-project.py output, generates a migration plan as JSON.
  2. Execute (--execute): creates the canonical structure and performs the moves via git mv
     (falling back to os.rename if not a git repo).
  3. Archive (--archive, implies --execute): also moves emptied directories into
     .agentstrap/archive/<timestamp>/ and writes a MIGRATION.md manifest.

Archive requires the explicit --archive flag.  The bootstrap skill (SKILL.md) handles
user sign-off before passing this flag.

Usage:
  normalize.py [project_dir]              # plan only (dry run)
  normalize.py [project_dir] --execute    # create structure + move files (no archive)
  normalize.py [project_dir] --archive    # execute + archive emptied old dirs

Exit codes:
  0 = success (or nothing to do)
  1 = error
"""
import json, os, re, shutil, subprocess, sys
from datetime import datetime, timezone

here = os.path.dirname(os.path.abspath(__file__))

# ── Argument parsing (intentionally simple — no argparse dependency) ──────────
args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = {a for a in sys.argv[1:] if a.startswith("--")}
root = os.path.abspath(args[0] if args else os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
do_execute = "--execute" in flags or "--archive" in flags
do_archive = "--archive" in flags

# ── Canonical structure ───────────────────────────────────────────────────────
# Maps component keys → (canonical parent relative to root, rename_to or None to keep basename)
CANONICAL_PARENTS = {
    "decisions_log":  "00 - Foundations",
    "open_questions": "00 - Foundations",
    "working_rules":  "00 - Foundations",
    "credentials":    "00 - Foundations",
    "handoff":        ".",               # project root
    "work_log":       ".",               # project root
    "delta":          ".",               # project root
}

# The numbered domain directories to create (even if they end up empty).
DOMAIN_DIRS = [
    "00 - Foundations",
    "10 - Product",
    "20 - Design",
    "30 - Engineering",
    "40 - Operations",
    "50 - Business",
    "90 - Reference",
]


def _detect():
    """Run detect-project.py and return its JSON output."""
    result = subprocess.run(
        [sys.executable, os.path.join(here, "detect-project.py"), root],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: detect-project.py failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout or "{}")


def _is_git():
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], cwd=root,
                        capture_output=True, text=True, timeout=5, check=True)
        return True
    except Exception:
        return False


def _move(src, dst, use_git):
    """Move src → dst, creating parent dirs as needed.  Prefers git mv."""
    dst_dir = os.path.dirname(dst)
    if dst_dir:
        os.makedirs(dst_dir, exist_ok=True)
    if use_git:
        result = subprocess.run(["git", "mv", src, dst], cwd=root,
                                capture_output=True, text=True)
        if result.returncode != 0:
            # fallback
            shutil.move(src, dst)
    else:
        shutil.move(src, dst)


def _is_empty_dir(path):
    """True if path is a directory containing no files (recursively)."""
    if not os.path.isdir(path):
        return False
    for _, _, files in os.walk(path):
        if files:
            return False
    return True


def build_plan(facts):
    """Build a migration plan from detect-project.py output.

    Returns a dict:
      {
        "moves":     [{"component": ..., "from": ..., "to": ..., "type": "file"|"directory"}, ...],
        "creates":   ["00 - Foundations", ...],  # dirs to create
        "conflicts": [{"component": ..., "from": ..., "to": ..., "reason": ...}, ...],
        "skipped":   [{"component": ..., "reason": ...}, ...],  # already canonical
      }
    """
    locations = facts.get("existing_locations", {})
    plan = {"moves": [], "creates": [], "conflicts": [], "skipped": []}

    # Determine which domain dirs need creating.
    for d in DOMAIN_DIRS:
        full = os.path.join(root, d)
        if not os.path.exists(full):
            plan["creates"].append(d)

    # For each detected component, decide if it needs moving.
    for comp_key, canonical_parent in CANONICAL_PARENTS.items():
        loc_list = locations.get(comp_key)
        if not loc_list:
            continue  # not detected — nothing to move
            
        if len(loc_list) > 1:
            print(f"ERROR: Ambiguity exists for {comp_key}. Resolve before normalizing.", file=sys.stderr)
            sys.exit(1)
            
        loc = loc_list[0]
        src_path = loc["path"]          # relative to root
        src_type = loc["type"]          # "file" or "directory"
        src_basename = os.path.basename(src_path)

        # Where it should live.
        if canonical_parent == ".":
            canonical_path = src_basename
        else:
            canonical_path = os.path.join(canonical_parent, src_basename)

        # Normalise for comparison.
        src_norm = os.path.normpath(src_path)
        dst_norm = os.path.normpath(canonical_path)

        if src_norm == dst_norm:
            plan["skipped"].append({
                "component": comp_key,
                "reason": f"already at canonical location: {src_path}",
            })
            continue

        # Check for conflicts at destination.
        dst_full = os.path.join(root, canonical_path)
        if os.path.exists(dst_full):
            plan["conflicts"].append({
                "component": comp_key,
                "from": src_path,
                "to": canonical_path,
                "reason": f"destination already exists: {canonical_path}",
            })
            continue

        plan["moves"].append({
            "component": comp_key,
            "from": src_path,
            "to": canonical_path,
            "type": src_type,
        })

    return plan


def execute_plan(plan, use_git):
    """Execute a migration plan.  Returns list of emptied parent directories."""
    # Create domain dirs.
    for d in plan["creates"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    # Move files / directories.
    emptied_parents = set()
    for move in plan["moves"]:
        src = os.path.join(root, move["from"])
        dst = os.path.join(root, move["to"])
        _move(src, dst, use_git)
        # Track parent dirs that might now be empty.
        parent = os.path.dirname(src)
        if parent and parent != root:
            emptied_parents.add(parent)

    # Walk up from emptied parents to find all empty ancestors (up to root).
    all_empty = set()
    for p in emptied_parents:
        current = p
        while current != root and os.path.isdir(current) and _is_empty_dir(current):
            all_empty.add(current)
            current = os.path.dirname(current)

    return sorted(all_empty)


def archive_dirs(empty_dirs, plan):
    """Move emptied directories into .agentstrap/archive/<timestamp>/ and write MIGRATION.md."""
    if not empty_dirs:
        return None

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    archive_root = os.path.join(root, ".agentstrap", "archive", ts)
    os.makedirs(archive_root, exist_ok=True)

    archived = []
    for d in empty_dirs:
        rel = os.path.relpath(d, root)
        dst = os.path.join(archive_root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(d, dst)
        archived.append(rel)

    # Write migration manifest.
    manifest_path = os.path.join(archive_root, "MIGRATION.md")
    lines = [
        f"# AgentStrap structure normalisation — {ts}",
        "",
        "## Files moved",
        "",
        "| Component | From | To |",
        "| --- | --- | --- |",
    ]
    for move in plan["moves"]:
        lines.append(f"| {move['component']} | `{move['from']}` | `{move['to']}` |")
    lines.append("")
    lines.append("## Archived empty directories")
    lines.append("")
    for a in archived:
        lines.append(f"- `{a}` → `{os.path.relpath(os.path.join(archive_root, a), root)}`")
    if plan["conflicts"]:
        lines.append("")
        lines.append("## Conflicts (not moved)")
        lines.append("")
        for c in plan["conflicts"]:
            lines.append(f"- `{c['from']}` → `{c['to']}`: {c['reason']}")
    lines.append("")
    with open(manifest_path, "w") as fh:
        fh.write("\n".join(lines))

    return os.path.relpath(archive_root, root)


# ── Main ──────────────────────────────────────────────────────────────────────
facts = _detect()
plan = build_plan(facts)

if not do_execute:
    # Dry-run: emit plan as JSON + human-readable summary.
    summary_lines = ["# AgentStrap — Structure Normalisation Plan", ""]

    if plan["creates"]:
        summary_lines.append("## Directories to create")
        for d in plan["creates"]:
            summary_lines.append(f"  + `{d}/`")
        summary_lines.append("")

    if plan["moves"]:
        summary_lines.append("## Files/directories to move")
        summary_lines.append("")
        summary_lines.append("| Component | From | To | Type |")
        summary_lines.append("| --- | --- | --- | --- |")
        for m in plan["moves"]:
            summary_lines.append(f"| {m['component']} | `{m['from']}` | `{m['to']}` | {m['type']} |")
        summary_lines.append("")

    if plan["conflicts"]:
        summary_lines.append("## ⚠ Conflicts (will be skipped)")
        for c in plan["conflicts"]:
            summary_lines.append(f"  ! `{c['from']}` → `{c['to']}`: {c['reason']}")
        summary_lines.append("")

    if plan["skipped"]:
        summary_lines.append("## Already canonical (no action)")
        for s in plan["skipped"]:
            summary_lines.append(f"  ✓ {s['component']}: {s['reason']}")
        summary_lines.append("")

    if not plan["moves"] and not plan["creates"]:
        summary_lines.append("**Nothing to do** — all detected components are already in canonical locations.")

    print("\n".join(summary_lines))
    print("---JSON---")
    print(json.dumps(plan, indent=2))
else:
    use_git = _is_git()
    empty_dirs = execute_plan(plan, use_git)

    result = {
        "executed": True,
        "dirs_created": plan["creates"],
        "files_moved": plan["moves"],
        "conflicts": plan["conflicts"],
        "skipped": plan["skipped"],
        "emptied_dirs": [os.path.relpath(d, root) for d in empty_dirs],
    }

    if do_archive and empty_dirs:
        archive_path = archive_dirs(empty_dirs, plan)
        result["archive_path"] = archive_path
        print(f"Archived {len(empty_dirs)} emptied director{'y' if len(empty_dirs)==1 else 'ies'} to `{archive_path}/`")
    elif empty_dirs:
        print(f"Note: {len(empty_dirs)} director{'y is' if len(empty_dirs)==1 else 'ies are'} now empty after moves.")
        print("Run again with --archive to archive them (requires user sign-off).")

    print("---JSON---")
    print(json.dumps(result, indent=2))

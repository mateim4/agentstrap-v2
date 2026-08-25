#!/usr/bin/env python3
"""detect-project.py — emit JSON facts about a target project for /agentstrap:bootstrap.

Read-only. Detects VCS, language/build files, an Obsidian vault, numbered
documentation domains, and any pre-existing AgentStrap / methodology artifacts so
bootstrap can run idempotently and conform to existing conventions.

Detection runs in two passes:
  1. Filename-based matching (the original WANT patterns — exact file names).
  2. Structural probing — detects *directories* that serve the same governance
     function (e.g. `docs/decisions/ADR-*.md` instead of a single `Decisions Log.md`).
     Structural results only fill gaps; they never override a filename match.

Usage: detect-project.py [project_dir]   (defaults to $CLAUDE_PROJECT_DIR or cwd)
"""
import json, os, re, subprocess, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).replace("\\", "/")


def run(*args):
    try:
        return subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def exists(*parts):
    return os.path.exists(os.path.join(root, *parts))


# VCS
is_git = bool(run("git", "rev-parse", "--git-dir"))
has_remote = bool(run("git", "remote")) if is_git else False

# Languages / build files
build_map = {
    "package.json": "node", "pnpm-lock.yaml": "node", "Cargo.toml": "rust",
    "pyproject.toml": "python", "requirements.txt": "python", "go.mod": "go",
    "pom.xml": "java", "build.gradle": "java", "Gemfile": "ruby", "composer.json": "php",
}
build_files, languages = [], set()
for f, lang in build_map.items():
    if exists(f):
        build_files.append(f)
        languages.add(lang)

# Obsidian + numbered documentation domains (conform to existing names, don't impose)
# Now also searches inside common doc directories, not just the root.
obsidian = exists(".obsidian")
numbered = []
DOC_ROOTS = [".", "docs", "doc", "documentation"]
try:
    for doc_root in DOC_ROOTS:
        search_dir = os.path.join(root, doc_root) if doc_root != "." else root
        if not os.path.isdir(search_dir):
            continue
        for name in sorted(os.listdir(search_dir)):
            full = os.path.join(search_dir, name)
            if os.path.isdir(full) and re.match(r"^\d{2}[ _-]", name):
                rel = os.path.relpath(full, root).replace("\\", "/")
                if rel not in numbered:
                    numbered.append(rel)
except OSError:
    pass

# ── Pass 1: Filename-based artifact matching (case-insensitive, depth ≤ 3) ──
WANT = {
    "handoff": re.compile(r"^handoff\.md$", re.I),
    "delta": re.compile(r"^delta[_-]?tracking\.md$", re.I),
    "decisions_log": re.compile(r"^decisions?[ _-]?log\.md$", re.I),
    "open_questions": re.compile(r"^open[ _-]?questions?\.md$", re.I),
    "working_rules": re.compile(r"^working[ _-]?rules?\.md$", re.I),
    "agents_md": re.compile(r"^agents\.md$", re.I),
    "work_log": re.compile(r"^(work[ _-]?log|devlog|dev[ _-]?log)\.md$", re.I),
    "credentials": re.compile(r"^credentials([ _-]and[ _-]secrets)?\.md$", re.I),
}
found = {k: [] for k in WANT}
SKIP = {".git", "node_modules", "target", "dist", "build", ".obsidian", "__pycache__"}
for dirpath, dirnames, filenames in os.walk(root):
    depth = os.path.relpath(dirpath, root).count(os.sep)
    if depth > 3:
        dirnames[:] = []
        continue
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in filenames:
        for key, pat in WANT.items():
            if pat.match(fn):
                found[key].append(os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/"))

# ── Pass 2: Structural detection — directories that serve a governance function ──
# Each entry: component key → {dir_names: regex[], file_pat: regex, min_files: int}
STRUCTURAL = {
    "decisions_log": {
        "dir_names": [re.compile(r"^(decisions?|adrs?|architecture([_-]decisions?)?|arch[_-]decisions?)$", re.I)],
        "file_pat": re.compile(r"^(ADR[-_]\d+|adr[-_]\d+|\d+[-_]).*\.md$", re.I),
        "min_files": 1,
    },
    "handoff": {
        "dir_names": [re.compile(r"^handoffs?$", re.I)],
        "file_pat": re.compile(r"\.md$", re.I),
        "min_files": 1,
    },
    "open_questions": {
        "dir_names": [re.compile(r"^(open[_-]?questions?|questions?)$", re.I)],
        "file_pat": re.compile(r"\.md$", re.I),
        "min_files": 1,
    },
    "work_log": {
        "dir_names": [re.compile(r"^(work[_-]?logs?|devlogs?|dev[_-]?logs?)$", re.I)],
        "file_pat": re.compile(r"\.md$", re.I),
        "min_files": 1,
    },
}

# existing_locations tracks richer detail about where each component was found.
# Format: {"component_key": [{"path": "...", "type": "file"|"directory", "count": N}, ...]}
existing_locations = {}

# Record Pass-1 file hits into existing_locations.
for key, paths in found.items():
    for path in paths:
        existing_locations.setdefault(key, []).append({"path": path, "type": "file", "count": 1})

# Structural walk — search depth ≤ 3 for matching directories.
for dirpath, dirnames, filenames in os.walk(root):
    depth = os.path.relpath(dirpath, root).count(os.sep)
    if depth > 3:
        dirnames[:] = []
        continue
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    dirname = os.path.basename(dirpath)
    for comp_key, spec in STRUCTURAL.items():
        if not any(pat.match(dirname) for pat in spec["dir_names"]):
            continue
        matching_files = [fn for fn in filenames if spec["file_pat"].search(fn)]
        if len(matching_files) >= spec["min_files"]:
            rel = os.path.relpath(dirpath, root).replace("\\", "/")
            existing_locations.setdefault(comp_key, []).append({
                "path": rel,
                "type": "directory",
                "count": len(matching_files),
            })


# ── Output style detection (Claude + Antigravity) ──
def output_style():
    """The project's pinned output style — checks Claude (.claude/settings.json)
    and Antigravity (.agents/rules/bluf.md) locations."""
    # Claude Code
    try:
        with open(os.path.join(root, ".claude", "settings.json"), encoding="utf-8") as fh:
            style = json.load(fh).get("outputStyle") or ""
            if style:
                return style
    except Exception:
        pass
    # Antigravity — the BLUF rule file
    bluf_path = os.path.join(root, ".agents", "rules", "bluf.md")
    if os.path.isfile(bluf_path):
        return "BLUF"
    return ""


# ── Assemble markers ──
markers = {
    "manifest": exists(".agentstrap", "manifest.json"),
    "config": exists(".agentstrap", "config.json"),
    "claude_md": exists("CLAUDE.md") or exists(".claude", "CLAUDE.md"),
    "gemini_md": exists("GEMINI.md") or exists(".agents", "GEMINI.md"),
    "agents_md": bool(existing_locations.get("agents_md")),
    "handoff": bool(existing_locations.get("handoff")),
    "delta": bool(existing_locations.get("delta")),
    "decisions_log": bool(existing_locations.get("decisions_log")),
    "open_questions": bool(existing_locations.get("open_questions")),
    "working_rules": bool(existing_locations.get("working_rules")),
    "work_log": bool(existing_locations.get("work_log")),
    "credentials": bool(existing_locations.get("credentials")),
    "output_style": output_style(),
}

has_methodology = bool(numbered or obsidian or markers["decisions_log"] or markers["working_rules"]
                       or markers["open_questions"] or markers["agents_md"])
stage_guess = "code" if (languages and (exists("src") or exists("crates") or exists("lib"))) else "planning"

print(json.dumps({
    "project_dir": root,
    "is_git": is_git,
    "has_remote": has_remote,
    "languages": sorted(languages),
    "build_files": build_files,
    "obsidian": obsidian,
    "numbered_domains": numbered,
    "markers": markers,
    "existing_locations": existing_locations,
    "has_methodology": has_methodology,
    "stage_guess": stage_guess,
}, indent=2))

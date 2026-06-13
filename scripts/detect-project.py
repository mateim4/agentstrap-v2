#!/usr/bin/env python3
"""detect-project.py — emit JSON facts about a target project for /agentstrap:bootstrap.

Read-only. Detects VCS, language/build files, an Obsidian vault, numbered
documentation domains, and any pre-existing AgentStrap / methodology artifacts so
bootstrap can run idempotently and conform to existing conventions.

Usage: detect-project.py [project_dir]   (defaults to $CLAUDE_PROJECT_DIR or cwd)
"""
import json, os, re, subprocess, sys

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


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
obsidian = exists(".obsidian")
numbered = []
try:
    for name in sorted(os.listdir(root)):
        if os.path.isdir(os.path.join(root, name)) and re.match(r"^\d{2}[ _-]", name):
            numbered.append(name)
except OSError:
    pass

# Locate known artifacts (case-insensitive) up to a shallow depth.
WANT = {
    "handoff": re.compile(r"^handoff\.md$", re.I),
    "delta": re.compile(r"^delta[_-]?tracking\.md$", re.I),
    "decisions_log": re.compile(r"^decisions?[ _-]?log\.md$", re.I),
    "open_questions": re.compile(r"^open[ _-]?questions?\.md$", re.I),
    "working_rules": re.compile(r"^working[ _-]?rules?\.md$", re.I),
    "agents_md": re.compile(r"^agents\.md$", re.I),
}
found = {k: "" for k in WANT}
SKIP = {".git", "node_modules", "target", "dist", "build", ".obsidian", "__pycache__"}
for dirpath, dirnames, filenames in os.walk(root):
    depth = os.path.relpath(dirpath, root).count(os.sep)
    if depth > 3:
        dirnames[:] = []
        continue
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in filenames:
        for key, pat in WANT.items():
            if not found[key] and pat.match(fn):
                found[key] = os.path.relpath(os.path.join(dirpath, fn), root)

markers = {
    "manifest": exists(".agentstrap", "manifest.json"),
    "config": exists(".agentstrap", "config.json"),
    "claude_md": exists("CLAUDE.md") or exists(".claude", "CLAUDE.md"),
    "agents_md": bool(found["agents_md"]),
    "handoff": found["handoff"],
    "delta": found["delta"],
    "decisions_log": found["decisions_log"],
    "open_questions": found["open_questions"],
    "working_rules": found["working_rules"],
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
    "has_methodology": has_methodology,
    "stage_guess": stage_guess,
}, indent=2))

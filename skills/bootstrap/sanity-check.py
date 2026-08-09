#!/usr/bin/env python3
"""sanity-check.py — classify an AgentStrap target and report gaps, non-destructively.

Runs detect-project.py, decides the bootstrap MODE, and prints a markdown gap report
plus a machine-readable JSON verdict (after a line containing only '---JSON---').

  mode = greenfield  : no methodology docs and no AgentStrap marker -> full scaffold
  mode = adopt       : methodology docs exist but no AgentStrap manifest -> add only what's missing
  mode = stamped     : .agentstrap/manifest.json exists -> verify/upgrade

This NEVER writes to the project. It only reports. The bootstrap skill decides what
to add, with confirmation, conforming to the project's existing naming.

Usage: sanity-check.py [project_dir]
"""
import json, os, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())

facts = json.loads(subprocess.run([sys.executable, os.path.join(here, "detect-project.py"), root],
                                  capture_output=True, text=True).stdout or "{}")
m = facts.get("markers", {})

if m.get("manifest"):
    mode = "stamped"
elif facts.get("has_methodology"):
    mode = "adopt"
else:
    mode = "greenfield"

# Expected components: (key, label, present?)
components = [
    ("agent_instructions", "Always-loaded agent guidance (agents.md / CLAUDE.md)", m.get("agents_md") or m.get("claude_md")),
    ("working_rules", "PM-first working rules", bool(m.get("working_rules")) or m.get("agents_md") or m.get("claude_md")),
    ("decisions_log", "Decisions Log (append-only ADRs)", bool(m.get("decisions_log"))),
    ("open_questions", "Open Questions register", bool(m.get("open_questions"))),
    ("numbered_domains", "00–90 numbered documentation domains", bool(facts.get("numbered_domains"))),
    ("handoff", "HANDOFF.md continuity file (~2-week window)", bool(m.get("handoff"))),
    ("work_log", "Work Log (permanent session history the handoff spills into)", bool(m.get("work_log"))),
    ("credentials", "Credentials and secrets (the one place credentials live)", bool(m.get("credentials"))),
    ("delta", "DELTA_TRACKING.md change log", bool(m.get("delta"))),
    ("config", ".agentstrap/config.json (runtime config)", bool(m.get("config"))),
    ("manifest", ".agentstrap/manifest.json (install stamp)", bool(m.get("manifest"))),
]
present = [c for c in components if c[2]]
missing = [c for c in components if not c[2]]

lines = []
lines.append("# AgentStrap — Sanity Check")
lines.append("")
lines.append(f"- **Mode:** `{mode}`")
lines.append(f"- **Project:** `{facts.get('project_dir','')}`")
lines.append(f"- **Git:** {'yes' if facts.get('is_git') else 'no'}"
             f" (remote: {'yes' if facts.get('has_remote') else 'no'}) · "
             f"**Obsidian vault:** {'yes' if facts.get('obsidian') else 'no'} · "
             f"**Stage guess:** {facts.get('stage_guess')}")
if facts.get("languages"):
    lines.append(f"- **Languages:** {', '.join(facts['languages'])}")
if facts.get("numbered_domains"):
    lines.append(f"- **Existing domains (will be conformed to, not renamed):** {', '.join(facts['numbered_domains'])}")
lines.append("")
lines.append("## Component inventory")
lines.append("")
lines.append("| Component | Status |")
lines.append("| --- | --- |")
for key, label, ok in components:
    lines.append(f"| {label} | {'✓ present' if ok else '✗ missing'} |")
lines.append("")
if mode == "greenfield":
    lines.append("**Recommendation:** greenfield — run the full bootstrap scaffold.")
elif mode == "adopt":
    lines.append("**Recommendation:** adopt — keep all existing content untouched; add ONLY the missing "
                 "components below, conforming to your existing folder naming. Nothing is overwritten.")
    lines.append("")
    lines.append("### Gaps to offer (additive only)")
    for key, label, ok in missing:
        lines.append(f"- [ ] {label}")
else:
    lines.append("**Recommendation:** stamped — AgentStrap already applied. Verify the manifest version and "
                 "repair only missing/ drifted components.")

report = "\n".join(lines)
verdict = {"mode": mode, "missing": [c[0] for c in missing], "present": [c[0] for c in present],
           "numbered_domains": facts.get("numbered_domains", []), "obsidian": facts.get("obsidian", False),
           "stage_guess": facts.get("stage_guess"), "is_git": facts.get("is_git"), "has_remote": facts.get("has_remote")}

print(report)
print("---JSON---")
print(json.dumps(verdict))

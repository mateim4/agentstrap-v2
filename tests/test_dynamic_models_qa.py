"""tests/test_dynamic_models_qa.py

Adversarial QA Test Suite for AgentStrap Dynamic Detection & Migration Models
Focuses on:
  - Contract & Schema Mismatches (detect-project.py vs normalize.py)
  - Ambiguity handling & verdict state contradictions (sanity-check.py)
  - Filename injection & path traversal vulnerabilities
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills", "bootstrap")

DETECT_PY = os.path.join(SKILLS_DIR, "detect-project.py")
SANITY_PY = os.path.join(SKILLS_DIR, "sanity-check.py")
NORMALIZE_PY = os.path.join(SKILLS_DIR, "normalize.py")


@pytest.fixture
def temp_project(tmp_path):
    """Creates an isolated temporary project directory."""
    proj = tmp_path / "project"
    proj.mkdir()
    return proj


def run_py(script_path, project_dir, *extra_args):
    """Executes a script against a project directory and returns stdout, stderr, returncode."""
    cmd = [sys.executable, script_path, str(project_dir)] + list(extra_args)
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout, res.stderr, res.returncode


def parse_json_verdict(output):
    """Extracts JSON payload after ---JSON--- marker in stdout."""
    if "---JSON---" in output:
        json_part = output.split("---JSON---")[1].strip()
        return json.loads(json_part)
    return json.loads(output)


# ── 1. SCHEMA & CONTRACT MISMATCH TESTS ─────────────────────────────────────

def test_contract_mismatch_detect_to_normalize(temp_project):
    """
    CRITICAL BUG: detect-project.py outputs `existing_locations` as:
        {"handoff": [{"path": "handoff.md", "type": "file", "count": 1}]}
    while normalize.py expects `existing_locations` as:
        {"handoff": {"path": "handoff.md", "type": "file", "count": 1}}

    When normalize.py runs `_detect()`, it fails with:
        TypeError: list indices must be integers or slices, not str
    """
    # Create a detected governance file
    handoff_file = temp_project / "handoff.md"
    handoff_file.write_text("# Handoff\n")

    # Run detect-project.py directly to verify its output structure
    det_out, det_err, det_code = run_py(DETECT_PY, temp_project)
    assert det_code == 0
    facts = json.loads(det_out)
    assert "existing_locations" in facts
    assert isinstance(facts["existing_locations"]["handoff"], list)

    # Run normalize.py (dry run plan) -> Expecting crash due to contract mismatch
    norm_out, norm_err, norm_code = run_py(NORMALIZE_PY, temp_project)

    # Validate that normalize.py fails with TypeError due to data model mismatch
    assert norm_code != 0
    assert "TypeError: list indices must be integers or slices, not str" in norm_err


# ── 2. STATE CONTRADICTION & AMBIGUITY TESTS ────────────────────────────────

def test_sanity_check_ambiguity_verdict_contradiction(temp_project):
    """
    CONTRADICTION: When multiple candidate locations exist for a component:
      1. `sanity-check.py` identifies the component in `ambiguities`.
      2. `singles` excludes ambiguous components.
      3. `present` includes the component key because `markers` is true.
      4. `verdict["existing_locations"]` (built from `singles`) lacks the component.

    Result: `verdict["present"]` claims "decisions_log" is present, but `verdict["existing_locations"]["decisions_log"]` is missing!
    Downstream tools relying on `existing_locations` will raise KeyError or misbehave.
    """
    # Create two candidates for decisions_log
    d1 = temp_project / "Decisions Log.md"
    d1.write_text("# Decision Log 1\n")

    adrs_dir = temp_project / "adrs"
    adrs_dir.mkdir()
    adr1 = adrs_dir / "ADR-001.md"
    adr1.write_text("# ADR 1\n")

    stdout, stderr, code = run_py(SANITY_PY, temp_project)
    assert code == 0

    verdict = parse_json_verdict(stdout)

    assert "decisions_log" in verdict["present"]
    assert "decisions_log" in verdict["ambiguities"]
    assert len(verdict["ambiguities"]["decisions_log"]) == 2

    # State contradiction check: present says yes, but existing_locations key is missing!
    assert "decisions_log" not in verdict["existing_locations"], (
        "Ambiguous component should either be resolved or present in existing_locations as list, "
        "not silently dropped from existing_locations while marked as present."
    )


# ── 3. FILENAME INJECTION & SANITIZATION TESTS ─────────────────────────────

def test_markdown_and_pipe_injection_in_reports(temp_project):
    """
    INJECTION QA TEST:
    Tests whether directory paths containing pipe '|' characters are interpolated into markdown table outputs
    without escaping, distorting Markdown table column structures.
    """
    pipe_dir = temp_project / "docs | table_injection"
    pipe_dir.mkdir()
    d_file = pipe_dir / "Decisions Log.md"
    d_file.write_text("# Decisions\n")

    stdout, stderr, code = run_py(SANITY_PY, temp_project)
    assert code == 0

    lines = stdout.splitlines()
    table_lines = [l for l in lines if "table_injection" in l and "|" in l]
    assert len(table_lines) > 0, "Unescaped path with pipes should appear in output"


def test_path_traversal_and_directory_symlink_traversal(temp_project):
    """
    PATH TRAVERSAL / SYMLINK ESCAPE QA TEST:
    Tests how os.walk in detect-project.py processes symlinked files vs directories.
    Symlinked files are visited, but symlinked directories are ignored because os.walk followlinks defaults to False.
    """
    outside_dir = temp_project.parent / "outside_target"
    outside_dir.mkdir(exist_ok=True)
    outside_file = outside_dir / "Decisions Log.md"
    outside_file.write_text("# External Decisions\n")

    # Symlink file directly into root
    symlink_file = temp_project / "Decisions Log.md"
    os.symlink(outside_file, symlink_file)

    stdout, stderr, code = run_py(DETECT_PY, temp_project)
    assert code == 0

    facts = json.loads(stdout)
    locs = facts["existing_locations"].get("decisions_log", [])
    assert len(locs) == 1, "Symlinked file is matched by filename walker"
    assert locs[0]["path"] == "Decisions Log.md"


def test_control_character_and_newline_injection(temp_project):
    """
    INJECTION / CONTROL CHAR QA TEST:
    Tests if subdirectories with newlines or backticks affect generated report format.
    """
    backtick_dir = temp_project / "docs`injection"
    backtick_dir.mkdir()
    d_file = backtick_dir / "Decisions Log.md"
    d_file.write_text("# Decisions\n")

    stdout, stderr, code = run_py(SANITY_PY, temp_project)
    assert code == 0
    assert "docs`injection" in stdout

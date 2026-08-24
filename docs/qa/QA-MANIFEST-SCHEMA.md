# Adversarial QA Feedback: AgentStrap Installation Manifest Schema (`templates/manifest.schema.json`)

**Date:** March 30, 2026
**Auditor:** Jules (Adversarial QA Specialist)
**Target:** `templates/manifest.schema.json` & Bootstrap State Invariants

---

## Executive Summary

An adversarial QA pass was conducted on the AgentStrap Installation Manifest Schema (`templates/manifest.schema.json`). The manifest serves as the installation stamp written by `/agentstrap:bootstrap`. Its presence transitions a project run from uninitialized/adopt into **stamped** (sanity-check/upgrade) mode, recording created artifacts so upgrades are diff-based and non-destructive.

While `manifest.schema.json` provides basic structural validation (enforcing required fields `agentstrap_version`, `applied_at`, and `mode`), an adversarial assessment revealed critical gaps in **tracking invariants**, **array uniqueness**, **mode consistency**, **schema strictness**, and **state transition completeness**.

---

## Key Findings & Adversarial Edge Cases

### 1. Missing Schema Definition for `linked` Field (Tracking Invariant Violation)
* **Severity:** High (P1)
* **Finding:** `skills/bootstrap/SKILL.md` (Step 3) specifies that in `adopt` mode, `.agentstrap/manifest.json` must include a `linked` array listing existing governance components that were structurally detected and linked rather than created. However, `templates/manifest.schema.json` omits the `linked` property definition entirely.
* **Impact:** Any manifest containing `linked: [...]` relies on unvalidated property handling. If strict schema validation is later enforced (`additionalProperties: false`), valid adopt-mode manifests created per `SKILL.md` specification will fail validation.
* **Recommendation:** Add the `linked` property to `manifest.schema.json` with item type `string`, `uniqueItems: true`, and path format constraints.

---

### 2. Absence of Array Uniqueness Constraints (`uniqueItems: true`)
* **Severity:** Medium (P2)
* **Finding:** Neither `created` nor `conformed_to.domains` specify `"uniqueItems": true`.
* **Impact:** Manifests can contain duplicate entries in `created` (e.g., `["agents.md", "agents.md"]`) or `conformed_to.domains`. During upgrade or sanity-check passes in `stamped` mode, duplicate path entries can cause redundant file checks, duplicate state diff logging, or race conditions during repair operations.
* **Recommendation:** Explicitly add `"uniqueItems": true` to `created`, `linked`, and `conformed_to.domains`.

---

### 3. Lack of Property Pollution Safeguards (`additionalProperties: false`)
* **Severity:** Medium (P2)
* **Finding:** Neither the root schema object nor `conformed_to` set `"additionalProperties": false`.
* **Impact:** Arbitrary untracked data can be injected into `.agentstrap/manifest.json` without failing schema validation (e.g., malicious payload injection, outdated config keys, drift artifacts).
* **Recommendation:** Add `"additionalProperties": false` at both the root object level and within `conformed_to`.

---

### 4. Unvalidated Timestamp and Version Formats
* **Severity:** Medium (P2)
* **Finding:** `applied_at` is typed as `{ "type": "string" }` without `"format": "date-time"` or pattern validation. Similarly, `agentstrap_version` lacks a SemVer pattern constraint (`pattern: "^\\d+\\.\\d+\\.\\d+.*$"`).
* **Impact:** Corrupted timestamps (e.g., `"applied_at": "invalid-date-string"`) pass schema validation, breaking timestamp comparisons during drift checks or migration logging.
* **Recommendation:** Set `"format": "date-time"` (or a pattern matching ISO 8601 timestamps) for `applied_at` and enforce SemVer pattern matching for `agentstrap_version`.

---

### 5. Absence of Relative Path & Traversal Protection
* **Severity:** High (P1)
* **Finding:** Items in `created` (and `linked`) are typed as plain strings without `minLength`, regex patterns, or absolute path prohibitions.
* **Impact:** Manifest entries can store empty strings (`""`), absolute filesystem paths (`"/etc/passwd"`), or path traversal strings (`"../../../root/.bashrc"`). If an upgrade tool attempts to repair or clean up files in `created`, path traversal could cause deletion or modification outside the project root.
* **Recommendation:** Enforce non-empty relative path validation on array items (e.g., `pattern: "^(?!/)(?!.*\\.\\./).+"` and `minLength: 1`).

---

### 6. Missing Greenfield vs. Adopt Mode Conditional Validation
* **Severity:** Low (P3)
* **Finding:** The schema allows `conformed_to` in `greenfield` mode, and does not require `conformed_to` (or `linked`) when `mode == "adopt"`.
* **Impact:** Inconsistent manifest state where a `greenfield` manifest carries `adopt`-specific structure, or an `adopt` manifest lacks details on what existing conventions it conformed to.
* **Recommendation:** Use JSON Schema conditional logic (`allOf` with `if`/`then`/`else`) to enforce that `conformed_to` and `linked` are valid for `adopt` mode while restricting `conformed_to` in pure `greenfield` mode.

---

### 7. State Transition Completeness & Drift Handling
* **Severity:** Medium (P2)
* **Finding:** The transition graph (`greenfield` / `adopt` → `stamped`) assumes `manifest.json` is immutable after creation except during version upgrades. However, no checksums (e.g., SHA-256 hashes of created files) are recorded in the manifest.
* **Impact:** In `stamped` mode, AgentStrap can verify file existence, but cannot detect silent user modifications or content drift in AgentStrap-owned files without re-verifying against template defaults.
* **Recommendation:** Consider adding optional checksum tracking for created files (e.g., `"checksums": { "agents.md": "sha256-..." }`) to strengthen drift detection in `stamped` mode.

---

## Negative Test Cases & Boundary Conditions

A comprehensive test suite has been implemented at `tests/test_manifest_schema.py` using `jsonschema`. It exercises boundary conditions and schema gaps:

| Test Case | Objective / Boundary Condition | Expected Schema Result | Current Schema Status |
| --- | --- | --- | --- |
| `test_missing_required_agentstrap_version` | Omit `agentstrap_version` | Validation Error | **PASSED** (Rejected) |
| `test_missing_required_mode` | Omit `mode` | Validation Error | **PASSED** (Rejected) |
| `test_invalid_mode_enum` | Set `mode: "stamped"` | Validation Error | **PASSED** (Rejected) |
| `test_invalid_created_type` | Set `created: "not-an-array"` | Validation Error | **PASSED** (Rejected) |
| `test_gap_duplicate_items_in_created_array` | Duplicate path entries in `created` | Validation Error (`uniqueItems`) | **GAP** (Allowed) |
| `test_gap_missing_linked_property_definition` | Add `linked: [...]` per `SKILL.md` spec | Field Validated | **GAP** (Field Missing) |
| `test_gap_unrestricted_additional_properties` | Inject untracked fields (`malicious_payload`) | Validation Error (`additionalProperties`) | **GAP** (Allowed) |
| `test_gap_unvalidated_applied_at_format` | Pass `"applied_at": "invalid-timestamp"` | Validation Error (`date-time`) | **GAP** (Allowed) |
| `test_gap_path_traversal_and_empty_paths` | Pass `""`, `"/etc/passwd"`, `"../../"` | Validation Error (`pattern`) | **GAP** (Allowed) |
| `test_gap_mode_conditional_validation` | `conformed_to` in `greenfield` mode | Conditional Enforcement | **GAP** (Allowed) |
| `test_gap_duplicate_domains_in_conformed_to` | Duplicate domains in `conformed_to.domains` | Validation Error (`uniqueItems`) | **GAP** (Allowed) |

---

## Recommended Schema Improvements

Below is the proposed, hardened version of `templates/manifest.schema.json` incorporating all recommendations while remaining backward-compatible with valid manifests:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentStrap install stamp (.agentstrap/manifest.json)",
  "description": "Written by /agentstrap:bootstrap. Its presence flips a re-run into 'stamped' (sanity-check/upgrade) mode. Records exactly what bootstrap created and linked so re-runs are a desired-vs-actual diff, never a clobber.",
  "type": "object",
  "required": ["agentstrap_version", "applied_at", "mode"],
  "additionalProperties": false,
  "properties": {
    "agentstrap_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+.*$"
    },
    "applied_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO-8601 timestamp when bootstrap was executed."
    },
    "mode": {
      "type": "string",
      "enum": ["greenfield", "adopt"]
    },
    "created": {
      "type": "array",
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "pattern": "^(?!/)(?!.*\\.\\./).+"
      },
      "description": "Project-relative paths AgentStrap created (so upgrades touch only its own files)."
    },
    "linked": {
      "type": "array",
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "pattern": "^(?!/)(?!.*\\.\\./).+"
      },
      "description": "Project-relative paths to existing components that were structurally detected and linked in adopt mode."
    },
    "conformed_to": {
      "type": "object",
      "additionalProperties": false,
      "description": "Existing conventions AgentStrap adapted to in adopt mode.",
      "properties": {
        "domains": {
          "type": "array",
          "uniqueItems": true,
          "items": { "type": "string", "minLength": 1 }
        },
        "handoff_file": { "type": "string", "minLength": 1 },
        "delta_file": { "type": "string", "minLength": 1 }
      }
    }
  }
}
```

---

## Conclusion

The current `templates/manifest.schema.json` satisfies basic typing requirements but lacks necessary validation constraints to protect against path traversal, duplicate path tracking, property pollution, and specification drift between `SKILL.md` and the schema. Adopting the recommendations in this report will ensure robust, deterministic behavior across `greenfield`, `adopt`, and `stamped` modes.

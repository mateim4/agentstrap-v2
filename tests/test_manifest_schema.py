#!/usr/bin/env python3
"""
Negative and Boundary Test Suite for AgentStrap Installation Manifest Schema
(templates/manifest.schema.json)

Exercises current schema behavior vs expected adversarial invariants:
- Tracking invariants & array uniqueness (`created`, `linked`, `conformed_to.domains`)
- State transition & mode consistency (`greenfield` vs `adopt`)
- Type safety, timestamp format, path validation, and strict property enforcement (`additionalProperties: false`)
"""

import json
import os
import unittest
import jsonschema

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "manifest.schema.json")

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class TestManifestSchemaBaseline(unittest.TestCase):
    """Test cases that conform to valid manifest structures."""

    def setUp(self):
        self.schema = load_schema()
        self.validator = jsonschema.Draft7Validator(self.schema)

    def test_valid_greenfield_manifest(self):
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "greenfield",
            "created": ["00 - Foundations/README.md", "agents.md"]
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertEqual(len(errors), 0, f"Valid greenfield manifest failed validation: {errors}")

    def test_valid_adopt_manifest(self):
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "adopt",
            "created": ["agents.md", ".agentstrap/config.json"],
            "conformed_to": {
                "domains": ["00 - Foundations"],
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md"
            }
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertEqual(len(errors), 0, f"Valid adopt manifest failed validation: {errors}")


class TestManifestSchemaStrictnessFailures(unittest.TestCase):
    """Test cases expected to fail schema validation under current schema."""

    def setUp(self):
        self.schema = load_schema()
        self.validator = jsonschema.Draft7Validator(self.schema)

    def test_missing_required_agentstrap_version(self):
        instance = {
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "greenfield"
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertTrue(any("agentstrap_version" in err.message for err in errors))

    def test_missing_required_mode(self):
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z"
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertTrue(any("mode" in err.message for err in errors))

    def test_invalid_mode_enum(self):
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "stamped"  # 'stamped' is a status, valid enum is only greenfield|adopt
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertTrue(any("mode" in err.path or "stamped" in err.message for err in errors))

    def test_invalid_created_type(self):
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "greenfield",
            "created": "not-an-array"
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertTrue(len(errors) > 0)


class TestManifestSchemaAdversarialGaps(unittest.TestCase):
    """
    Adversarial edge cases that test current schema gaps.
    These test cases demonstrate missing constraints in templates/manifest.schema.json.
    """

    def setUp(self):
        self.schema = load_schema()
        self.validator = jsonschema.Draft7Validator(self.schema)

    def test_gap_duplicate_items_in_created_array(self):
        """GAP: created array should enforce uniqueItems: true, but currently allows duplicates."""
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "greenfield",
            "created": ["agents.md", "agents.md"]
        }
        errors = list(self.validator.iter_errors(instance))
        # Demonstrating current behavior (0 errors = schema gap)
        is_schema_permissive = (len(errors) == 0)
        self.assertTrue(is_schema_permissive, "Schema unexpectedly rejected duplicate created items.")

    def test_gap_missing_linked_property_definition(self):
        """GAP: SKILL.md mentions 'linked' array for adopt mode, but manifest.schema.json has no 'linked' property definition."""
        self.assertNotIn("linked", self.schema.get("properties", {}),
                         "manifest.schema.json missing 'linked' field definition.")

    def test_gap_unrestricted_additional_properties(self):
        """GAP: additionalProperties: false is missing at root and conformed_to, allowing arbitrary payload pollution."""
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "greenfield",
            "malicious_payload": {"injected": True},
            "untracked_field": "test"
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertEqual(len(errors), 0, "Schema failed to allow additional properties due to missing additionalProperties: false restriction.")

    def test_gap_unvalidated_applied_at_format(self):
        """GAP: applied_at string lacks format: date-time / date-time regex validation."""
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "not-a-timestamp-123",
            "mode": "greenfield"
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertEqual(len(errors), 0, "Schema rejected invalid timestamp format because format is missing.")

    def test_gap_path_traversal_and_empty_paths(self):
        """GAP: created items permit empty strings, absolute paths, and path traversal strings."""
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "greenfield",
            "created": ["", "/etc/passwd", "../../../root/.bashrc"]
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertEqual(len(errors), 0, "Schema rejected path traversal/absolute paths due to lack of pattern/minLength constraints.")

    def test_gap_mode_conditional_validation(self):
        """GAP: Schema allows adopt-specific fields (conformed_to) in greenfield mode without conditional constraints."""
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "greenfield",
            "conformed_to": {
                "domains": ["00 - Foundations"]
            }
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertEqual(len(errors), 0, "Schema rejected conformed_to in greenfield mode, but conditional validation is not enforced.")

    def test_gap_duplicate_domains_in_conformed_to(self):
        """GAP: conformed_to.domains permits duplicate domain paths."""
        instance = {
            "agentstrap_version": "2.0.0",
            "applied_at": "2026-03-30T12:00:00Z",
            "mode": "adopt",
            "conformed_to": {
                "domains": ["00 - Foundations", "00 - Foundations"]
            }
        }
        errors = list(self.validator.iter_errors(instance))
        self.assertEqual(len(errors), 0, "Schema rejected duplicate domains in conformed_to.domains.")


if __name__ == "__main__":
    unittest.main()

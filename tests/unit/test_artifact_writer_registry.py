"""Tests for lazy uniform artifact-writer registration."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.artifact_writer_registry import ARTIFACT_WRITERS


class ArtifactWriterRegistryTests(unittest.TestCase):
    def test_registry_contains_only_lazy_string_bindings(self) -> None:
        self.assertGreaterEqual(len(ARTIFACT_WRITERS), 10)
        for name, spec in ARTIFACT_WRITERS.items():
            with self.subTest(name=name):
                self.assertTrue(name)
                self.assertTrue(spec.module.startswith("scenesmith.robot_lab."))
                self.assertTrue(spec.builder.startswith("build_"))
                self.assertTrue(spec.verifier.startswith("verify_"))
                self.assertTrue(spec.output.startswith("configurations/robot_lab/"))


if __name__ == "__main__":
    unittest.main()

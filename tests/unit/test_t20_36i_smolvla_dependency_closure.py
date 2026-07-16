from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36i_smolvla_dependency_closure import (
    build_result,
    load_sources,
    verify_result,
)


class T2036iSmolVLADependencyClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_sources()
        cls.result = build_result(sources=cls.sources)

    def test_exact_recursive_closure_finds_both_missing_requirements(self) -> None:
        verify_result(self.result, sources=self.sources)
        rows = self.result["environment_manifest"]["requirements"]
        self.assertEqual(
            [row["package"] for row in rows],
            ["accelerate", "lerobot", "num2words", "transformers"],
        )
        self.assertEqual(
            [row["package"] for row in self.result["missing_requirements"]],
            ["accelerate", "num2words"],
        )
        self.assertTrue(self.result["observed_failure_is_in_declared_closure"])

    def test_correction_fails_before_attempt_and_requires_new_owner(self) -> None:
        correction = self.result["correction_design"]
        self.assertTrue(correction["auto_processor_smoke_must_precede_attempt_marker"])
        self.assertTrue(correction["replacement_attempt_requires_new_owner_authority"])
        self.assertFalse(self.result["replacement_attempt_ready"])
        self.assertFalse(self.result["replacement_attempt_authorized"])
        self.assertFalse(self.result["dependency_install_performed"])

    def test_source_or_authority_drift_rejects(self) -> None:
        source_drift = copy.deepcopy(self.sources)
        source_drift["pyproject_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_result(sources=source_drift)
        result_drift = copy.deepcopy(self.result)
        result_drift["replacement_attempt_authorized"] = True
        with self.assertRaises(ValueError):
            verify_result(sign_payload(result_drift), sources=self.sources)


if __name__ == "__main__":
    unittest.main()

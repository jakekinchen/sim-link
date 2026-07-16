from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36j_a_offline_cache_resolution import (
    EXPECTED_INSTALLS,
    build_result,
    load_sources,
    verify_result,
)


class T2036jAOfflineCacheResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_sources()
        cls.result = build_result(sources=cls.sources)

    def test_exact_recursive_install_set_resolves_offline(self) -> None:
        verify_result(self.result, sources=self.sources)
        self.assertEqual(
            self.result["offline_resolution"]["would_install"],
            [
                {"package": package, "version": version}
                for package, version in sorted(EXPECTED_INSTALLS.items())
            ],
        )
        self.assertTrue(self.result["all_required_packages_available_offline"])
        self.assertFalse(self.result["network_acquisition_required"])

    def test_every_cached_package_has_content_identity(self) -> None:
        rows = self.result["cache_manifest"]["packages"]
        self.assertEqual(
            [row["package"] for row in rows], sorted(EXPECTED_INSTALLS)
        )
        for row in rows:
            self.assertEqual(len(row["content_tree_sha256"]), 64)
            self.assertEqual(len(row["metadata_sha256"]), 64)
            self.assertGreater(row["content_file_count"], 0)
            self.assertGreater(row["content_total_bytes"], 0)

    def test_owner_boundary_retains_no_mutation_or_attempt(self) -> None:
        self.assertTrue(
            self.result["planned_offline_install"]["requires_new_owner_authority"]
        )
        self.assertTrue(
            self.result["replacement_boundary"]["at_most_one_replacement_attempt"]
        )
        self.assertTrue(self.result["replacement_boundary"]["gate_b_unchanged"])
        self.assertFalse(self.result["dependency_install_performed"])
        self.assertFalse(self.result["environment_mutated"])
        self.assertFalse(self.result["attempt_marker_created"])
        self.assertFalse(self.result["replacement_attempt_authorized"])

    def test_resolver_or_authority_drift_rejects(self) -> None:
        source_drift = copy.deepcopy(self.sources)
        source_drift["dry_run"]["would_install"].append(
            {"package": "unexpected", "version": "1.0"}
        )
        with self.assertRaises(ValueError):
            build_result(sources=source_drift)
        duplicate_cache_row = copy.deepcopy(self.sources)
        duplicate_cache_row["cache_packages"][1] = copy.deepcopy(
            duplicate_cache_row["cache_packages"][0]
        )
        with self.assertRaises(ValueError):
            build_result(sources=duplicate_cache_row)
        result_drift = copy.deepcopy(self.result)
        result_drift["dependency_install_performed"] = True
        with self.assertRaises(ValueError):
            verify_result(sign_payload(result_drift), sources=self.sources)


if __name__ == "__main__":
    unittest.main()

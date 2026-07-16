from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (
    EXPECTED_OFFLINE_INSTALLS,
    ROOT_REQUIREMENTS,
    build_contract,
    build_corrected_preflight,
    build_installed_closure,
    build_processor_smoke_evidence,
    load_sources,
    verify_contract,
    verify_corrected_preflight,
    verify_installed_closure,
    verify_processor_smoke_evidence,
)


class T2036jBCorrectedPreflightContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_sources()
        cls.contract = build_contract(sources=cls.sources)
        cls.marker_environment = {
            "implementation_name": "cpython",
            "implementation_version": "3.12.12",
            "os_name": "posix",
            "platform_machine": "arm64",
            "platform_python_implementation": "CPython",
            "platform_release": "fixture",
            "platform_system": "Darwin",
            "platform_version": "fixture",
            "python_full_version": "3.12.12",
            "python_version": "3.12",
            "sys_platform": "darwin",
            "extra": "",
        }
        cls.distributions = cls._distribution_fixture()
        cls.closure = build_installed_closure(
            root_requirements=ROOT_REQUIREMENTS,
            distributions=cls.distributions,
            marker_environment=cls.marker_environment,
        )
        cls.processor = build_processor_smoke_evidence(
            expected_vlm_snapshot=cls.contract["processor_smoke"][
                "exact_vlm_snapshot"
            ],
            observed_vlm_snapshot=cls.contract["processor_smoke"][
                "exact_vlm_snapshot"
            ],
            processor_class="SmolVLMProcessor",
            tokenizer_class="GPT2TokenizerFast",
            image_processor_class="SmolVLMImageProcessor",
            opened_snapshot_files=[
                "processor_config.json",
                "tokenizer.json",
                "preprocessor_config.json",
            ],
            offline_environment={
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
            },
            local_files_only=True,
            network_attempted=False,
            constructed=True,
        )

    def test_contract_binds_exact_cache_and_ordering(self) -> None:
        verify_contract(self.contract, sources=self.sources)
        self.assertEqual(
            self.contract["exact_offline_install"],
            [
                {"package": package, "version": version}
                for package, version in sorted(EXPECTED_OFFLINE_INSTALLS.items())
            ],
        )
        self.assertEqual(
            [row["stage"] for row in self.contract["required_stage_order"]],
            [
                "recursive_installed_closure",
                "offline_auto_processor_smoke",
                "attempt_marker",
                "full_policy_construction",
            ],
        )

    def test_recursive_closure_honors_versions_and_active_markers(self) -> None:
        self.assertTrue(self.closure["all_requirements_satisfied"])
        packages = [row["package"] for row in self.closure["packages"]]
        self.assertIn("docopt", packages)
        self.assertIn("psutil", packages)
        self.assertIn("packaging", packages)
        self.assertNotIn("windows-only", packages)
        self.assertNotIn("rich", packages)
        self.assertEqual(self.closure["missing_requirements"], [])
        self.assertEqual(self.closure["version_mismatches"], [])
        verify_installed_closure(self.closure)
        verify_processor_smoke_evidence(
            self.processor,
            expected_vlm_snapshot=self.contract["processor_smoke"][
                "exact_vlm_snapshot"
            ],
        )

    def test_missing_or_mismatched_recursive_dependency_fails_closed(self) -> None:
        missing = copy.deepcopy(self.distributions)
        del missing["docopt"]
        missing_closure = build_installed_closure(
            root_requirements=ROOT_REQUIREMENTS,
            distributions=missing,
            marker_environment=self.marker_environment,
        )
        self.assertFalse(missing_closure["all_requirements_satisfied"])
        with self.assertRaises(ValueError):
            self._preflight(closure=missing_closure)
        mismatch = copy.deepcopy(self.distributions)
        mismatch["psutil"]["version"] = "1.0.0"
        mismatch_closure = build_installed_closure(
            root_requirements=ROOT_REQUIREMENTS,
            distributions=mismatch,
            marker_environment=self.marker_environment,
        )
        self.assertFalse(mismatch_closure["all_requirements_satisfied"])
        with self.assertRaises(ValueError):
            self._preflight(closure=mismatch_closure)

    def test_processor_smoke_rejects_network_weight_or_snapshot_drift(self) -> None:
        for mutation in ("network", "weight", "snapshot"):
            values = {
                "expected_vlm_snapshot": self.contract["processor_smoke"][
                    "exact_vlm_snapshot"
                ],
                "observed_vlm_snapshot": self.contract["processor_smoke"][
                    "exact_vlm_snapshot"
                ],
                "processor_class": "SmolVLMProcessor",
                "tokenizer_class": "GPT2TokenizerFast",
                "image_processor_class": "SmolVLMImageProcessor",
                "opened_snapshot_files": ["processor_config.json"],
                "offline_environment": {
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                },
                "local_files_only": True,
                "network_attempted": False,
                "constructed": True,
            }
            if mutation == "network":
                values["network_attempted"] = True
            elif mutation == "weight":
                values["opened_snapshot_files"] = ["model.safetensors"]
            else:
                values["observed_vlm_snapshot"] = "/tmp/other-snapshot"
            with self.assertRaises(ValueError):
                build_processor_smoke_evidence(**values)

    def test_corrected_preflight_enforces_pre_marker_processor_gate(self) -> None:
        preflight = self._preflight()
        verify_corrected_preflight(preflight, contract=self.contract)
        stages = preflight["stage_evidence"]
        self.assertTrue(stages[0]["completed"])
        self.assertTrue(stages[1]["completed"])
        self.assertFalse(stages[2]["completed"])
        self.assertFalse(stages[3]["completed"])
        self.assertTrue(preflight["auto_processor_constructed"])
        self.assertFalse(preflight["attempt_marker_created"])
        self.assertFalse(preflight["model_constructed"])
        self.assertFalse(preflight["training_permit_created"])
        self.assertFalse(preflight["replacement_attempt_ready"])
        drift = copy.deepcopy(preflight)
        drift["attempt_marker_created"] = True
        with self.assertRaises(ValueError):
            verify_corrected_preflight(sign_payload(drift), contract=self.contract)
        closure_drift = copy.deepcopy(self.closure)
        closure_drift["active_edges"] = []
        closure_drift = sign_payload(closure_drift)
        with self.assertRaises(ValueError):
            self._preflight(closure=closure_drift)
        processor_drift = copy.deepcopy(self.processor)
        processor_drift["network_attempted"] = True
        processor_drift = sign_payload(processor_drift)
        with self.assertRaises(ValueError):
            build_corrected_preflight(
                contract=self.contract,
                owner_authorization_identity_sha256="a" * 64,
                authority_decision_identity_sha256="b" * 64,
                installed_closure=self.closure,
                processor_smoke=processor_drift,
                python_major_minor=[3, 12],
                mps_available=True,
                free_disk_bytes=8 * 1024 * 1024 * 1024,
                lerobot_stack_identity_sha256="c" * 64,
                batch_evidence_identity_sha256="d" * 64,
                checkpoint_tree_identity_sha256="e" * 64,
                source_commit="f" * 40,
                remote_source_commit="f" * 40,
                branch="codex/pi05-autolearn-loop",
                scoped_dirty_paths=[],
                attempt_exists=False,
                run_exists=False,
                result_exists=False,
            )

    def test_cache_or_contract_authority_drift_rejects(self) -> None:
        sources = copy.deepcopy(self.sources)
        packages = sources["offline_resolution"]["cache_manifest"]["packages"]
        packages[1] = copy.deepcopy(packages[0])
        sources["offline_resolution"] = sign_payload(sources["offline_resolution"])
        with self.assertRaises(ValueError):
            build_contract(sources=sources)
        reference_drift = copy.deepcopy(self.sources)
        reference_drift["source_refs"]["spec"]["path"] = "wrong.json"
        with self.assertRaises(ValueError):
            build_contract(sources=reference_drift)
        contract_drift = copy.deepcopy(self.contract)
        contract_drift["replacement_attempt_authorized"] = True
        with self.assertRaises(ValueError):
            verify_contract(sign_payload(contract_drift), sources=self.sources)

    def _preflight(self, *, closure=None):
        return build_corrected_preflight(
            contract=self.contract,
            owner_authorization_identity_sha256="a" * 64,
            authority_decision_identity_sha256="b" * 64,
            installed_closure=closure or self.closure,
            processor_smoke=self.processor,
            python_major_minor=[3, 12],
            mps_available=True,
            free_disk_bytes=8 * 1024 * 1024 * 1024,
            lerobot_stack_identity_sha256="c" * 64,
            batch_evidence_identity_sha256="d" * 64,
            checkpoint_tree_identity_sha256="e" * 64,
            source_commit="f" * 40,
            remote_source_commit="f" * 40,
            branch="codex/pi05-autolearn-loop",
            scoped_dirty_paths=[],
            attempt_exists=False,
            run_exists=False,
            result_exists=False,
        )

    @staticmethod
    def _distribution_fixture():
        sha = "1" * 64
        return {
            "lerobot": {
                "version": "0.6.1",
                "metadata_sha256": sha,
                "requires_dist": [],
            },
            "transformers": {
                "version": "5.5.4",
                "metadata_sha256": sha,
                "requires_dist": ["packaging>=20"],
            },
            "num2words": {
                "version": "0.5.14",
                "metadata_sha256": sha,
                "requires_dist": ["docopt>=0.6.2"],
            },
            "accelerate": {
                "version": "1.14.0",
                "metadata_sha256": sha,
                "requires_dist": [
                    "numpy>=1.17",
                    "psutil>=7.0",
                    "windows-only>=1; sys_platform == 'win32'",
                    "rich; extra == 'rich'",
                ],
            },
            "packaging": {
                "version": "25.0",
                "metadata_sha256": sha,
                "requires_dist": [],
            },
            "docopt": {
                "version": "0.6.2",
                "metadata_sha256": sha,
                "requires_dist": [],
            },
            "numpy": {
                "version": "2.2.6",
                "metadata_sha256": sha,
                "requires_dist": [],
            },
            "psutil": {
                "version": "7.2.2",
                "metadata_sha256": sha,
                "requires_dist": [],
            },
        }


if __name__ == "__main__":
    unittest.main()

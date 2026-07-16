import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.t20_36o_bounded_optimizer_authority import (
    MINIMUM_FREE_DISK_BYTES,
    build_attempt_marker,
    build_runtime_preflight,
    build_training_permit,
    verify_attempt_marker,
    verify_runtime_preflight,
    verify_training_permit,
)


class T2036oBoundedOptimizerAuthorityTest(unittest.TestCase):
    def setUp(self) -> None:
        spec = load_strict_json(
            Path("configurations/robot_lab/t20_36o_bounded_optimizer_spec.json")
        )
        self.sources = {
            "optimizer_spec": spec,
            "optimizer_sources": {
                "baseline_result": {"identity_sha256": "1" * 64}
            },
            "x_runtime": {
                "checkpoint_identity_sha256": "2" * 64,
                "lerobot_stack_identity_sha256": "3" * 64,
                "checkpoint_tree": [
                    {"path": "model.safetensors", "sha256": "4" * 64, "size_bytes": 1}
                ],
                "required_dependency_versions": {"torch": "2.11.0"},
                "snapshot_revision": "5" * 40,
                "snapshot_tree": [
                    {"path": "base.safetensors", "sha256": "6" * 64, "size_bytes": 2}
                ],
            },
        }

    def _preflight(self):
        return build_runtime_preflight(
            sources=self.sources,
            authority_identity="a" * 64,
            python_major_minor=[3, 12],
            mps_available=True,
            checkpoint_tree=self.sources["x_runtime"]["checkpoint_tree"],
            dependency_versions=self.sources["x_runtime"][
                "required_dependency_versions"
            ],
            snapshot_revision=self.sources["x_runtime"]["snapshot_revision"],
            snapshot_tree=self.sources["x_runtime"]["snapshot_tree"],
            free_disk_bytes=MINIMUM_FREE_DISK_BYTES,
            source_commit="b" * 40,
            remote_source_commit="b" * 40,
            attempt_exists=False,
            result_exists=False,
            output_checkpoint_exists=False,
        )

    def test_permit_binds_ceiling_schedule_and_marker_first(self) -> None:
        preflight = self._preflight()
        verify_runtime_preflight(
            preflight,
            sources=self.sources,
            authority_identity="a" * 64,
        )
        permit = build_training_permit(
            sources=self.sources,
            authority_identity="a" * 64,
            runtime_preflight=preflight,
        )
        verify_training_permit(
            permit,
            sources=self.sources,
            authority_identity="a" * 64,
            runtime_preflight=preflight,
        )
        self.assertEqual(permit["optimizer_update_count_ceiling"], 2500)
        self.assertEqual(permit["probe_update_counts"], [500, 1000, 1500, 2000, 2500])
        self.assertFalse(permit["retry_authorized"])
        self.assertFalse(permit["gate_c_authorized"])
        marker = build_attempt_marker(permit=permit, source_commit="c" * 40)
        verify_attempt_marker(marker, permit=permit)
        self.assertTrue(marker["created_before_optimizer_creation"])
        self.assertFalse(marker["optimizer_created"])

    def test_preflight_and_schedule_drift_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            build_runtime_preflight(
                sources=self.sources,
                authority_identity="a" * 64,
                python_major_minor=[3, 12],
                mps_available=True,
                checkpoint_tree=self.sources["x_runtime"]["checkpoint_tree"],
                dependency_versions=self.sources["x_runtime"][
                    "required_dependency_versions"
                ],
                snapshot_revision=self.sources["x_runtime"]["snapshot_revision"],
                snapshot_tree=self.sources["x_runtime"]["snapshot_tree"],
                free_disk_bytes=MINIMUM_FREE_DISK_BYTES,
                source_commit="b" * 40,
                remote_source_commit="b" * 40,
                attempt_exists=True,
                result_exists=False,
                output_checkpoint_exists=False,
            )
        drift = copy.deepcopy(self.sources)
        drift["optimizer_spec"] = copy.deepcopy(self.sources["optimizer_spec"])
        drift["optimizer_spec"]["correction_schedule"]["retry_authorized"] = True
        drift["optimizer_spec"] = sign_payload(drift["optimizer_spec"])
        preflight = build_runtime_preflight(
            sources=drift,
            authority_identity="a" * 64,
            python_major_minor=[3, 12],
            mps_available=True,
            checkpoint_tree=drift["x_runtime"]["checkpoint_tree"],
            dependency_versions=drift["x_runtime"]["required_dependency_versions"],
            snapshot_revision=drift["x_runtime"]["snapshot_revision"],
            snapshot_tree=drift["x_runtime"]["snapshot_tree"],
            free_disk_bytes=MINIMUM_FREE_DISK_BYTES,
            source_commit="b" * 40,
            remote_source_commit="b" * 40,
            attempt_exists=False,
            result_exists=False,
            output_checkpoint_exists=False,
        )
        with self.assertRaises(ValueError):
            build_training_permit(
                sources=drift,
                authority_identity="a" * 64,
                runtime_preflight=preflight,
            )


if __name__ == "__main__":
    unittest.main()

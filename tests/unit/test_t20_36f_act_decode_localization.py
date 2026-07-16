from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36f_act_decode_localization import (
    EXPECTED_CHECKPOINT_TREE,
    EXPECTED_DEPENDENCY_VERSIONS,
    EXPECTED_FINAL_ACTION_HASH,
    EXPECTED_FINAL_OBJECTIVE,
    JOINT_NAMES,
    build_attempt_marker,
    build_inference_permit,
    build_result,
    build_runtime_preflight,
    load_verified_sources,
    verify_result,
)


class T2036fActDecodeLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()
        cls.authority = "a" * 64
        cls.runtime = build_runtime_preflight(
            sources=cls.sources,
            authority_identity=cls.authority,
            python_major_minor=[3, 12],
            dependency_versions=EXPECTED_DEPENDENCY_VERSIONS,
            mps_available=True,
            lerobot_stack_identity_sha256="b" * 64,
            checkpoint_tree=EXPECTED_CHECKPOINT_TREE,
            free_disk_bytes=3 * 1024 * 1024 * 1024,
            source_commit="c" * 40,
            remote_source_commit="c" * 40,
            attempt_exists=False,
            result_exists=False,
        )
        cls.permit = build_inference_permit(
            sources=cls.sources,
            authority_identity=cls.authority,
            runtime_preflight=cls.runtime,
        )
        cls.attempt = build_attempt_marker(
            permit=cls.permit,
            authority_identity=cls.authority,
            source_commit="d" * 40,
        )

    def test_exact_reproduction_builds_bounded_result(self) -> None:
        result = self._result()
        verify_result(result, permit=self.permit, attempt=self.attempt)
        self.assertEqual(result["error_concentration"], "localized_physical_outlier")
        self.assertFalse(result["smolvla_entry_authorized"])
        self.assertFalse(result["gate_b_threshold_changed"])

    def test_preflight_rejects_remote_checkpoint_or_attempt_drift(self) -> None:
        base = self._runtime_kwargs()
        variants = []
        remote = copy.deepcopy(base)
        remote["remote_source_commit"] = "e" * 40
        variants.append(remote)
        checkpoint = copy.deepcopy(base)
        checkpoint["checkpoint_tree"][1]["sha256"] = "f" * 64
        variants.append(checkpoint)
        attempt = copy.deepcopy(base)
        attempt["attempt_exists"] = True
        variants.append(attempt)
        for values in variants:
            with self.assertRaises(ValueError):
                build_runtime_preflight(
                    sources=self.sources,
                    authority_identity=self.authority,
                    **values,
                )

    def test_result_rejects_hash_objective_or_queue_drift(self) -> None:
        kwargs = self._result_kwargs()
        for field, value in (
            ("reproduced_objective", 0.2),
            ("direct_action_hash", "f" * 64),
            ("direct_queue_maximum_error_rad", 0.01),
        ):
            variant = copy.deepcopy(kwargs)
            variant[field] = value
            with self.assertRaises(ValueError):
                build_result(permit=self.permit, attempt=self.attempt, **variant)

    def test_signed_result_rejects_authority_escalation(self) -> None:
        result = self._result()
        drift = copy.deepcopy(result)
        drift["optimizer_training"] = True
        with self.assertRaises(ValueError):
            verify_result(sign_payload(drift), permit=self.permit, attempt=self.attempt)

    def _runtime_kwargs(self):
        return {
            "python_major_minor": [3, 12],
            "dependency_versions": copy.deepcopy(EXPECTED_DEPENDENCY_VERSIONS),
            "mps_available": True,
            "lerobot_stack_identity_sha256": "b" * 64,
            "checkpoint_tree": copy.deepcopy(EXPECTED_CHECKPOINT_TREE),
            "free_disk_bytes": 3 * 1024 * 1024 * 1024,
            "source_commit": "c" * 40,
            "remote_source_commit": "c" * 40,
            "attempt_exists": False,
            "result_exists": False,
        }

    def _joint_rows(self, *, physical: bool):
        rows = []
        for index, name in enumerate(JOINT_NAMES):
            row = {
                "joint_name": name,
                "mean_absolute_error": 0.01,
                "maximum_absolute_error": 0.44 if index == 4 else 0.02,
                "maximum_error_timestep": 49 if index == 4 else 2,
            }
            if physical:
                row["threshold_exceedance_count"] = 1 if index == 4 else 0
            rows.append(row)
        return rows

    def _result_kwargs(self):
        return {
            "reproduced_objective": EXPECTED_FINAL_OBJECTIVE,
            "repetition_action_hashes": [EXPECTED_FINAL_ACTION_HASH] * 5,
            "direct_action_hash": EXPECTED_FINAL_ACTION_HASH,
            "direct_queue_maximum_error_rad": 0.0,
            "normalized_per_joint": self._joint_rows(physical=False),
            "physical_per_joint": self._joint_rows(physical=True),
            "time_regions": [
                {
                    "label": f"steps_{start}_{start + 9}",
                    "mean_absolute_error_rad": 0.01,
                    "maximum_absolute_error_rad": 0.44 if start == 40 else 0.02,
                    "threshold_exceedance_count": 1 if start == 40 else 0,
                }
                for start in range(0, 50, 10)
            ],
            "maximum_error": {
                "joint_name": "wrist_roll",
                "timestep": 49,
                "predicted_action": 0.44,
                "target_action": 0.0,
                "absolute_error_rad": 0.44,
            },
        }

    def _result(self):
        return build_result(
            permit=self.permit,
            attempt=self.attempt,
            **self._result_kwargs(),
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import socket
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (
    INFERENCE_SEEDS,
    OBJECTIVE_SEEDS,
)
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (
    ROOT_REQUIREMENTS,
    build_corrected_preflight,
    build_installed_closure,
    build_processor_smoke_evidence,
    verify_contract_file,
)
from scenesmith.robot_lab.t20_36j_exact_smolvla_gate_b import (
    _distribution_metadata_bytes,
    build_attempt_marker,
    build_failure,
    build_failure_result,
    build_training_permit,
    guarded_processor_access,
    load_verified_spec,
    verify_failure_result,
    verify_training_permit,
)


class T2036jExactSmolVLAGateBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = load_verified_spec()
        cls.authority = "a" * 64
        cls.contract = verify_contract_file()
        cls.closure = build_installed_closure(
            root_requirements=ROOT_REQUIREMENTS,
            distributions=cls._distributions(),
            marker_environment=cls._marker_environment(),
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
            opened_snapshot_files=["processor_config.json"],
            offline_environment={
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
            },
            local_files_only=True,
            network_attempted=False,
            constructed=True,
        )
        cls.preflight = build_corrected_preflight(
            contract=cls.contract,
            owner_authorization_identity_sha256="b" * 64,
            authority_decision_identity_sha256=cls.authority,
            installed_closure=cls.closure,
            processor_smoke=cls.processor,
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
        cls.permit = build_training_permit(
            spec=cls.spec,
            authority_identity=cls.authority,
            corrected_preflight=cls.preflight,
        )
        cls.attempt = build_attempt_marker(
            spec=cls.spec,
            authority_identity=cls.authority,
            training_permit=cls.permit,
            source_commit="1" * 40,
        )

    def test_permit_binds_corrected_environment_and_frozen_gate(self) -> None:
        verify_training_permit(
            self.permit,
            spec=self.spec,
            authority_identity=self.authority,
            corrected_preflight=self.preflight,
        )
        self.assertEqual(
            self.permit["environment_manifest_identity_sha256"],
            self.closure["environment_manifest_identity_sha256"],
        )
        self.assertEqual(
            self.permit["maximum_final_to_baseline_supervised_objective_ratio"],
            0.10,
        )
        self.assertEqual(
            self.permit["maximum_physical_action_error_rad"], 0.05
        )
        self.assertFalse(self.permit["retry_or_sweep_allowed"])

    def test_permit_rejects_preflight_or_gate_drift(self) -> None:
        drift = copy.deepcopy(self.preflight)
        drift["processor_smoke"]["network_attempted"] = True
        drift["processor_smoke"] = sign_payload(drift["processor_smoke"])
        drift = sign_payload(drift)
        with self.assertRaises(ValueError):
            build_training_permit(
                spec=self.spec,
                authority_identity=self.authority,
                corrected_preflight=drift,
            )
        gate = copy.deepcopy(self.spec)
        gate["gate"]["maximum_physical_action_error_rad"] = 0.06
        with self.assertRaises(ValueError):
            build_training_permit(
                spec=gate,
                authority_identity=self.authority,
                corrected_preflight=self.preflight,
            )

    def test_counted_failure_consumes_only_attempt_and_closes_alphabet(self) -> None:
        failure = build_failure(
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            failure_stage="runtime_smoke",
            error_type="RuntimeError",
            error_message="bounded failure",
            optimizer_update_count=0,
            model_constructed=True,
            model_loaded=True,
            model_inference=False,
            optimizer_created=False,
            optimizer_training=False,
        )
        result = build_failure_result(
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            failure=failure,
        )
        verify_failure_result(
            result,
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            failure=failure,
        )
        self.assertTrue(result["attempt_consumed"])
        self.assertTrue(result["smolvla_alphabet_closed"])
        self.assertFalse(result["retry_or_sweep_allowed"])

    def test_processor_guard_blocks_tensor_and_network_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "snapshot"
            root.mkdir()
            (root / "processor_config.json").write_text("{}", encoding="utf-8")
            (root / "model.safetensors").write_bytes(b"weights")
            with guarded_processor_access(root) as guard:
                self.assertEqual(
                    (root / "processor_config.json").read_text(encoding="utf-8"),
                    "{}",
                )
                with self.assertRaises(PermissionError):
                    (root / "model.safetensors").read_bytes()
                with self.assertRaises(RuntimeError):
                    socket.getaddrinfo("example.com", 443)
            self.assertEqual(
                guard.opened_snapshot_files, {"processor_config.json"}
            )
            self.assertTrue(guard.network_attempted)

    def test_processor_guard_maps_resolved_blob_targets_to_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "snapshot"
            root.mkdir()
            config_blob = base / "config-blob"
            weight_blob = base / "weight-blob"
            config_blob.write_text("{}", encoding="utf-8")
            weight_blob.write_bytes(b"weights")
            (root / "processor_config.json").symlink_to(config_blob)
            (root / "model.safetensors").symlink_to(weight_blob)
            with guarded_processor_access(root) as guard:
                self.assertEqual(config_blob.read_text(encoding="utf-8"), "{}")
                with self.assertRaises(PermissionError):
                    weight_blob.read_bytes()
            self.assertEqual(
                guard.opened_snapshot_files, {"processor_config.json"}
            )

    def test_processor_guard_preserves_lexical_snapshot_contract_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            physical = base / "physical"
            physical.mkdir()
            (physical / "processor_config.json").write_text(
                "{}", encoding="utf-8"
            )
            lexical = base / "lexical"
            lexical.symlink_to(physical, target_is_directory=True)
            with guarded_processor_access(lexical) as guard:
                self.assertEqual(
                    (lexical / "processor_config.json").read_text(
                        encoding="utf-8"
                    ),
                    "{}",
                )
            self.assertEqual(
                guard.opened_snapshot_files, {"processor_config.json"}
            )

    def test_editable_distribution_pkg_info_is_valid_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lerobot.egg-info"
            root.mkdir()
            (root / "PKG-INFO").write_bytes(b"Name: lerobot\nVersion: 0.6.1\n")

            class EditableDistribution:
                _path = root
                files = None

            self.assertEqual(
                _distribution_metadata_bytes(
                    EditableDistribution(), name="lerobot"
                ),
                b"Name: lerobot\nVersion: 0.6.1\n",
            )

    @staticmethod
    def _marker_environment():
        return {
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

    @staticmethod
    def _distributions():
        sha = "1" * 64
        rows = {
            "lerobot": ("0.6.1", []),
            "transformers": ("5.5.4", ["packaging>=20"]),
            "num2words": ("0.5.14", ["docopt>=0.6.2"]),
            "accelerate": ("1.14.0", ["numpy>=1.17", "psutil>=7.0"]),
            "packaging": ("25.0", []),
            "docopt": ("0.6.2", []),
            "numpy": ("2.2.6", []),
            "psutil": ("7.2.2", []),
        }
        return {
            name: {
                "version": version,
                "metadata_sha256": sha,
                "requires_dist": requires,
            }
            for name, (version, requires) in rows.items()
        }


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
import scenesmith.robot_lab.pi05_reviewed_input_gate as gate_module
from scenesmith.robot_lab.pi05_reviewed_input_gate import (
    PI05_CAMERA_ROLE_BINDING_SCHEMA_VERSION,
    PI05_LIVE_SESSION_ACCEPTANCE_SCHEMA_VERSION,
    PI05_REVIEWED_INPUT_GATE_SCHEMA_VERSION,
    PI05_REVIEWED_TASK_PROMPT_SCHEMA_VERSION,
    build_pi05_reviewed_input_gate,
    review_subject_sha256,
    verify_pi05_reviewed_input_gate,
)


SESSION_ID = "fixture-session-001"
REVIEW_DECISION_ID = "900"
EVALUATION_TIME_NS = 1_000_000_000_000
VALID_FROM_NS = EVALUATION_TIME_NS - 1_000
VALID_UNTIL_NS = EVALUATION_TIME_NS + 1_000
ISSUED_AT_NS = VALID_FROM_NS - 1_000
ISSUER_ID = "scenesmith_same_agent_reviewer_v1"
SOURCE_CONTRACT_PATH = Path(
    "configurations/robot_lab/"
    "pi05_policy_input_preprocessing.blocked_missing_inputs.json"
)
AUTHORITY_NOT_GRANTED = [
    "accepted_live_policy_input",
    "policy_shadow_input_valid",
    "policy_shadow",
    "model_weight_load",
    "policy_inference",
    "physical_follower_command",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]
SOURCE_REVIEW_AUTHORITY_NOT_GRANTED = [
    "live_candidate_session_accepted",
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _file_reference(path: Path, *, repo_root: Path) -> dict:
    encoded = path.read_bytes()
    return {
        "path": path.relative_to(repo_root).as_posix(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "size_bytes": len(encoded),
    }


def _review_manifest(source_contract: dict) -> dict:
    cameras = [
        {
            "stable_camera_identity_sha256": identity,
            "capture_camera_identity_sha256": marker * 64,
            "input_mode": {
                "pixel_format": "2vuy",
                "width": 640,
                "height": 480,
                "framerate_fps": 30,
            },
            "frames": [
                {
                    "frame_index": 0,
                    "frame_sha256": frame_marker * 64,
                    "width": 640,
                    "height": 480,
                    "channels": 3,
                    "encoding": "png",
                }
            ],
        }
        for identity, marker, frame_marker in zip(
            source_contract["camera_contract"]["stable_camera_identity_sha256"],
            ("a", "b"),
            ("c", "d"),
            strict=True,
        )
    ]
    return sign_payload(
        {
            "schema_version": (
                "scenesmith.static_pose_live_session_review_manifest.v1"
            ),
            "manifest_name": "pi05_static_pose_live_candidate_session_review",
            "qualification_scope": (
                "local_static_pose_live_candidate_session_review"
            ),
            "evidence_mode": (
                "tracked_redacted_private_candidate_session_review"
            ),
            "status": "candidate_observed_pending_review",
            "review_decision_required": True,
            "session_id": SESSION_ID,
            "candidate_only": True,
            "camera_observation_summary": cameras,
            "local_capabilities": [
                "redacted_static_pose_live_candidate_session_review_conformant"
            ],
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(
                SOURCE_REVIEW_AUTHORITY_NOT_GRANTED
            ),
            "hardware_opened": True,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "accepted_as_static_pose_bracketed_observation": False,
            "accepted_as_policy_shadow_input": False,
        }
    )


def _common_input(
    *,
    schema_version: str,
    input_kind: str,
    scope: str,
    source_contract: dict,
    evidence_class: str,
) -> dict:
    production = evidence_class == "tracked_production_review"
    return {
        "schema_version": schema_version,
        "input_kind": input_kind,
        "qualification_scope": scope,
        "evidence_class": evidence_class,
        "status": "reviewed" if production else "fixture_conformant",
        "issuer_id": ISSUER_ID,
        "review_decision_id": REVIEW_DECISION_ID,
        "source_contract_identity_sha256": source_contract["identity_sha256"],
        "session_id": SESSION_ID,
        "issued_at_unix_ns": ISSUED_AT_NS,
        "valid_from_unix_ns": VALID_FROM_NS,
        "valid_until_unix_ns": VALID_UNTIL_NS,
        "production_eligible": production,
        "proof_labels": [],
        "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED),
        "accepted_live_policy_input": False,
        "policy_input_built": False,
        "model_instantiated": False,
        "model_weights_read": False,
        "preprocessing_run": False,
        "policy_shadow_run": False,
        "policy_inference_run": False,
        "mujoco_replay_run": False,
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
    }


class _Fixture:
    def __init__(self, root: Path, *, evidence_class: str = "deterministic_fixture"):
        self.repo_root = root / "repo"
        self.repo_root.mkdir()
        source = Path(__file__).resolve().parents[2] / SOURCE_CONTRACT_PATH
        destination = self.repo_root / SOURCE_CONTRACT_PATH
        destination.parent.mkdir(parents=True)
        shutil.copyfile(source, destination)
        self.source_contract = load_strict_json(destination)
        self.calibration_path = self.repo_root / "private-calibration.json"
        _write_json(self.calibration_path, {"fixture": True})
        self.cache_root = self.repo_root / "fixture-cache"
        self.cache_root.mkdir()
        self.evidence_class = evidence_class

        self.manifest_path = (
            self.repo_root
            / "configurations/robot_lab/"
            f"pi05_static_pose_live_session_{SESSION_ID}.redacted.json"
        )
        self.manifest = _review_manifest(self.source_contract)
        _write_json(self.manifest_path, self.manifest)
        manifest_ref = _file_reference(
            self.manifest_path,
            repo_root=self.repo_root,
        )
        manifest_ref["schema_version"] = self.manifest["schema_version"]
        manifest_ref["identity_sha256"] = self.manifest["identity_sha256"]

        self.inputs = {
            "accepted_live_session_review_decision": self._acceptance(
                manifest_ref
            ),
            "reviewed_stable_camera_role_binding": self._camera_binding(
                manifest_ref
            ),
            "reviewed_task_prompt": self._task_prompt(),
        }
        self.review_path = (
            self.repo_root
            / "docs/reviewer-messages/900-pi05-fixture-reviewed-inputs.md"
        )
        self.review_path.parent.mkdir(parents=True)
        lines = ["# Fixture PI0.5 Reviewed Inputs", ""]
        for input_kind, payload in self.inputs.items():
            subject = review_subject_sha256(payload)
            payload["review_subject_sha256"] = subject
            lines.extend(
                [
                    f"PI05_REVIEW_INPUT_KIND: {input_kind}",
                    f"PI05_REVIEW_DECISION_ID: {REVIEW_DECISION_ID}",
                    f"PI05_REVIEW_SUBJECT_SHA256: {subject}",
                    "",
                ]
            )
        self.review_path.write_text("\n".join(lines), encoding="utf-8")
        review_ref = _file_reference(
            self.review_path,
            repo_root=self.repo_root,
        )
        for payload in self.inputs.values():
            payload["review_record"] = copy.deepcopy(review_ref)

        self.input_paths = {
            "acceptance_decision_path": (
                self.repo_root
                / "configurations/robot_lab/"
                f"pi05_static_pose_live_session_{SESSION_ID}.acceptance.json"
            ),
            "camera_role_binding_path": (
                self.repo_root
                / "configurations/robot_lab/"
                f"pi05_camera_role_binding_{SESSION_ID}.json"
            ),
            "task_prompt_path": (
                self.repo_root
                / "configurations/robot_lab/"
                f"pi05_task_prompt_{SESSION_ID}.json"
            ),
        }
        for path, payload in zip(
            self.input_paths.values(),
            self.inputs.values(),
            strict=True,
        ):
            _write_json(path, sign_payload(payload))

    def _acceptance(self, manifest_ref: dict) -> dict:
        production = self.evidence_class == "tracked_production_review"
        payload = _common_input(
            schema_version=PI05_LIVE_SESSION_ACCEPTANCE_SCHEMA_VERSION,
            input_kind="accepted_live_session_review_decision",
            scope="local_pi05_live_session_acceptance",
            source_contract=self.source_contract,
            evidence_class=self.evidence_class,
        )
        payload.update(
            {
                "review_manifest": copy.deepcopy(manifest_ref),
                "review_outcome": (
                    "accepted_for_pi05_reviewed_input_bundle"
                    if production
                    else "fixture_acceptance_conformant"
                ),
                "accepted_live_session_review": production,
                "accepted_as_static_pose_bracketed_observation": production,
                "local_capabilities": [
                    (
                        "pi05_live_session_acceptance_valid"
                        if production
                        else "fixture_pi05_live_session_acceptance_conformant"
                    )
                ],
            }
        )
        return payload

    def _camera_binding(self, manifest_ref: dict) -> dict:
        production = self.evidence_class == "tracked_production_review"
        identities = self.source_contract["camera_contract"][
            "stable_camera_identity_sha256"
        ]
        payload = _common_input(
            schema_version=PI05_CAMERA_ROLE_BINDING_SCHEMA_VERSION,
            input_kind="reviewed_stable_camera_role_binding",
            scope="local_pi05_stable_camera_role_binding",
            source_contract=self.source_contract,
            evidence_class=self.evidence_class,
        )
        payload.update(
            {
                "review_manifest": copy.deepcopy(manifest_ref),
                "assignments": [
                    {
                        "stable_camera_identity_sha256": identities[0],
                        "source_key": "observation.images.top",
                        "model_key": "observation.images.base_0_rgb",
                    },
                    {
                        "stable_camera_identity_sha256": identities[1],
                        "source_key": "observation.images.wrist",
                        "model_key": "observation.images.left_wrist_0_rgb",
                    },
                ],
                "private_review_evidence_sha256": "e" * 64,
                "binding_reviewed": production,
                "numeric_camera_index_used": False,
                "raw_camera_identity_included": False,
                "local_capabilities": [
                    (
                        "pi05_stable_camera_role_binding_valid"
                        if production
                        else "fixture_pi05_camera_role_binding_conformant"
                    )
                ],
            }
        )
        return payload

    def _task_prompt(self) -> dict:
        production = self.evidence_class == "tracked_production_review"
        task = "sort the block"
        template = self.source_contract["task_contract"]["prompt_template"]
        payload = _common_input(
            schema_version=PI05_REVIEWED_TASK_PROMPT_SCHEMA_VERSION,
            input_kind="reviewed_task_prompt",
            scope="local_pi05_task_prompt_review",
            source_contract=self.source_contract,
            evidence_class=self.evidence_class,
        )
        payload.update(
            {
                "task_key": "task",
                "task_text": task,
                "task_text_sha256": hashlib.sha256(task.encode()).hexdigest(),
                "prompt_template_sha256": hashlib.sha256(
                    template.encode()
                ).hexdigest(),
                "prompt_prefix_sha256": hashlib.sha256(
                    f"Task: {task}, State: ".encode()
                ).hexdigest(),
                "task_prompt_reviewed": production,
                "local_capabilities": [
                    (
                        "pi05_task_prompt_review_valid"
                        if production
                        else "fixture_pi05_task_prompt_review_conformant"
                    )
                ],
            }
        )
        return payload

    @contextmanager
    def source_verifier_patch(self):
        with patch.object(
            gate_module,
            "verify_pi05_preprocessing_source_contract",
        ):
            yield

    def build(self, **overrides) -> dict:
        arguments = {
            "repo_root": self.repo_root,
            "hf_cache_root": self.cache_root,
            "calibration_path": self.calibration_path,
            "evaluation_time_unix_ns": EVALUATION_TIME_NS,
            **self.input_paths,
        }
        arguments.update(overrides)
        with self.source_verifier_patch():
            return build_pi05_reviewed_input_gate(**arguments)

    def verify(self, payload: dict, **overrides) -> None:
        arguments = {
            "repo_root": self.repo_root,
            "hf_cache_root": self.cache_root,
            "calibration_path": self.calibration_path,
            "evaluation_time_unix_ns": EVALUATION_TIME_NS,
            **self.input_paths,
        }
        arguments.update(overrides)
        with self.source_verifier_patch():
            verify_pi05_reviewed_input_gate(payload, **arguments)

    def resign_input(self, key: str, mutation) -> None:
        path_key = {
            "accepted_live_session_review_decision": "acceptance_decision_path",
            "reviewed_stable_camera_role_binding": "camera_role_binding_path",
            "reviewed_task_prompt": "task_prompt_path",
        }[key]
        path = self.input_paths[path_key]
        payload = load_strict_json(path)
        mutation(payload)
        payload["review_subject_sha256"] = review_subject_sha256(payload)
        self._rewrite_review_markers(key, payload["review_subject_sha256"])
        payload["review_record"] = _file_reference(
            self.review_path,
            repo_root=self.repo_root,
        )
        _write_json(path, sign_payload(payload))

    def _rewrite_review_markers(self, key: str, subject: str) -> None:
        lines = self.review_path.read_text(encoding="utf-8").splitlines()
        marker = f"PI05_REVIEW_INPUT_KIND: {key}"
        index = lines.index(marker)
        lines[index + 2] = f"PI05_REVIEW_SUBJECT_SHA256: {subject}"
        self.review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        review_ref = _file_reference(
            self.review_path,
            repo_root=self.repo_root,
        )
        for path in self.input_paths.values():
            payload = load_strict_json(path)
            payload["review_record"] = copy.deepcopy(review_ref)
            _write_json(path, sign_payload(payload))


class Pi05ReviewedInputGateTests(unittest.TestCase):
    def test_checked_in_gate_is_signed_blocked_and_nonexecuting(self):
        repo_root = Path(__file__).resolve().parents[2]
        payload = load_strict_json(
            repo_root
            / "configurations/robot_lab/"
            "pi05_reviewed_inputs.blocked_missing_reviewed_inputs.json"
        )
        verify_signed_payload(payload, label="checked-in reviewed-input gate")
        self.assertEqual(
            payload["schema_version"],
            PI05_REVIEWED_INPUT_GATE_SCHEMA_VERSION,
        )
        self.assertEqual(
            payload["identity_sha256"],
            "0f6362f69be4b9083f9bab45828a93f0c1c8e4f04132eed9fc54f8a30e1bfed3",
        )
        self.assertEqual(payload["status"], "blocked_missing_reviewed_inputs")
        self.assertEqual(
            payload["missing_inputs"],
            [
                "accepted_live_session_review_decision",
                "reviewed_stable_camera_role_binding",
                "reviewed_task_prompt",
            ],
        )
        self.assertFalse(payload["production_input_issuance_allowed"])
        self.assertFalse(payload["accepted_live_policy_input"])
        self.assertFalse(payload["policy_input_built"])
        self.assertFalse(payload["preprocessing_run"])
        self.assertFalse(payload["policy_inference_run"])
        self.assertEqual(payload["proof_labels"], [])

    def test_default_builder_is_deterministic_and_all_inputs_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            overrides = {
                "evaluation_time_unix_ns": None,
                "acceptance_decision_path": None,
                "camera_role_binding_path": None,
                "task_prompt_path": None,
            }
            first = fixture.build(**overrides)
            second = fixture.build(**overrides)
            fixture.verify(first, **overrides)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "blocked_missing_reviewed_inputs")
        self.assertEqual(
            first["local_capabilities"],
            ["pi05_reviewed_input_issuance_gate_conformant"],
        )
        self.assertEqual(first["authority_not_granted"], AUTHORITY_NOT_GRANTED)
        self.assertTrue(
            all(not item["present"] for item in first["reviewed_inputs"].values())
        )
        self.assertNotIn(str(Path.home()), json.dumps(first, sort_keys=True))

    def test_complete_fixture_inputs_prove_conformance_not_production(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            payload = fixture.build()
            fixture.verify(payload)
        self.assertEqual(payload["status"], "fixture_inputs_conformant")
        self.assertEqual(payload["missing_inputs"], [])
        self.assertFalse(payload["production_input_issuance_allowed"])
        self.assertFalse(payload["accepted_live_policy_input"])
        self.assertEqual(
            payload["local_capabilities"],
            ["pi05_reviewed_input_issuance_gate_conformant"],
        )
        self.assertEqual(
            {
                item["evidence_class"]
                for item in payload["reviewed_inputs"].values()
            },
            {"deterministic_fixture"},
        )

    def test_complete_production_reviews_grant_bundle_only(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(
                Path(directory).resolve(),
                evidence_class="tracked_production_review",
            )
            payload = fixture.build()
            fixture.verify(payload)
        self.assertEqual(payload["status"], "reviewed_input_bundle_valid")
        self.assertTrue(payload["production_input_issuance_allowed"])
        self.assertFalse(payload["accepted_live_policy_input"])
        self.assertFalse(payload["policy_input_built"])
        self.assertEqual(
            payload["local_capabilities"],
            [
                "pi05_reviewed_input_issuance_gate_conformant",
                "pi05_reviewed_input_bundle_valid",
            ],
        )

    def test_partial_or_mixed_inputs_cannot_promote(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            partial = fixture.build(task_prompt_path=None)
        self.assertEqual(partial["status"], "blocked_missing_reviewed_inputs")
        self.assertEqual(partial["missing_inputs"], ["reviewed_task_prompt"])

        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            fixture.resign_input(
                "reviewed_task_prompt",
                lambda value: value.update(
                    {
                        "evidence_class": "tracked_production_review",
                        "status": "reviewed",
                        "production_eligible": True,
                        "task_prompt_reviewed": True,
                        "local_capabilities": [
                            "pi05_task_prompt_review_valid"
                        ],
                    }
                ),
            )
            with self.assertRaises(ValueError):
                fixture.build()

    def test_rejects_common_authority_identity_scope_and_time_drift(self):
        mutations = (
            ("issuer", lambda value: value.__setitem__("issuer_id", "forged")),
            (
                "scope",
                lambda value: value.__setitem__(
                    "qualification_scope", "global_policy_authority"
                ),
            ),
            (
                "subject",
                lambda value: value.__setitem__(
                    "source_contract_identity_sha256", "f" * 64
                ),
            ),
            (
                "session",
                lambda value: value.__setitem__("session_id", "other-session"),
            ),
            (
                "future",
                lambda value: value.__setitem__(
                    "valid_from_unix_ns", EVALUATION_TIME_NS + 1
                ),
            ),
            (
                "expired",
                lambda value: value.__setitem__(
                    "valid_until_unix_ns", EVALUATION_TIME_NS - 1
                ),
            ),
            (
                "boolean time",
                lambda value: value.__setitem__("issued_at_unix_ns", True),
            ),
            (
                "authority",
                lambda value: value.__setitem__(
                    "accepted_live_policy_input", True
                ),
            ),
            (
                "proof label",
                lambda value: value.__setitem__(
                    "proof_labels", ["policy_shadow_input_valid"]
                ),
            ),
        )
        for label, mutation in mutations:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                fixture = _Fixture(Path(directory).resolve())
                fixture.resign_input(
                    "accepted_live_session_review_decision",
                    mutation,
                )
                with self.assertRaises(ValueError):
                    fixture.build()

    def test_rejects_manifest_camera_and_task_substitution(self):
        cases = (
            (
                "manifest status",
                "accepted_live_session_review_decision",
                self._drift_manifest_status,
            ),
            (
                "duplicate role",
                "reviewed_stable_camera_role_binding",
                lambda value: value["assignments"][1].__setitem__(
                    "source_key", "observation.images.top"
                ),
            ),
            (
                "unknown camera",
                "reviewed_stable_camera_role_binding",
                lambda value: value["assignments"][0].__setitem__(
                    "stable_camera_identity_sha256", "f" * 64
                ),
            ),
            (
                "numeric index",
                "reviewed_stable_camera_role_binding",
                lambda value: value.__setitem__("numeric_camera_index_used", True),
            ),
            (
                "missing private review evidence",
                "reviewed_stable_camera_role_binding",
                lambda value: value.__setitem__(
                    "private_review_evidence_sha256", None
                ),
            ),
            (
                "underscore task",
                "reviewed_task_prompt",
                lambda value: value.__setitem__("task_text", "sort_the_block"),
            ),
            (
                "multiline task",
                "reviewed_task_prompt",
                lambda value: value.__setitem__("task_text", "sort\nthe block"),
            ),
            (
                "non-NFC task",
                "reviewed_task_prompt",
                lambda value: value.__setitem__("task_text", "sort cafe\u0301 block"),
            ),
            (
                "prompt hash",
                "reviewed_task_prompt",
                lambda value: value.__setitem__("prompt_prefix_sha256", "f" * 64),
            ),
        )
        for label, key, mutation in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                fixture = _Fixture(Path(directory).resolve())
                if label == "manifest status":
                    mutation(fixture)
                else:
                    fixture.resign_input(key, mutation)
                with self.assertRaises(ValueError):
                    fixture.build()

    def test_rejects_review_record_and_path_alias_substitution(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            fixture.review_path.write_text("forged\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                fixture.build()

        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            path = fixture.input_paths["camera_role_binding_path"]
            target = path.with_name("camera-real.json")
            path.rename(target)
            path.symlink_to(target)
            with self.assertRaises(ValueError):
                fixture.build()

    def test_verifier_rejects_resigned_gate_escalation(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            payload = fixture.build()
            mutations = (
                lambda value: value.__setitem__(
                    "status", "reviewed_input_bundle_valid"
                ),
                lambda value: value.__setitem__(
                    "production_input_issuance_allowed", True
                ),
                lambda value: value.__setitem__("accepted_live_policy_input", True),
                lambda value: value.__setitem__("policy_input_built", True),
                lambda value: value.__setitem__("model_weights_read", True),
                lambda value: value.__setitem__(
                    "local_capabilities", ["physical_transfer_ready"]
                ),
                lambda value: value.__setitem__("authority_not_granted", []),
                lambda value: value.__setitem__("unexpected_authority", True),
            )
            for mutation in mutations:
                changed = copy.deepcopy(payload)
                mutation(changed)
                with self.assertRaises(ValueError):
                    fixture.verify(sign_payload(changed))

    @staticmethod
    def _drift_manifest_status(fixture: _Fixture) -> None:
        manifest = load_strict_json(fixture.manifest_path)
        manifest["status"] = "accepted"
        _write_json(fixture.manifest_path, sign_payload(manifest))


if __name__ == "__main__":
    unittest.main()

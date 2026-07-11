from __future__ import annotations

import copy
import hashlib
import json
import math
import struct
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
import scenesmith.robot_lab.pi05_preprocessing_contract as contract_module
from scenesmith.robot_lab.pi05_preprocessing_contract import (
    CHECKPOINT_REVISION,
    PI05_PREPROCESSING_SOURCE_CONTRACT_SCHEMA_VERSION,
    TOKENIZER_REVISION,
    build_pi05_preprocessing_source_contract,
    verify_pi05_preprocessing_source_contract,
)


JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]
SOURCE_PATHS = [
    "external/lerobot/src/lerobot/policies/pi05/configuration_pi05.py",
    "external/lerobot/src/lerobot/policies/pi05/modeling_pi05.py",
    "external/lerobot/src/lerobot/policies/pi05/processor_pi05.py",
    "external/lerobot/src/lerobot/processor/relative_action_processor.py",
]
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


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(payload))


def _file_reference(path: Path, *, repo_root: Path) -> dict:
    data = path.read_bytes()
    return {
        "path": path.relative_to(repo_root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }


def _write_safetensors(path: Path, tensors: dict[str, tuple[list[int], list[float]]]) -> None:
    header: dict[str, object] = {}
    data = bytearray()
    for name, (shape, values) in tensors.items():
        start = len(data)
        data.extend(struct.pack(f"<{len(values)}f", *values))
        header[name] = {
            "dtype": "F32",
            "shape": shape,
            "data_offsets": [start, len(data)],
        }
    encoded_header = json.dumps(header, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<Q", len(encoded_header)) + encoded_header + data)


def _normalizer_tensors(
    *,
    width: int = 6,
    state_std: float = 2.0,
    sample_count: float = 100.0,
) -> dict[str, tuple[list[int], list[float]]]:
    return {
        "observation.state.count": ([1], [sample_count]),
        "observation.state.mean": ([width], [float(index) for index in range(width)]),
        "observation.state.std": ([width], [state_std] * width),
        "action.count": ([1], [sample_count]),
        "action.mean": ([width], [float(index + 1) for index in range(width)]),
        "action.std": ([width], [3.0] * width),
    }


def _mutate_safetensors_header(
    encoded: bytes,
    mutation,
    *,
    trailing_data: bytes = b"",
) -> bytes:
    header_length = struct.unpack("<Q", encoded[:8])[0]
    header = json.loads(encoded[8 : 8 + header_length])
    data = encoded[8 + header_length :] + trailing_data
    mutation(header)
    rewritten = json.dumps(
        header,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return struct.pack("<Q", len(rewritten)) + rewritten + data


def _features() -> dict:
    return {
        "observation.images.base_0_rgb": {"type": "VISUAL", "shape": [3, 224, 224]},
        "observation.images.left_wrist_0_rgb": {
            "type": "VISUAL",
            "shape": [3, 224, 224],
        },
        "observation.images.right_wrist_0_rgb": {
            "type": "VISUAL",
            "shape": [3, 224, 224],
        },
        "observation.state": {"type": "STATE", "shape": [32]},
    }


def _checkpoint_config() -> dict:
    return {
        "type": "pi05",
        "input_features": _features(),
        "output_features": {"action": {"type": "ACTION", "shape": [6]}},
        "device": "cuda",
        "dtype": "bfloat16",
        "chunk_size": 50,
        "n_action_steps": 50,
        "max_state_dim": 32,
        "max_action_dim": 32,
        "use_relative_actions": False,
        "relative_exclude_joints": ["gripper"],
        "action_feature_names": [f"{name}.pos" for name in JOINT_NAMES],
        "image_resolution": [224, 224],
        "tokenizer_max_length": 200,
        "normalization_mapping": {
            "ACTION": "MEAN_STD",
            "STATE": "MEAN_STD",
            "VISUAL": "IDENTITY",
        },
    }


def _preprocessor() -> dict:
    return {
        "name": "policy_preprocessor",
        "steps": [
            {
                "registry_name": "rename_observations_processor",
                "config": {
                    "rename_map": {
                        "observation.images.top": "observation.images.base_0_rgb",
                        "observation.images.wrist": (
                            "observation.images.left_wrist_0_rgb"
                        ),
                    }
                },
            },
            {"registry_name": "to_batch_processor", "config": {}},
            {
                "registry_name": "normalizer_processor",
                "config": {
                    "eps": 1e-8,
                    "features": {**_features(), "action": {"type": "ACTION", "shape": [6]}},
                    "norm_map": {
                        "ACTION": "MEAN_STD",
                        "STATE": "MEAN_STD",
                        "VISUAL": "IDENTITY",
                    },
                },
                "state_file": (
                    "policy_preprocessor_step_2_normalizer_processor.safetensors"
                ),
            },
            {"registry_name": "pi05_prepare_state_tokenizer_processor_step", "config": {}},
            {
                "registry_name": "tokenizer_processor",
                "config": {
                    "max_length": 200,
                    "task_key": "task",
                    "padding_side": "right",
                    "padding": "max_length",
                    "truncation": True,
                    "tokenizer_name": "google/paligemma-3b-pt-224",
                },
            },
            {
                "registry_name": "device_processor",
                "config": {"device": "cuda", "float_dtype": None},
            },
        ],
    }


def _postprocessor() -> dict:
    return {
        "name": "policy_postprocessor",
        "steps": [
            {
                "registry_name": "unnormalizer_processor",
                "config": {
                    "eps": 1e-8,
                    "features": {"action": {"type": "ACTION", "shape": [6]}},
                    "norm_map": {
                        "ACTION": "MEAN_STD",
                        "STATE": "MEAN_STD",
                        "VISUAL": "IDENTITY",
                    },
                },
                "state_file": (
                    "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
                ),
            },
            {
                "registry_name": "device_processor",
                "config": {"device": "cpu", "float_dtype": None},
            },
        ],
    }


class _Fixture:
    def __init__(self, root: Path):
        self.repo_root = root / "repo"
        self.cache_root = root / "hub"
        self.repo_root.mkdir()
        self.cache_root.mkdir()
        self._write_repository()
        self._write_checkpoint_cache()
        self._write_tokenizer_cache()

    def _write_repository(self) -> None:
        for index, relative in enumerate(SOURCE_PATHS):
            path = self.repo_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"fixture source {index}\n", encoding="utf-8")
        source_files = [
            _file_reference(self.repo_root / relative, repo_root=self.repo_root)
            for relative in SOURCE_PATHS
        ]
        executable_stack = {
            "schema_version": "scenesmith.lerobot_stack_identity.v1",
            "identity_sha256": "c" * 64,
            "base_revision": "e" * 40,
            "source_root": "external/lerobot/src",
            "processor_contract": {
                "joint_names": JOINT_NAMES,
                "input_units": "radians",
                "lerobot_units": "degrees",
                "tensor_width": 32,
                "padding_value": 0.0,
            },
        }
        lock = sign_payload(
            {
                "schema_version": "scenesmith.robotics_dependency_lock.v2",
                "runtime_contract": {
                    "robot_model": "SO-101",
                    "joint_names": JOINT_NAMES,
                },
                "dependencies": {
                    "local_lerobot_checkout": {
                        "executable_stack": executable_stack,
                        "relevant_sources": {
                            "files": source_files,
                            "relative_paths": [
                                path.replace("external/lerobot/", "")
                                for path in SOURCE_PATHS
                            ],
                            "root": "external/lerobot",
                            "tree_sha256": "d" * 64,
                        },
                    }
                },
            }
        )
        _write_json(
            self.repo_root
            / "configurations/robot_lab/pi05_robotics_dependency_lock.json",
            lock,
        )
        runtime = {
            "schema_version": "scenesmith.lerobot_runtime.v1",
            "base_revision": "e" * 40,
            "source_root": "external/lerobot/src",
            "environment_lock": "external/lerobot/uv.lock",
            "patches": ["scripts/robot_lab/patches/pi05_gripper_loss_weight.patch"],
            "critical_environment": {},
            "processor_contract": copy.deepcopy(executable_stack["processor_contract"]),
            "roles": ["collection", "training", "finalization", "inference", "lelab"],
        }
        _write_json(
            self.repo_root / "configurations/robot_lab/pi05_lerobot_runtime.json",
            runtime,
        )
        joints = []
        static_joints = []
        for index, name in enumerate(JOINT_NAMES, start=1):
            mode = "range_0_100" if name == "gripper" else "degrees"
            units = "normalized_percent" if name == "gripper" else "degrees"
            joints.append(
                {
                    "joint_name": name,
                    "servo_id": index,
                    "normalization": {
                        "mode": mode,
                        "output_units": units,
                    },
                }
            )
            static_joints.append(
                {
                    "joint_name": name,
                    "servo_id": index,
                    "normalization_mode": mode,
                    "coordinate_units": "percent" if name == "gripper" else "degrees",
                }
            )
        calibration = sign_payload(
            {
                "schema_version": "scenesmith.calibration_profile.v1",
                "profile_name": "pi05_follower_arm_calibration_profile",
                "joints": joints,
                "hardware_accessed": False,
                "physical_follower_commanded": False,
            }
        )
        static_contract = sign_payload(
            {
                "schema_version": "scenesmith.static_pose_bracket_contract.v2",
                "contract_name": "pi05_static_pose_bracket_contract",
                "joints": static_joints,
                "cameras": [
                    {"stable_camera_identity_sha256": "a" * 64},
                    {"stable_camera_identity_sha256": "b" * 64},
                ],
                "hardware_accessed": False,
                "physical_follower_commanded": False,
            }
        )
        _write_json(
            self.repo_root / "configurations/robot_lab/pi05_calibration_profile.json",
            calibration,
        )
        _write_json(
            self.repo_root
            / "configurations/robot_lab/pi05_static_pose_bracket_contract.json",
            static_contract,
        )
        _write_json(
            self.repo_root
            / "configurations/robot_lab/pi05_live_readonly_observation.redacted.json",
            sign_payload({"schema_version": "fixture.accepted_manifest.v1"}),
        )
        _write_json(
            self.repo_root / "fixture-private-calibration.json",
            {"fixture": True},
        )

    def _model_root(self, name: str) -> Path:
        return self.cache_root / name

    def _add_cache_file(
        self,
        *,
        model_root: Path,
        revision: str,
        filename: str,
        data: bytes,
    ) -> Path:
        digest = hashlib.sha256(data).hexdigest()
        blob = model_root / "blobs" / digest
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(data)
        snapshot = model_root / "snapshots" / revision
        snapshot.mkdir(parents=True, exist_ok=True)
        link = snapshot / filename
        link.symlink_to(Path("../../blobs") / digest)
        return link

    def _write_checkpoint_cache(self) -> None:
        self.checkpoint_root = self._model_root(
            "models--Cache-SCA--pi05_teleop_sort_block"
        )
        (self.checkpoint_root / "refs").mkdir(parents=True)
        (self.checkpoint_root / "refs/main").write_text(
            CHECKPOINT_REVISION,
            encoding="utf-8",
        )
        self._add_cache_file(
            model_root=self.checkpoint_root,
            revision=CHECKPOINT_REVISION,
            filename="config.json",
            data=_json_bytes(_checkpoint_config()),
        )
        self._add_cache_file(
            model_root=self.checkpoint_root,
            revision=CHECKPOINT_REVISION,
            filename="policy_preprocessor.json",
            data=_json_bytes(_preprocessor()),
        )
        self._add_cache_file(
            model_root=self.checkpoint_root,
            revision=CHECKPOINT_REVISION,
            filename="policy_postprocessor.json",
            data=_json_bytes(_postprocessor()),
        )
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.safetensors"
            _write_safetensors(state, _normalizer_tensors())
            state_bytes = state.read_bytes()
        self.normalizer = self._add_cache_file(
            model_root=self.checkpoint_root,
            revision=CHECKPOINT_REVISION,
            filename=(
                "policy_preprocessor_step_2_normalizer_processor.safetensors"
            ),
            data=state_bytes,
        )
        self._add_cache_file(
            model_root=self.checkpoint_root,
            revision=CHECKPOINT_REVISION,
            filename=(
                "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
            ),
            data=state_bytes,
        )
        self.model_weights = self._add_cache_file(
            model_root=self.checkpoint_root,
            revision=CHECKPOINT_REVISION,
            filename="model.safetensors",
            data=b"MODEL WEIGHTS MUST NOT BE READ",
        )

    def _write_tokenizer_cache(self) -> None:
        self.tokenizer_root = self._model_root(
            "models--google--paligemma-3b-pt-224"
        )
        (self.tokenizer_root / "refs").mkdir(parents=True)
        (self.tokenizer_root / "refs/main").write_text(
            TOKENIZER_REVISION,
            encoding="utf-8",
        )
        files = {
            "added_tokens.json": {},
            "config.json": {"model_type": "paligemma"},
            "special_tokens_map.json": {
                "bos_token": "<bos>",
                "eos_token": "<eos>",
                "pad_token": "<pad>",
                "unk_token": "<unk>",
            },
            "tokenizer.json": {"version": "1.0", "model": {"type": "Unigram"}},
            "tokenizer_config.json": {
                "tokenizer_class": "GemmaTokenizer",
                "bos_token": "<bos>",
                "eos_token": "<eos>",
                "pad_token": "<pad>",
                "unk_token": "<unk>",
            },
        }
        for filename, payload in files.items():
            self._add_cache_file(
                model_root=self.tokenizer_root,
                revision=TOKENIZER_REVISION,
                filename=filename,
                data=_json_bytes(payload),
            )

    def replace_checkpoint_file(self, filename: str, data: bytes) -> None:
        link = self.checkpoint_root / "snapshots" / CHECKPOINT_REVISION / filename
        link.unlink()
        self._add_cache_file(
            model_root=self.checkpoint_root,
            revision=CHECKPOINT_REVISION,
            filename=filename,
            data=data,
        )

    def replace_normalizer(
        self,
        tensors: dict[str, tuple[list[int], list[float]]],
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.safetensors"
            _write_safetensors(path, tensors)
            data = path.read_bytes()
        for filename in (
            "policy_preprocessor_step_2_normalizer_processor.safetensors",
            "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
        ):
            self.replace_checkpoint_file(filename, data)

    def replace_normalizer_bytes(self, data: bytes) -> None:
        for filename in (
            "policy_preprocessor_step_2_normalizer_processor.safetensors",
            "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
        ):
            self.replace_checkpoint_file(filename, data)

    @contextmanager
    def verifier_patches(self):
        with patch.object(
            contract_module,
            "verify_robotics_dependency_lock",
        ), patch.object(
            contract_module,
            "verify_calibration_profile",
        ), patch.object(
            contract_module,
            "verify_static_pose_bracket_contract",
        ):
            yield

    def build(self) -> dict:
        with self.verifier_patches():
            return build_pi05_preprocessing_source_contract(
                repo_root=self.repo_root,
                hf_cache_root=self.cache_root,
                calibration_path=self.repo_root / "fixture-private-calibration.json",
            )

    def verify(self, payload: dict) -> None:
        with self.verifier_patches():
            verify_pi05_preprocessing_source_contract(
                payload,
                repo_root=self.repo_root,
                hf_cache_root=self.cache_root,
                calibration_path=self.repo_root / "fixture-private-calibration.json",
            )


class Pi05PreprocessingContractTests(unittest.TestCase):
    def test_checked_in_contract_is_signed_blocked_and_redacted(self):
        repo_root = Path(__file__).resolve().parents[2]
        payload = load_strict_json(
            repo_root
            / "configurations/robot_lab/"
            "pi05_policy_input_preprocessing.blocked_missing_inputs.json"
        )
        verify_signed_payload(payload, label="checked-in PI0.5 source contract")
        self.assertEqual(
            payload["identity_sha256"],
            "f6b216684f6bb3f895b3d1761d72e80b5e93a5ec7be8f44b04cc277e7a871afa",
        )
        self.assertEqual(payload["status"], "blocked_missing_inputs")
        self.assertFalse(payload["production_preprocessing_allowed"])
        self.assertFalse(payload["policy_input_built"])
        self.assertFalse(payload["model_instantiated"])
        self.assertFalse(payload["model_weights_read"])
        self.assertFalse(payload["preprocessing_run"])
        self.assertFalse(payload["policy_shadow_run"])
        self.assertFalse(payload["policy_inference_run"])
        self.assertFalse(payload["mujoco_replay_run"])
        self.assertFalse(payload["hardware_accessed"])
        self.assertEqual(payload["proof_labels"], [])
        encoded = json.dumps(payload, sort_keys=True)
        self.assertNotIn("model.safetensors", encoded)
        self.assertNotIn(str(Path.home()), encoded)

    def test_builds_deterministic_blocked_contract_without_reading_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            original_hash = contract_module._hash_file
            hashed_paths = []

            def guarded_hash(path: Path) -> str:
                if path.name == "model.safetensors":
                    raise AssertionError("model weights were read")
                hashed_paths.append(path)
                return original_hash(path)

            with patch.object(
                contract_module,
                "_hash_file",
                side_effect=guarded_hash,
            ):
                first = fixture.build()
                second = fixture.build()
                fixture.verify(first)
        self.assertEqual(first, second)
        self.assertEqual(
            first["schema_version"],
            PI05_PREPROCESSING_SOURCE_CONTRACT_SCHEMA_VERSION,
        )
        self.assertEqual(first["status"], "blocked_missing_inputs")
        self.assertFalse(first["production_preprocessing_allowed"])
        self.assertFalse(first["model_instantiated"])
        self.assertFalse(first["model_weights_read"])
        self.assertFalse(first["policy_shadow_run"])
        self.assertFalse(first["network_accessed"])
        self.assertEqual(
            first["local_capabilities"],
            ["pi05_policy_input_preprocessing_source_contract_conformant"],
        )
        self.assertEqual(first["authority_not_granted"], AUTHORITY_NOT_GRANTED)
        self.assertEqual(
            first["missing_inputs"],
            [
                "accepted_live_session_review_decision",
                "reviewed_stable_camera_role_binding",
                "reviewed_task_prompt",
            ],
        )
        self.assertEqual(
            first["effective_preprocessor"]["device_override"],
            {"source": "cuda", "effective": "cpu", "only_mutation": True},
        )
        self.assertEqual(first["coordinate_contract"]["raw_state_width"], 6)
        self.assertEqual(first["coordinate_contract"]["tokenized_state_width"], 6)
        self.assertEqual(
            first["task_contract"]["prompt_template"],
            "Task: {cleaned_task}, State: {discretized_state};\nAction: ",
        )
        self.assertTrue(hashed_paths)
        self.assertNotIn("model.safetensors", json.dumps(first, sort_keys=True))
        self.assertNotIn(str(Path.home()), json.dumps(first, sort_keys=True))

    def test_rejects_source_revision_cache_escape_and_processor_drift(self):
        mutations = (
            (
                "source",
                lambda fixture: (fixture.repo_root / SOURCE_PATHS[0]).write_text(
                    "drift\n", encoding="utf-8"
                ),
            ),
            (
                "revision",
                lambda fixture: (fixture.checkpoint_root / "refs/main").write_text(
                    "0" * 40, encoding="utf-8"
                ),
            ),
            (
                "cache escape",
                self._escape_checkpoint_symlink,
            ),
            (
                "model cache ancestor alias",
                self._alias_checkpoint_model_root,
            ),
            (
                "snapshot ancestor alias",
                self._alias_checkpoint_snapshot,
            ),
            (
                "tracked source ancestor alias",
                self._alias_tracked_source_parent,
            ),
            (
                "processor order",
                self._drift_processor_order,
            ),
            (
                "processor device",
                self._drift_processor_device,
            ),
            (
                "checkpoint config",
                self._drift_checkpoint_config,
            ),
        )
        for label, mutate in mutations:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                fixture = _Fixture(Path(directory).resolve())
                mutate(fixture)
                with self.assertRaises((ValueError, OSError)):
                    fixture.build()

    def test_rejects_malformed_nonfinite_or_wrong_width_safetensors(self):
        cases = (
            ("malformed", None),
            ("wrong width", _normalizer_tensors(width=5)),
            ("zero std", _normalizer_tensors(state_std=0.0)),
            ("nonfinite", _normalizer_tensors(state_std=math.inf)),
            ("fractional count", _normalizer_tensors(sample_count=100.5)),
        )
        for label, tensors in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                fixture = _Fixture(Path(directory).resolve())
                if tensors is None:
                    for filename in (
                        "policy_preprocessor_step_2_normalizer_processor.safetensors",
                        "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
                    ):
                        fixture.replace_checkpoint_file(filename, b"not-safetensors")
                else:
                    fixture.replace_normalizer(tensors)
                with self.assertRaises(ValueError):
                    fixture.build()

    def test_rejects_safetensors_gap_overlap_boolean_shape_and_dtype(self):
        mutations = (
            (
                "trailing gap",
                lambda data: _mutate_safetensors_header(
                    data,
                    lambda header: None,
                    trailing_data=b"x",
                ),
            ),
            (
                "overlap",
                lambda data: _mutate_safetensors_header(
                    data,
                    lambda header: header["action.mean"].__setitem__(
                        "data_offsets",
                        header["observation.state.mean"]["data_offsets"],
                    ),
                ),
            ),
            (
                "boolean shape",
                lambda data: _mutate_safetensors_header(
                    data,
                    lambda header: header["action.mean"].__setitem__(
                        "shape",
                        [True],
                    ),
                ),
            ),
            (
                "boolean dtype",
                lambda data: _mutate_safetensors_header(
                    data,
                    lambda header: header["action.count"].__setitem__(
                        "dtype",
                        "BOOL",
                    ),
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                fixture = _Fixture(Path(directory).resolve())
                source = fixture.normalizer.resolve().read_bytes()
                fixture.replace_normalizer_bytes(mutate(source))
                with self.assertRaises(ValueError):
                    fixture.build()

    def test_rejects_tokenizer_coordinate_and_runtime_semantic_drift(self):
        mutations = (
            ("tokenizer revision", self._drift_tokenizer_revision),
            ("coordinate units", self._drift_coordinate_units),
            ("runtime width", self._drift_runtime_width),
        )
        for label, mutate in mutations:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                fixture = _Fixture(Path(directory).resolve())
                mutate(fixture)
                with self.assertRaises(ValueError):
                    fixture.build()

    def test_verifier_rejects_resigned_blocker_or_authority_escalation(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory).resolve())
            payload = fixture.build()
            mutations = (
                lambda value: value.__setitem__("status", "ready"),
                lambda value: value.__setitem__("production_preprocessing_allowed", True),
                lambda value: value.__setitem__("policy_input_built", True),
                lambda value: value.__setitem__("model_weights_read", True),
                lambda value: value.__setitem__("model_instantiated", True),
                lambda value: value.__setitem__("policy_shadow_run", True),
                lambda value: value.__setitem__(
                    "evidence_mode", "live_physical_observation"
                ),
                lambda value: value.__setitem__(
                    "proof_labels", ["policy_shadow_input_valid"]
                ),
                lambda value: value.__setitem__(
                    "local_capabilities", ["policy_shadow_input_valid"]
                ),
                lambda value: value.__setitem__("missing_inputs", []),
                lambda value: value["camera_contract"].__setitem__(
                    "stable_camera_role_binding", {"forged": True}
                ),
                lambda value: value["task_contract"].__setitem__(
                    "reviewed_task_prompt", "forged"
                ),
                lambda value: value["observation_acceptance_contract"].__setitem__(
                    "accepted_live_review_decision_present", True
                ),
            )
            for mutate in mutations:
                changed = copy.deepcopy(payload)
                mutate(changed)
                with self.assertRaises(ValueError):
                    fixture.verify(sign_payload(changed))

    @staticmethod
    def _escape_checkpoint_symlink(fixture: _Fixture) -> None:
        target = fixture.repo_root / "outside-config.json"
        target.write_bytes(_json_bytes(_checkpoint_config()))
        link = (
            fixture.checkpoint_root
            / "snapshots"
            / CHECKPOINT_REVISION
            / "config.json"
        )
        link.unlink()
        link.symlink_to(target)

    @staticmethod
    def _alias_checkpoint_model_root(fixture: _Fixture) -> None:
        aliased_target = fixture.cache_root / "checkpoint-real"
        fixture.checkpoint_root.rename(aliased_target)
        fixture.checkpoint_root.symlink_to(aliased_target, target_is_directory=True)

    @staticmethod
    def _alias_checkpoint_snapshot(fixture: _Fixture) -> None:
        snapshot = fixture.checkpoint_root / "snapshots" / CHECKPOINT_REVISION
        aliased_target = fixture.checkpoint_root / "snapshot-real"
        snapshot.rename(aliased_target)
        snapshot.symlink_to(aliased_target, target_is_directory=True)

    @staticmethod
    def _alias_tracked_source_parent(fixture: _Fixture) -> None:
        parent = (
            fixture.repo_root
            / "external/lerobot/src/lerobot/policies/pi05"
        )
        aliased_target = parent.parent / "pi05-real"
        parent.rename(aliased_target)
        parent.symlink_to(aliased_target, target_is_directory=True)

    @staticmethod
    def _drift_processor_order(fixture: _Fixture) -> None:
        value = _preprocessor()
        value["steps"][0], value["steps"][1] = value["steps"][1], value["steps"][0]
        fixture.replace_checkpoint_file("policy_preprocessor.json", _json_bytes(value))

    @staticmethod
    def _drift_processor_device(fixture: _Fixture) -> None:
        value = _preprocessor()
        value["steps"][-1]["config"]["device"] = "mps"
        fixture.replace_checkpoint_file("policy_preprocessor.json", _json_bytes(value))

    @staticmethod
    def _drift_checkpoint_config(fixture: _Fixture) -> None:
        value = _checkpoint_config()
        value["chunk_size"] = 49
        fixture.replace_checkpoint_file("config.json", _json_bytes(value))

    @staticmethod
    def _drift_tokenizer_revision(fixture: _Fixture) -> None:
        (fixture.tokenizer_root / "refs/main").write_text(
            "0" * 40,
            encoding="utf-8",
        )

    @staticmethod
    def _drift_coordinate_units(fixture: _Fixture) -> None:
        path = fixture.repo_root / "configurations/robot_lab/pi05_calibration_profile.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["joints"][0]["normalization"]["output_units"] = "radians"
        _write_json(path, sign_payload(value))

    @staticmethod
    def _drift_runtime_width(fixture: _Fixture) -> None:
        path = fixture.repo_root / "configurations/robot_lab/pi05_lerobot_runtime.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["processor_contract"]["tensor_width"] = 31
        _write_json(path, value)


if __name__ == "__main__":
    unittest.main()

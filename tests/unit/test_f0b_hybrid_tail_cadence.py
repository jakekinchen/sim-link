from __future__ import annotations

import copy
import ast
import inspect
import os
import tempfile
import unittest

from pathlib import Path

import numpy as np

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.f0b_hybrid_tail_cadence import (
    ACTChunkDecoder,
    BRANCH,
    CHECKPOINT_IDENTITY,
    DECODE_STARTS,
    EXECUTED_LENGTHS,
    EXPECTED_LEROBOT_VERSION,
    EXPECTED_MUJOCO_VERSION,
    EXPECTED_PYTHON_VERSION,
    EXPECTED_TORCH_VERSION,
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    LEROBOT_CHECKOUT_HEAD,
    LEROBOT_CHECKOUT_TREE,
    SO101_ASSET_TREE_IDENTITY,
    SO_ARM_CHECKOUT_HEAD,
    SO_ARM_CHECKOUT_TREE,
    SELECTED_PREFIX_LENGTHS,
    SMOKE_SCHEMA,
    TRACE_SCHEMA,
    HybridTailQueueAdapter,
    _require_paths_absent,
    _execute_once,
    _tree_identity,
    _verify_terminal_exclusivity,
    _verify_snapshot,
    build_acceptance,
    build_central_authority,
    build_marker,
    build_owner_grant,
    build_spec,
    replay_strict_v2,
    verify_adapter_evidence,
    verify_owner_grant,
    verify_schedule,
    verify_spec,
)
from scenesmith.robot_lab.act_grasp_closed_loop import _evaluate, phase_for_frame
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID


COMMIT = "a" * 40
SHA = "b" * 64
START = "2026-07-17T05:00:00-05:00"
STOP = "2026-07-17T09:30:00-05:00"


class F0bHybridTailCadenceTests(unittest.TestCase):
    def test_frozen_schedule_is_exact_and_complete(self) -> None:
        verify_schedule(
            decode_starts=list(DECODE_STARTS),
            executed_lengths=list(EXECUTED_LENGTHS),
            selected_prefix_lengths=list(SELECTED_PREFIX_LENGTHS),
        )
        self.assertEqual(sum(EXECUTED_LENGTHS), 244)
        self.assertEqual(SELECTED_PREFIX_LENGTHS[3] - EXECUTED_LENGTHS[3], 24)
        self.assertEqual(SELECTED_PREFIX_LENGTHS[-1] - EXECUTED_LENGTHS[-1], 2)
        with self.assertRaises(ValueError):
            verify_schedule(
                decode_starts=list(DECODE_STARTS),
                executed_lengths=[*EXECUTED_LENGTHS[:-1], 9],
                selected_prefix_lengths=list(SELECTED_PREFIX_LENGTHS),
            )

    def test_adapter_discards_exact_frame_150_suffix_and_redecodes_at_176(self) -> None:
        chunks: list[np.ndarray] = []

        def decode(_images, _state):
            ordinal = len(chunks)
            chunk = np.arange(300, dtype=np.float64).reshape(50, 6) + ordinal * 1000
            chunks.append(chunk)
            return chunk

        adapter = HybridTailQueueAdapter(decode)
        actions = [adapter({}, np.zeros(12)) for _ in range(244)]
        terminal = adapter.finalize()
        verify_adapter_evidence(
            decode_rows=adapter.decode_rows,
            discard_events=adapter.discard_events,
            terminal_unexecuted=terminal,
        )
        self.assertEqual(
            [row["decode_start_frame"] for row in adapter.decode_rows],
            list(DECODE_STARTS),
        )
        self.assertEqual(len(chunks), len(DECODE_STARTS))
        np.testing.assert_array_equal(actions[175], chunks[3][25])
        np.testing.assert_array_equal(actions[176], chunks[4][0])
        np.testing.assert_array_equal(
            adapter.discard_events[0]["discarded_action_rows_rad"], chunks[3][26:50]
        )
        np.testing.assert_array_equal(
            terminal["unexecuted_selected_action_rows_rad"], chunks[-1][8:10]
        )

    def test_adapter_rejects_invalid_chunk_and_early_finalize(self) -> None:
        adapter = HybridTailQueueAdapter(lambda _images, _state: np.zeros((49, 6)))
        with self.assertRaises(ValueError):
            adapter({}, np.zeros(12))
        valid = HybridTailQueueAdapter(lambda _images, _state: np.zeros((50, 6)))
        valid({}, np.zeros(12))
        with self.assertRaises(ValueError):
            valid.finalize()
        nonfinite = HybridTailQueueAdapter(
            lambda _images, _state: np.full((50, 6), np.nan)
        )
        with self.assertRaises(ValueError):
            nonfinite({}, np.zeros(12))

    def test_adapter_evidence_rejects_missing_extra_and_23_or_25_action_discard(
        self,
    ) -> None:
        adapter = HybridTailQueueAdapter(lambda _images, _state: np.zeros((50, 6)))
        for _ in range(244):
            adapter({}, np.zeros(12))
        terminal = adapter.finalize()
        for count in (23, 25):
            discard = copy.deepcopy(adapter.discard_events)
            discard[0]["discarded_action_count"] = count
            with self.assertRaises(ValueError):
                verify_adapter_evidence(
                    decode_rows=adapter.decode_rows,
                    discard_events=discard,
                    terminal_unexecuted=terminal,
                )
        for discard in ([], [*adapter.discard_events, *adapter.discard_events]):
            with self.assertRaises(ValueError):
                verify_adapter_evidence(
                    decode_rows=adapter.decode_rows,
                    discard_events=discard,
                    terminal_unexecuted=terminal,
                )

    def test_decoder_actor_input_is_observation_only(self) -> None:
        import torch

        observed_keys = []

        class Policy:
            def predict_action_chunk(self, observation):
                observed_keys.append(sorted(observation))
                return torch.zeros((1, 50, 6), dtype=torch.float32)

        decoder = ACTChunkDecoder(
            policy=Policy(),
            preprocessor=lambda value: value,
            postprocessor=lambda value: value,
            torch=torch,
        )
        chunk = decoder(
            {
                "top": np.zeros((8, 8, 3), dtype=np.uint8),
                "wrist": np.zeros((8, 8, 3), dtype=np.uint8),
            },
            np.zeros(12, dtype=np.float32),
        )
        self.assertEqual(chunk.shape, (50, 6))
        self.assertEqual(
            observed_keys,
            [
                [
                    "observation.images.base_0_rgb",
                    "observation.images.left_wrist_0_rgb",
                    "observation.state",
                ]
            ],
        )

    def test_forged_gate_c_is_rejected_by_independent_replay(self) -> None:
        frames = []
        for index in range(244):
            frames.append(
                {
                    "frame_index": index,
                    "phase": phase_for_frame(index),
                    "pad_contact_aggregate": None,
                    "cube_positions_m": {OBJECT_ID: [0.0, 0.0, 0.1]},
                    "anchor_support_contacts": [],
                    "nonpad_robot_object_contacts": [],
                    "grasp_assists_active": [],
                    "all_robot_object_contact_geoms": [],
                }
            )
        evaluation = _evaluate(
            frames,
            anchor_start=np.asarray([0.0, 0.0, 0.1]),
            anchor_final=np.asarray([0.0, 0.0, 0.1]),
            projected_frames=[],
            release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        )
        closed_loop = sign_payload({"projected_action_frame_indices": [], **evaluation})
        replay_strict_v2(observed_frames=frames, closed_loop=closed_loop)
        forged = copy.deepcopy(closed_loop)
        forged["simulation_semantic_strict_success"] = True
        forged = sign_payload(forged)
        with self.assertRaises(ValueError):
            replay_strict_v2(observed_frames=frames, closed_loop=forged)

    def test_live_spec_binds_checkpoint_and_keeps_all_action_closed(self) -> None:
        spec = build_spec()
        verify_signed_payload(spec, label="F0b test spec")
        self.assertEqual(spec["checkpoint"]["identity_sha256"], CHECKPOINT_IDENTITY)
        self.assertEqual(spec["evaluation"]["decode_starts"], list(DECODE_STARTS))
        self.assertEqual(spec["training_lock"], "closed")
        for field in (
            "checkpoint_tensor_read",
            "model_constructed",
            "model_loaded",
            "model_inference",
            "simulation_rollout",
            "live_rendering",
            "optimizer_created",
            "optimizer_training",
        ):
            self.assertFalse(spec[field])

    def test_resigned_spec_source_or_checkpoint_drift_is_rejected(self) -> None:
        spec = build_spec()
        for field in ("source", "checkpoint"):
            drifted = copy.deepcopy(spec)
            if field == "source":
                drifted["source_refs"][0]["file_sha256"] = "c" * 64
            else:
                drifted["checkpoint"]["identity_sha256"] = "c" * 64
            with self.assertRaises(ValueError):
                verify_spec(sign_payload(drifted))

    def test_owner_and_central_authority_are_single_evaluation_only(self) -> None:
        spec = build_spec()
        owner = build_owner_grant(
            spec=spec,
            required_source_commit=COMMIT,
            valid_from=START,
            valid_until=STOP,
        )
        verify_owner_grant(owner, spec=spec)
        smoke = sign_payload(
            {
                "schema_version": SMOKE_SCHEMA,
                "task_id": "F0b",
                "new_rendering_executed": True,
                "checkpoint_tensor_read": False,
                "model_constructed": False,
                "model_inference": False,
                "simulation_rollout": False,
                "optimizer_created": False,
                "optimizer_training": False,
            }
        )
        request, decision = build_central_authority(spec=spec, owner=owner, smoke=smoke)
        verify_signed_payload(request, label="F0b test request")
        self.assertEqual(decision["authority_granted"], ["simulation_training_ready"])
        self.assertEqual(owner["authorized_attempt_count"], 1)
        self.assertFalse(owner["optimizer_authorized"])
        self.assertFalse(owner["training_authorized"])
        self.assertFalse(owner["retry_authorized"])
        smoke["model_inference"] = True
        with self.assertRaises(ValueError):
            build_central_authority(spec=spec, owner=owner, smoke=sign_payload(smoke))

    def test_live_runner_contains_no_optimizer_dataset_loader_or_training_call(
        self,
    ) -> None:
        tree = ast.parse(inspect.getsource(_execute_once))
        calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        forbidden = {
            "Adam",
            "AdamW",
            "SGD",
            "DataLoader",
            "LeRobotDataset",
            "backward",
            "step",
            "train",
        }
        self.assertTrue(
            forbidden.isdisjoint(calls), sorted(forbidden.intersection(calls))
        )
        self.assertEqual(calls.count("from_pretrained"), 1)

    def test_resigned_owner_optimizer_escalation_is_rejected(self) -> None:
        spec = build_spec()
        owner = build_owner_grant(
            spec=spec,
            required_source_commit=COMMIT,
            valid_from=START,
            valid_until=STOP,
        )
        owner["optimizer_authorized"] = True
        with self.assertRaises(ValueError):
            verify_owner_grant(sign_payload(owner), spec=spec)

    def test_acceptance_and_marker_are_marker_first_and_no_retry(self) -> None:
        permit = sign_payload({"schema_version": "fixture", "task_id": "F0b"})
        acceptance = build_acceptance(
            permit=permit,
            authority_commit=COMMIT,
            reviewer_decision_id="fixture",
            reviewer_path="docs/reviewer-messages/fixture.md",
            reviewer_file_sha256=SHA,
        )
        marker = build_marker(permit=permit, source_commit=COMMIT, started_at=START)
        self.assertFalse(acceptance["checkpoint_tensor_read"])
        self.assertTrue(marker["created_before_checkpoint_tensor_read"])
        self.assertTrue(marker["created_before_model_construction"])
        self.assertTrue(marker["permit_consumed"])
        self.assertFalse(marker["retry_authorized"])

    def test_runtime_snapshot_fails_closed_on_mps_or_version_drift(self) -> None:
        owner = {"required_source_commit": COMMIT}
        smoke = {"identity_sha256": SHA}
        tree = build_spec()["checkpoint"]["tree"]
        snapshot = {
            "branch": BRANCH,
            "head": COMMIT,
            "upstream": COMMIT,
            "required_source_commit": COMMIT,
            "implementation_scoped_paths_clean": True,
            "checkpoint_tree": tree,
            "checkpoint_tree_identity_sha256": _tree_identity(tree),
            "lerobot_checkout_head": LEROBOT_CHECKOUT_HEAD,
            "lerobot_checkout_tree": LEROBOT_CHECKOUT_TREE,
            "so_arm_checkout_head": SO_ARM_CHECKOUT_HEAD,
            "so_arm_checkout_tree": SO_ARM_CHECKOUT_TREE,
            "so101_asset_tree_identity_sha256": SO101_ASSET_TREE_IDENTITY,
            "python_version": EXPECTED_PYTHON_VERSION,
            "torch_version": EXPECTED_TORCH_VERSION,
            "mujoco_version": EXPECTED_MUJOCO_VERSION,
            "lerobot_version": EXPECTED_LEROBOT_VERSION,
            "mps_available": True,
            "runner_interpreter": "external/lerobot/.venv/bin/python",
            "mujoco_support_site_packages": str(
                __import__(
                    "scenesmith.robot_lab.f0b_hybrid_tail_cadence",
                    fromlist=["MUJOCO_SUPPORT_SITE_PACKAGES"],
                ).MUJOCO_SUPPORT_SITE_PACKAGES
            ),
            "renderer_smoke_identity_sha256": SHA,
            "output_paths_absent": True,
            "disk_free_bytes": 2_000_000_000,
            "checkpoint_tensor_deserialized": False,
            "model_constructed": False,
            "model_inference": False,
            "optimizer_created": False,
            "simulation_rollout": False,
        }
        _verify_snapshot(snapshot, owner=owner, smoke=smoke)
        snapshot["mps_available"] = False
        with self.assertRaises(ValueError):
            _verify_snapshot(snapshot, owner=owner, smoke=smoke)

    def test_output_aliases_and_terminal_result_coexistence_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            os.symlink(outside, root / "outputs")
            with self.assertRaises(ValueError):
                _require_paths_absent(root, [Path("outputs/robot_lab/result.json")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "configurations/robot_lab"
            target.mkdir(parents=True)
            (target / "f0b_hybrid_tail_cadence_terminal_failure.json").write_text("{}")
            (target / "f0b_hybrid_tail_cadence_result.json").write_text("{}")
            with self.assertRaises(ValueError):
                _verify_terminal_exclusivity(root)

    def test_renderer_dispatch_has_explicit_f0b_schema_route(self) -> None:
        import importlib.util

        module_path = Path("scripts/robot_lab/render_rollout_mirror_v2.py")
        spec = importlib.util.spec_from_file_location("f0b_renderer_test", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            payload = sign_payload({"schema_version": TRACE_SCHEMA, "task_id": "F0b"})
            dump_canonical_json(path, payload)
            calls = []
            module.verify_f0b_trace = lambda value: calls.append(value)
            result = module.dispatch_trace(
                path,
                legacy_loader=lambda _path: self.fail("legacy route used for F0b"),
            )
            self.assertEqual(result, payload)
            self.assertEqual(calls, [payload])
            source_frames = module.dispatch_source_episode(
                payload,
                0,
                legacy_loader=lambda _seed: self.fail(
                    "legacy source route used for F0b"
                ),
            )
            self.assertEqual(len(source_frames), 244)
            self.assertEqual(source_frames[0]["frame_index"], 0)


if __name__ == "__main__":
    unittest.main()

"""Safety and determinism tests for the SceneSmith intervention loop."""

from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest

from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenesmith.robot_lab import build_so101_desk_sort_scene
from scenesmith.robot_lab.causal_sort_expert import CausalSortExpert
from scenesmith.robot_lab.desk_sort import export_so101_desk_sort_scene
from scenesmith.robot_lab.domain_randomization import (
    apply_mujoco_randomization,
    randomize_scene,
    validate_randomized_scene,
)
from scenesmith.robot_lab.intervention_control import (
    DeadmanSignal,
    InterventionArbiter,
    InterventionControlStore,
)
from scenesmith.robot_lab.intervention_supervisor import (
    CLOSED_GRIPPER_CONTROL,
    EpisodeRunConfig,
    NeuralGraspAssistState,
    _contact_gated_tray_transfer_control,
    _contact_reflex_post_place_control,
    _contact_reflex_release_ready,
    _policy_task_for_remaining_cubes,
    _policy_search_seed,
    _release_neural_grasp_assist_if_open,
    _schedule_contact_reflex_post_place_retreat,
)
from scenesmith.robot_lab.leader_arm_bridge import (
    KNOWN_PHYSICAL_FOLLOWER_PORT,
    PhysicalLeaderArmConfig,
    PhysicalLeaderCorrectionSource,
    _action_to_six_radians,
    _studio_payload_to_six_radians,
)
from scenesmith.robot_lab.policy_action_source import HttpPolicyActionSource
from scenesmith.robot_lab.so101_coordinates import (
    BODY_JOINT_OFFSETS_DEG,
    BODY_JOINT_SIGNS,
    COORDINATE_SCHEMA_VERSION,
    coordinate_contract,
    lerobot_to_mujoco,
    mujoco_to_lerobot,
)
from scripts.robot_lab.local_policy_action_server import (
    _camera_role_for_feature_key,
    _has_cached_adapter_config,
    _lerobot_action_to_mujoco,
    _limit_action_horizon,
    _mujoco_state_to_lerobot,
    _parse_camera_map,
    _parse_five_values,
    _parse_six_values,
    _preprocessor_state_dim,
    _raw_observation_for_policy,
)


DESCRIPTION = "Set up an SO-101 arm on a desk with red and blue trays and cubes."


class DomainRandomizationTests(unittest.TestCase):
    def test_policy_observations_default_to_training_image_geometry(self):
        config = EpisodeRunConfig()

        self.assertEqual((config.observation_width, config.observation_height), (224, 224))

    def test_same_seed_matches_and_many_seeds_remain_valid(self):
        scene = build_so101_desk_sort_scene(DESCRIPTION)
        left, left_manifest = randomize_scene(scene, 4100)
        right, right_manifest = randomize_scene(scene, 4100)

        self.assertEqual(left.to_dict(), right.to_dict())
        self.assertEqual(left_manifest, right_manifest)
        for seed in range(4100, 4200):
            variant, _ = randomize_scene(scene, seed)
            validate_randomized_scene(variant)

    def test_different_seed_changes_geometry_dynamics_and_sensor_samples(self):
        scene = build_so101_desk_sort_scene(DESCRIPTION)
        left, left_manifest = randomize_scene(scene, 4100)
        right, right_manifest = randomize_scene(scene, 4101)

        self.assertNotEqual(left.cubes, right.cubes)
        self.assertNotEqual(left.trays, right.trays)
        self.assertNotEqual(left_manifest["mujoco"], right_manifest["mujoco"])

    def test_manifest_is_applied_to_exported_mujoco_xml(self):
        scene = build_so101_desk_sort_scene(DESCRIPTION)
        variant, manifest = randomize_scene(scene, 4100)
        with tempfile.TemporaryDirectory() as directory:
            proof = export_so101_desk_sort_scene(variant, Path(directory))
            xml_path = Path(proof["artifacts"]["mujoco_xml"])
            before = xml_path.read_text(encoding="utf-8")
            applied = apply_mujoco_randomization(xml_path, manifest)
            after = xml_path.read_text(encoding="utf-8")

        self.assertNotEqual(before, after)
        self.assertEqual(applied["status"], "applied")
        self.assertIn("default_geom_friction", applied)
        self.assertEqual(set(applied["cameras"]), {"cam0_side", "cam1_overhead"})

    def test_causal_expert_tray_slots_are_separated_and_inside_fixture(self):
        scene = build_so101_desk_sort_scene(DESCRIPTION)
        cube = scene.cubes[0]
        tray = next(tray for tray in scene.trays if tray.color == cube.color)
        left = CausalSortExpert._tray_target(tray, cube.side_length_m, 0)
        right = CausalSortExpert._tray_target(tray, cube.side_length_m, 1)

        self.assertGreater(np.linalg.norm(left[:2] - right[:2]), cube.side_length_m)
        for target in (left, right):
            self.assertLessEqual(
                abs(target[0] - tray.center_m[0]) + cube.side_length_m / 2,
                tray.size_m[0] / 2,
            )
            self.assertLessEqual(
                abs(target[1] - tray.center_m[1]) + cube.side_length_m / 2,
                tray.size_m[1] / 2,
            )


class ContactReflexControllerTests(unittest.TestCase):
    def test_followup_task_targets_color_with_more_remaining_cubes(self):
        scene = build_so101_desk_sort_scene(DESCRIPTION).to_dict()
        initial = _policy_task_for_remaining_cubes(scene, set())
        followup = _policy_task_for_remaining_cubes(scene, {"blue_cube_1"})
        next_task = _policy_task_for_remaining_cubes(
            scene, {"blue_cube_1", "red_cube_1"}
        )

        self.assertEqual(
            initial, "Pick up one blue block and place it in the blue plate."
        )
        self.assertEqual(
            followup, "Pick up one red block and place it in the red plate."
        )
        self.assertEqual(
            next_task, "Pick up one blue block and place it in the blue plate."
        )

    def test_completed_task_falls_back_to_general_sort_instruction(self):
        scene = build_so101_desk_sort_scene(DESCRIPTION).to_dict()
        completed = {cube["name"] for cube in scene["cubes"]}

        self.assertEqual(
            _policy_task_for_remaining_cubes(scene, completed),
            "Sort each colored block onto the plate of the matching color.",
        )

    def test_policy_search_seed_walks_around_reproducible_base(self):
        self.assertEqual(
            [_policy_search_seed(6204, index) for index in range(7)],
            [6204, 6203, 6205, 6202, 6206, 6201, 6207],
        )

    def test_release_requires_matching_tray_and_near_surface_height(self):
        cube = {"side_length_m": 0.032}
        tray = {"center_m": [0.35, -0.14, 0.316], "size_m": [0.18, 0.12, 0.012]}
        entry = {"correct": True}

        self.assertFalse(
            _contact_reflex_release_ready(
                entry, cube, tray, np.asarray([0.35, -0.14, 0.438])
            )
        )
        self.assertTrue(
            _contact_reflex_release_ready(
                entry, cube, tray, np.asarray([0.35, -0.14, 0.350])
            )
        )
        self.assertFalse(
            _contact_reflex_release_ready(
                {"correct": False}, cube, tray, np.asarray([0.35, -0.14, 0.350])
            )
        )

    def test_post_place_controller_holds_open_then_reaches_home(self):
        state = NeuralGraspAssistState()
        start = np.asarray([0.4, -1.1, 1.2, 0.3, -0.1, 0.0])
        lift = np.asarray([0.3, -1.3, 1.4, 0.6, -0.08, 1.6])
        home = np.asarray([0.05, -1.7, 1.55, 1.06, -0.05, 1.6])
        _schedule_contact_reflex_post_place_retreat(
            state,
            start,
            lift,
            cube_name="blue_cube_0",
            frame_index=20,
        )

        held, held_phase = _contact_reflex_post_place_control(
            state, home, frame_index=21, hold_steps=2, lift_steps=3, retreat_steps=3
        )
        self.assertEqual(held_phase, "contact_reflex_post_place_hold")
        self.assertEqual(held[:5], tuple(start[:5]))
        self.assertEqual(held[5], 1.6)

        lifted, lifted_phase = _contact_reflex_post_place_control(
            state, home, frame_index=25, hold_steps=2, lift_steps=3, retreat_steps=3
        )
        self.assertEqual(lifted_phase, "contact_reflex_post_place_lift")
        np.testing.assert_allclose(lifted, lift)

        final, final_phase = _contact_reflex_post_place_control(
            state, home, frame_index=28, hold_steps=2, lift_steps=3, retreat_steps=3
        )
        self.assertEqual(final_phase, "contact_reflex_post_place_retreat")
        np.testing.assert_allclose(final, home)

        complete, complete_phase = _contact_reflex_post_place_control(
            state, home, frame_index=29, hold_steps=2, lift_steps=3, retreat_steps=3
        )
        self.assertIsNone(complete)
        self.assertIsNone(complete_phase)
        self.assertEqual(state.post_place_controller_frames, 3)
        self.assertTrue(state.policy_reset_pending)
        self.assertEqual(state.events[-1]["kind"], "post_place_retreat_completed")

    def test_contact_gated_tray_transfer_interpolates_all_phases(self):
        state = NeuralGraspAssistState(
            active_cube="blue_cube_0",
            tray_transfer_start_frame=10,
            tray_transfer_start_control=(0.0, 0.0, 0.0, 0.0, 0.0, -0.17453),
            tray_transfer_lift_control=(1.0, 0.0, 0.0, 0.0, 0.0, -0.17453),
            tray_transfer_carry_control=(1.0, 1.0, 0.0, 0.0, 0.0, -0.17453),
            tray_transfer_place_control=(1.0, 1.0, 1.0, 0.0, 0.0, -0.17453),
        )

        lift, lift_phase = _contact_gated_tray_transfer_control(
            state, frame_index=10, lift_steps=2, carry_steps=2, lower_steps=2
        )
        carry, carry_phase = _contact_gated_tray_transfer_control(
            state, frame_index=12, lift_steps=2, carry_steps=2, lower_steps=2
        )
        lower, lower_phase = _contact_gated_tray_transfer_control(
            state, frame_index=14, lift_steps=2, carry_steps=2, lower_steps=2
        )
        settle, settle_phase = _contact_gated_tray_transfer_control(
            state, frame_index=16, lift_steps=2, carry_steps=2, lower_steps=2
        )

        self.assertEqual(lift_phase, "contact_gated_tray_transfer_lift")
        self.assertEqual(carry_phase, "contact_gated_tray_transfer_carry")
        self.assertEqual(lower_phase, "contact_gated_tray_transfer_lower")
        self.assertEqual(settle_phase, "contact_gated_tray_transfer_settle")
        self.assertLess(lift[0], carry[0] + 1e-9)
        self.assertLess(carry[1], lower[1] + 1e-9)
        self.assertLess(lower[2], settle[2])
        self.assertTrue(
            all(
                action[5] == CLOSED_GRIPPER_CONTROL
                for action in (lift, carry, lower, settle)
            )
        )
        self.assertEqual(state.tray_transfer_controller_frames, 4)


class InterventionArbiterTests(unittest.TestCase):
    def test_fresh_armed_deadman_selects_human_and_records_transition(self):
        arbiter = InterventionArbiter(deadman_timeout_s=0.5)
        policy = [0.0, -0.5, 0.8, -0.4, 0.0, 0.5]
        human = [0.2, -0.3, 0.6, -0.2, 0.1, 0.9]
        signal = DeadmanSignal(True, True, 10.0, 4, "test")

        decision = arbiter.decide(policy, human, signal, now=10.1)

        self.assertTrue(decision.is_intervention)
        self.assertEqual(decision.action_source, "human_leader")
        self.assertEqual(decision.intervention_event, "takeover_started")
        self.assertEqual(decision.executed_action, tuple(human))

    def test_stale_deadman_fails_closed_and_releases_immediately(self):
        arbiter = InterventionArbiter(deadman_timeout_s=0.5)
        policy = [0.0, -0.5, 0.8, -0.4, 0.0, 0.5]
        human = [0.2, -0.3, 0.6, -0.2, 0.1, 0.9]
        arbiter.decide(policy, human, DeadmanSignal(True, True, 10.0, 1, "test"), now=10.1)

        released = arbiter.decide(
            policy,
            human,
            DeadmanSignal(True, True, 10.0, 1, "test"),
            now=10.6,
        )

        self.assertFalse(released.is_intervention)
        self.assertFalse(released.deadman_fresh)
        self.assertEqual(released.action_source, "policy")
        self.assertEqual(released.intervention_event, "takeover_released")

    def test_slew_limit_bounds_takeover_jump(self):
        arbiter = InterventionArbiter(max_delta_per_step=(0.1,) * 6)
        arbiter.decide([0.0] * 6, None, DeadmanSignal(), now=1.0)
        decision = arbiter.decide(
            [0.0] * 6,
            [1.0] * 6,
            DeadmanSignal(True, True, 1.1, 1, "test"),
            now=1.1,
        )
        self.assertEqual(decision.executed_action, (0.1,) * 6)

    def test_malformed_control_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deadman.json"
            path.write_text("not json", encoding="utf-8")
            store = InterventionControlStore(path)
            self.assertEqual(store.read(), DeadmanSignal())
            updated = store.update(armed=True, takeover=True, source="test", now=20.0)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(updated.armed)
        self.assertTrue(updated.takeover)
        self.assertEqual(payload["sequence"], 1)

    def test_neural_grasp_assist_releases_only_when_policy_opens(self):
        calls = []
        mujoco = type(
            "Mujoco",
            (),
            {"mj_forward": lambda _self, _model, _data: calls.append(True)},
        )()
        model = object()
        data = type(
            "Data",
            (),
            {
                "ctrl": np.asarray([0, 0, 0, 0, 0, 0.1], dtype=float),
                "eq_active": np.asarray([1], dtype=int),
                "time": 1.5,
            },
        )()
        state = NeuralGraspAssistState("red_cube_0", 0)

        _release_neural_grasp_assist_if_open(
            mujoco, model, data, state, frame_index=12
        )
        self.assertEqual(state.active_cube, "red_cube_0")
        data.ctrl[5] = 1.0
        _release_neural_grasp_assist_if_open(
            mujoco, model, data, state, frame_index=13
        )

        self.assertIsNone(state.active_cube)
        self.assertEqual(data.eq_active[0], 0)
        self.assertEqual(state.events[-1]["reason"], "policy_opened_gripper")
        self.assertEqual(state.cooldown_until_frame, 28)
        self.assertEqual(calls, [True])


class HttpPolicyActionSourceTests(unittest.TestCase):
    def test_reset_forwards_episode_seed(self):
        source = object.__new__(HttpPolicyActionSource)
        calls = []
        reset_status = {"ok": True, "inference_seed": 6200}
        source._post = lambda path, payload: calls.append((path, payload)) or reset_status

        source.reset(seed=6200)

        self.assertEqual(calls, [("/reset", {"seed": 6200})])
        self.assertEqual(source._status, reset_status)


class LeaderBridgeTests(unittest.TestCase):
    def test_degree_and_gripper_percent_mapping(self):
        action = _action_to_six_radians(
            {
                "shoulder_pan.pos": 90.0,
                "shoulder_lift.pos": -45.0,
                "elbow_flex.pos": 30.0,
                "wrist_flex.pos": -20.0,
                "wrist_roll.pos": 180.0,
                "gripper.pos": 100.0,
            }
        )
        self.assertAlmostEqual(action[0], 1.570796, places=5)
        self.assertAlmostEqual(action[1], -0.785398, places=5)
        self.assertAlmostEqual(action[5], 1.74533, places=5)

    def test_known_non_leader_port_is_rejected_before_hardware_open(self):
        with self.assertRaisesRegex(ValueError, "forbidden non-leader port"):
            PhysicalLeaderCorrectionSource(
                PhysicalLeaderArmConfig(
                    leader_port=KNOWN_PHYSICAL_FOLLOWER_PORT,
                    leader_config="leader_arm",
                    repo_root=Path.cwd(),
                )
            )

    def test_studio_parity_payload_maps_calibrated_leader_only(self):
        action = _studio_payload_to_six_radians(
            {
                "available": True,
                "joints": {
                    "shoulder_pan": {"leaderDeg": 10.0, "followerDeg": 99.0},
                    "shoulder_lift": {"leaderDeg": -20.0, "followerDeg": 99.0},
                    "elbow_flex": {"leaderDeg": 30.0, "followerDeg": 99.0},
                    "wrist_flex": {"leaderDeg": -40.0, "followerDeg": 99.0},
                    "wrist_roll": {"leaderDeg": 50.0, "followerDeg": 99.0},
                    "gripper": {"leaderDeg": 25.0, "followerDeg": 99.0},
                },
            }
        )
        self.assertAlmostEqual(action[0], 0.174533, places=5)
        self.assertAlmostEqual(action[1], -0.349066, places=5)
        self.assertAlmostEqual(action[5], 0.305435, places=5)

    def test_bridge_source_has_no_motor_write_calls(self):
        source_path = Path(__file__).parents[2] / "scenesmith" / "robot_lab" / "leader_arm_bridge.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue({"connect", "sync_read"}.isdisjoint(called_attributes - {"connect"}))
        self.assertTrue(
            {"write", "sync_write", "write_calibration", "configure", "send_feedback"}.isdisjoint(
                called_attributes
            )
        )


class LocalPI05AdapterTests(unittest.TestCase):
    def test_local_peft_adapter_is_detected_without_loading_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            self.assertFalse(_has_cached_adapter_config(str(path)))
            (path / "adapter_config.json").write_text("{}", encoding="utf-8")
            self.assertTrue(_has_cached_adapter_config(str(path)))

    def test_common_camera_names_route_by_semantics(self):
        self.assertEqual(_camera_role_for_feature_key("observation.images.top"), "overhead")
        self.assertEqual(_camera_role_for_feature_key("observation.images.up"), "overhead")
        self.assertEqual(_camera_role_for_feature_key("observation.images.wrist"), "wrist")
        self.assertEqual(_camera_role_for_feature_key("observation.images.front"), "base")

    def test_explicit_camera_map_supports_renames_and_empty_slots(self):
        images = {
            "base": np.full((2, 3, 3), 10, dtype=np.uint8),
            "wrist": np.full((2, 3, 3), 20, dtype=np.uint8),
            "overhead": np.full((2, 3, 3), 30, dtype=np.uint8),
        }
        features = {
            "observation.images.base_0_rgb": {"shape": [3, 2, 3]},
            "observation.images.left_wrist_0_rgb": {"shape": [3, 2, 3]},
            "observation.images.right_wrist_0_rgb": {"shape": [3, 2, 3]},
            "observation.state": {"shape": [6]},
        }
        camera_map = {
            "observation.images.base_0_rgb": "overhead",
            "observation.images.left_wrist_0_rgb": "wrist",
            "observation.images.right_wrist_0_rgb": "empty",
        }
        observation = _raw_observation_for_policy(
            "pi05", images, np.arange(6, dtype=np.float32), features, camera_map
        )

        self.assertTrue(np.all(observation["observation.images.base_0_rgb"] == 30))
        self.assertTrue(np.all(observation["observation.images.left_wrist_0_rgb"] == 20))
        self.assertFalse(np.any(observation["observation.images.right_wrist_0_rgb"]))

    def test_camera_map_and_action_horizon_are_validated(self):
        self.assertEqual(_parse_camera_map('{"observation.images.top":"overhead"}'), {
            "observation.images.top": "overhead"
        })
        with self.assertRaises(ValueError):
            _parse_camera_map('{"observation.images.top":"ceiling"}')
        self.assertEqual(_parse_six_values("[0,1,2,3,4,5]", "home"), [0, 1, 2, 3, 4, 5])
        with self.assertRaises(ValueError):
            _parse_six_values("[0,1]", "home")
        self.assertEqual(_parse_five_values("[1,1,1,1,1]", "body_joint_signs"), [1] * 5)
        with self.assertRaises(ValueError):
            _parse_five_values("[1,0,1,1,1]", "body_joint_signs")

        config = type("Config", (), {"n_action_steps": 50})()
        _limit_action_horizon(config, 5)
        self.assertEqual(config.n_action_steps, 5)
        with self.assertRaises(ValueError):
            _limit_action_horizon(config, 0)

    def test_so101_calibrated_coordinates_round_trip(self):
        mujoco = [0.2, -0.5, 0.8, -0.4, 0.1, 0.6]
        calibrated = _mujoco_state_to_lerobot(mujoco)

        self.assertGreater(calibrated[1], 0.0)
        round_trip = _lerobot_action_to_mujoco(calibrated.tolist())
        np.testing.assert_allclose(round_trip, mujoco, atol=1e-6)

        signs = [1.0] * 5
        offsets = [0.0, -105.85, 89.58, 0.0, 0.0]
        raw = _mujoco_state_to_lerobot(mujoco, signs, offsets)
        custom_round_trip = _lerobot_action_to_mujoco(raw.tolist(), signs, offsets)
        np.testing.assert_allclose(custom_round_trip, mujoco, atol=1e-6)

        canonical = mujoco_to_lerobot(mujoco)
        np.testing.assert_allclose(canonical, calibrated, atol=1e-6)
        np.testing.assert_allclose(lerobot_to_mujoco(canonical), mujoco, atol=1e-6)

    def test_so101_coordinate_contract_is_canonical_and_versioned(self):
        contract = coordinate_contract()

        self.assertEqual(contract["schema_version"], COORDINATE_SCHEMA_VERSION)
        self.assertEqual(contract["body_joint_signs"], list(BODY_JOINT_SIGNS))
        self.assertEqual(contract["body_joint_offsets_deg"], list(BODY_JOINT_OFFSETS_DEG))
        home = mujoco_to_lerobot(
            [0.050438, -1.697719, 1.549157, 1.059675, -0.053182, 1.6]
        )
        self.assertGreater(home[1], 0.0)
        self.assertLess(home[2], 0.0)

    def test_saved_normalizer_controls_raw_state_width(self):
        tensor = type("Tensor", (), {"numel": lambda self: 6})()
        step = type(
            "Normalizer",
            (),
            {"_tensor_stats": {"observation.state": {"mean": tensor}}},
        )()
        preprocessor = type("Preprocessor", (), {"steps": [step]})()

        self.assertEqual(_preprocessor_state_dim(preprocessor, 32), 6)


if __name__ == "__main__":
    unittest.main()

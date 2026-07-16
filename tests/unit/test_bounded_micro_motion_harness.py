from __future__ import annotations

import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.bounded_micro_motion_harness import (
    DeterministicClock,
    DeterministicFixtureTransport,
    build_bounded_micro_motion_plan,
    build_bounded_motion_fixture_result,
    run_injected_bounded_motion_harness,
    verify_bounded_micro_motion_plan,
    verify_bounded_motion_fixture_result,
)


ROOT = Path(__file__).resolve().parents[2]


class BoundedMicroMotionHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_bounded_micro_motion_plan(repo_root=ROOT)

    def test_fixture_runs_subdegree_delta_exact_return_and_torque_off(self) -> None:
        result = build_bounded_motion_fixture_result(repo_root=ROOT)
        self.assertLess(self.plan["delta_degrees"], 1.0)
        self.assertEqual(result["write_count"], 4)
        self.assertEqual(result["torque_change_count"], 2)
        self.assertEqual(result["motion_command_count"], 2)
        self.assertTrue(result["returned_to_baseline"])
        self.assertTrue(result["final_torque_disabled"])
        self.assertFalse(result["hardware_accessed"])
        verify_bounded_motion_fixture_result(result, repo_root=ROOT)

    def test_deadman_failure_before_entry_causes_no_write_and_closes(self) -> None:
        transport = DeterministicFixtureTransport(self.plan)
        with self.assertRaisesRegex(RuntimeError, "deadman"):
            run_injected_bounded_motion_harness(
                plan=self.plan,
                transport=transport,
                deadman=lambda _: False,
                monotonic_ns=DeterministicClock(),
                repo_root=ROOT,
            )
        self.assertEqual(transport.torque, 0)
        self.assertTrue(transport.closed)

    def test_wrong_starting_pose_rejects_before_any_torque(self) -> None:
        transport = DeterministicFixtureTransport(self.plan)
        transport.position += 50
        transport.goal = transport.position
        with self.assertRaisesRegex(ValueError, "starting pose"):
            run_injected_bounded_motion_harness(
                plan=self.plan,
                transport=transport,
                deadman=lambda _: True,
                monotonic_ns=DeterministicClock(),
                repo_root=ROOT,
            )
        self.assertEqual(transport.torque, 0)
        self.assertTrue(transport.closed)

    def test_settle_failure_emergency_returns_and_disables_torque(self) -> None:
        class StuckTransport(DeterministicFixtureTransport):
            def read(self, register: str, servo_id: int) -> int:
                if register == "Present_Position" and self.goal != self.plan["baseline_position_raw"]:
                    return self.plan["baseline_position_raw"]
                return super().read(register, servo_id)

        transport = StuckTransport(self.plan)
        with self.assertRaisesRegex(TimeoutError, "settling"):
            run_injected_bounded_motion_harness(
                plan=self.plan,
                transport=transport,
                deadman=lambda _: True,
                monotonic_ns=DeterministicClock(),
                repo_root=ROOT,
            )
        self.assertEqual(transport.goal, self.plan["baseline_position_raw"])
        self.assertEqual(transport.torque, 0)
        self.assertTrue(transport.closed)

    def test_resigned_plan_or_result_drift_rejects(self) -> None:
        forged_plan = copy.deepcopy(self.plan)
        forged_plan["delta_ticks"] = 9
        forged_plan = sign_payload(
            {key: value for key, value in forged_plan.items() if key != "identity_sha256"}
        )
        with self.assertRaisesRegex(ValueError, "plan drifted"):
            verify_bounded_micro_motion_plan(forged_plan, repo_root=ROOT)
        result = build_bounded_motion_fixture_result(repo_root=ROOT)
        forged_result = copy.deepcopy(result)
        forged_result["hardware_accessed"] = True
        forged_result = sign_payload(
            {key: value for key, value in forged_result.items() if key != "identity_sha256"}
        )
        with self.assertRaisesRegex(ValueError, "result drifted"):
            verify_bounded_motion_fixture_result(forged_result, repo_root=ROOT)


if __name__ == "__main__":
    unittest.main()

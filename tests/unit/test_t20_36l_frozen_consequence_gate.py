import unittest

from copy import deepcopy

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import (
    CALIBRATION_PATH,
    JOINT_NAMES,
    REPO_ROOT,
    RESULT_PATH,
    SPEC_PATH,
    freeze_reach_grasp_thresholds,
    score_act_retained_witness,
    score_smolvla_retained_evidence,
    verify_result,
    verify_spec,
)


class T2036lFrozenConsequenceGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.calibration = load_strict_json(REPO_ROOT / CALIBRATION_PATH)

    def test_frozen_thresholds_reconstruct_only_from_calibration(self) -> None:
        thresholds = freeze_reach_grasp_thresholds(self.calibration)
        self.assertEqual(set(thresholds), {"reach", "grasp"})
        self.assertEqual(set(thresholds["reach"]), set(JOINT_NAMES))
        self.assertEqual(thresholds["reach"]["wrist_roll"], 0.4)
        self.assertEqual(thresholds["reach"]["shoulder_lift"], 0.05)
        self.assertEqual(thresholds["grasp"]["gripper"], 0.025)

    def test_act_retained_witness_conclusively_fails_amended_gate(self) -> None:
        thresholds = freeze_reach_grasp_thresholds(self.calibration)
        localization = load_strict_json(
            REPO_ROOT
            / "configurations/robot_lab/t20_36f_act_decode_localization_result.json"
        )
        run = load_strict_json(
            REPO_ROOT
            / "outputs/robot_lab/t20_36e_exact_act_gate_b_control_run_001/run_summary.json"
        )
        score = score_act_retained_witness(
            localization=localization,
            run=run,
            thresholds=thresholds,
        )
        self.assertEqual(score["action_gate_status"], "fail_with_retained_witness")
        self.assertFalse(score["amended_gate_b_passed"])
        failed = {row["joint_name"] for row in score["failure_witnesses"]}
        self.assertTrue({"shoulder_lift", "wrist_roll", "gripper"} <= failed)

    def test_smolvla_aggregates_fail_closed_without_retained_tensor(self) -> None:
        run = load_strict_json(
            REPO_ROOT
            / "outputs/robot_lab/t20_36j_exact_smolvla_gate_b/run_summary.json"
        )
        score = score_smolvla_retained_evidence(run=run, decoded_tensor=None)
        self.assertEqual(
            score["action_gate_status"],
            "indeterminate_fail_closed_missing_retained_tensor",
        )
        self.assertFalse(score["amended_gate_b_passed"])
        self.assertFalse(score["gate_c_route_open"])

    def test_materialized_spec_and_result_verify_without_authority_escalation(self) -> None:
        spec = load_strict_json(REPO_ROOT / SPEC_PATH)
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_spec(spec)
        verify_result(result, spec=spec)
        self.assertFalse(result["gate_c_authorized"])
        self.assertFalse(result["simulation_policy_accepted"])
        mutation = deepcopy(result)
        mutation["gate_c_authorized"] = True
        mutation = sign_payload(mutation)
        with self.assertRaisesRegex(ValueError, "gate_c_authorized"):
            verify_result(mutation, spec=spec)

    def test_spec_rejects_candidate_dependent_threshold_claim(self) -> None:
        spec = load_strict_json(REPO_ROOT / SPEC_PATH)
        mutation = deepcopy(spec)
        mutation["threshold_derivation"]["candidate_outputs_are_inputs"] = True
        mutation = sign_payload(mutation)
        with self.assertRaisesRegex(ValueError, "candidate"):
            verify_spec(mutation)


if __name__ == "__main__":
    unittest.main()

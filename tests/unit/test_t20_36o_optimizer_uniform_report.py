import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.t20_36o_bounded_optimizer_authority import (
    TRACKED_ATTEMPT_PATH,
    TRAINING_PERMIT_PATH,
    load_verified_sources,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_run import PROBE_TENSOR_PATH
from scenesmith.robot_lab.t20_36o_bounded_optimizer_spec import SPEC_PATH
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (
    SPEC_PATH as BRIDGE_SPEC_PATH,
)
from scenesmith.robot_lab.t20_36o_optimizer_uniform_report import (
    build_uniform_report,
)


RESULT_PATH = Path("configurations/robot_lab/t20_36o_optimizer_result.json")


class T2036oOptimizerUniformReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sources = load_verified_sources()
        cls.attempt = load_strict_json(TRACKED_ATTEMPT_PATH)
        cls.permit = load_strict_json(TRAINING_PERMIT_PATH)
        cls.spec = load_strict_json(SPEC_PATH)
        cls.bridge = load_strict_json(BRIDGE_SPEC_PATH)
        cls.probes = load_strict_json(PROBE_TENSOR_PATH)
        cls.result = load_strict_json(RESULT_PATH)
        cls.baseline = sources["optimizer_sources"]["source_spec"][
            "source_gate_baseline_objective_mean"
        ]

    def test_reports_uniform_metric_without_changing_amended_decision(self) -> None:
        report = build_uniform_report(
            attempt=self.attempt,
            permit=self.permit,
            optimizer_spec=self.spec,
            bridge_spec=self.bridge,
            probe_artifact=self.probes,
            result=self.result,
            source_gate_baseline_objective_mean=self.baseline,
        )
        self.assertFalse(report["selected_strict_uniform_report_only_passed"])
        self.assertFalse(report["unexecuted_tail_scored"])
        self.assertFalse(report["amended_gate_decision_changed"])
        self.assertEqual(report["selected_update_count"], 2500)

    def test_threshold_drift_fails_closed(self) -> None:
        drift = copy.deepcopy(self.bridge)
        drift["acceptance"][
            "strict_uniform_maximum_absolute_error_rad_report_only"
        ] = 0.06
        drift = sign_payload(drift)
        with self.assertRaises(ValueError):
            build_uniform_report(
                attempt=self.attempt,
                permit=self.permit,
                optimizer_spec=self.spec,
                bridge_spec=drift,
                probe_artifact=self.probes,
                result=self.result,
                source_gate_baseline_objective_mean=self.baseline,
            )


if __name__ == "__main__":
    unittest.main()

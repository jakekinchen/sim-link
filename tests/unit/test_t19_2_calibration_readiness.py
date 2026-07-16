from __future__ import annotations

import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.t19_2_calibration_readiness import (
    REQUIRED_PHYSICAL_EVIDENCE,
    build_t19_2_calibration_readiness,
    verify_t19_2_calibration_readiness,
)


ROOT = Path(__file__).resolve().parents[2]


class T192CalibrationReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = load_strict_json(
            ROOT / "docs/autonomous-workflow/project_state.json"
        )

    def test_current_sources_fail_closed_on_all_unmeasured_physical_evidence(self) -> None:
        report = build_t19_2_calibration_readiness(
            repo_root=ROOT, project_state=self.state
        )
        self.assertFalse(report["calibration_session_ready"])
        self.assertFalse(report["motion_authority_ready"])
        self.assertEqual(
            report["missing_prerequisite_ids"], list(REQUIRED_PHYSICAL_EVIDENCE)
        )
        self.assertEqual(
            report["authority_granted"],
            ["t19_2_calibration_readiness_matrix_valid"],
        )
        verify_t19_2_calibration_readiness(
            report, repo_root=ROOT, project_state=self.state
        )

    def test_resigned_positive_readiness_is_rejected(self) -> None:
        report = build_t19_2_calibration_readiness(
            repo_root=ROOT, project_state=self.state
        )
        forged = copy.deepcopy(report)
        forged["calibration_session_ready"] = True
        forged = sign_payload(
            {key: value for key, value in forged.items() if key != "identity_sha256"}
        )
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_t19_2_calibration_readiness(
                forged, repo_root=ROOT, project_state=self.state
            )

    def test_t19_1_state_source_substitution_is_rejected(self) -> None:
        state = copy.deepcopy(self.state)
        state["tasks"]["T19.1"]["artifact"]["identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "T19.1 state/source"):
            build_t19_2_calibration_readiness(repo_root=ROOT, project_state=state)

    def test_camera_review_state_substitution_is_rejected(self) -> None:
        state = copy.deepcopy(self.state)
        state["tasks"]["T16.5c"]["latest_observed_live_candidate"][
            "review_manifest"
        ]["identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "camera review/state"):
            build_t19_2_calibration_readiness(repo_root=ROOT, project_state=state)


if __name__ == "__main__":
    unittest.main()

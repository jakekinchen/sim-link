from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.measured_inertial_intake import (
    DEFAULT_ASSEMBLY_INERTIALS_PATH,
    DEFAULT_MEASURED_MASS_INTAKE_PATH,
    build_assembly_inertials,
    build_measured_mass_intake,
    require_ready_or_raise,
    verify_assembly_inertials,
    verify_measured_mass_intake,
    write_assembly_inertials,
    write_measured_mass_intake,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/robot_lab/write_measured_inertial_intake.py"


class MeasuredInertialIntakeTests(unittest.TestCase):
    def test_build_and_verify_blocked_artifacts(self):
        intake = build_measured_mass_intake(repo_root=REPO_ROOT)
        with tempfile.TemporaryDirectory() as tmpdir:
            intake_path = Path(tmpdir) / "intake.json"
            output_path = Path(tmpdir) / "output.json"
            write_measured_mass_intake(repo_root=REPO_ROOT, output_path=intake_path)
            output = write_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=intake_path,
                output_path=output_path,
            )
            verify_assembly_inertials(output, repo_root=REPO_ROOT, intake_path=intake_path)

        verify_measured_mass_intake(intake, repo_root=REPO_ROOT)

        self.assertEqual(intake["status"], "awaiting_measurements")
        self.assertEqual(output["status"], "blocked_missing_measurements")
        self.assertIsNone(output["aggregate_physical_properties"]["mass_kg"])
        self.assertFalse(output["physical_qualification_authority"])
        self.assertFalse(output["training_or_promotion_authority"])
        self.assertEqual(len(intake["measurements"]), 0)

    def test_checked_in_artifacts_match_deterministic_build(self):
        expected_intake = build_measured_mass_intake(repo_root=REPO_ROOT)
        expected_output = build_assembly_inertials(repo_root=REPO_ROOT)
        observed_intake = json.loads(
            (REPO_ROOT / DEFAULT_MEASURED_MASS_INTAKE_PATH).read_text(encoding="utf-8")
        )
        observed_output = json.loads(
            (REPO_ROOT / DEFAULT_ASSEMBLY_INERTIALS_PATH).read_text(encoding="utf-8")
        )

        self.assertEqual(observed_intake, expected_intake)
        self.assertEqual(observed_output, expected_output)

    def test_runtime_cad_priors_remain_priors_only(self):
        intake = build_measured_mass_intake(repo_root=REPO_ROOT)

        priors = intake["cad_priors"]
        self.assertEqual(len(priors), 7)
        self.assertTrue(all(prior["origin"] == "CAD" for prior in priors))
        self.assertAlmostEqual(
            sum(prior["source_mass_kg"] for prior in priors),
            0.632006,
            places=9,
        )

    def test_verify_rejects_tampered_structural_diff_linkage(self):
        intake = build_measured_mass_intake(repo_root=REPO_ROOT)
        intake["structural_diff_ref"]["identity_sha256"] = "0" * 64
        intake["identity_sha256"] = _resign(intake)

        with self.assertRaisesRegex(ValueError, "Structural diff linkage drifted"):
            verify_measured_mass_intake(intake, repo_root=REPO_ROOT)

    def test_verify_rejects_measurements_in_awaiting_intake(self):
        intake = build_measured_mass_intake(repo_root=REPO_ROOT)
        intake["measurements"] = [{"measurement_id": "fake"}]
        intake["identity_sha256"] = _resign(intake)

        with self.assertRaisesRegex(ValueError, "must not carry measurements"):
            verify_measured_mass_intake(intake, repo_root=REPO_ROOT)

    def test_require_ready_rejects_blocked_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            intake_path = Path(tmpdir) / "intake.json"
            output_path = Path(tmpdir) / "output.json"
            write_measured_mass_intake(repo_root=REPO_ROOT, output_path=intake_path)
            output = write_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=intake_path,
                output_path=output_path,
            )

        with self.assertRaisesRegex(ValueError, "is not ready"):
            require_ready_or_raise(output)

    def test_cli_require_ready_rejects_checked_in_blocked_output(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--verify",
                "--require-ready",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "blocked_missing_measurements")
        self.assertFalse(payload["ready"])


def _resign(payload: dict) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


if __name__ == "__main__":
    unittest.main()

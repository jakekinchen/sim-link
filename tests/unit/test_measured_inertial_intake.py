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

    def test_verify_rejects_resigned_cad_prior_mass_tampering(self):
        intake = build_measured_mass_intake(repo_root=REPO_ROOT)
        intake["cad_priors"][0]["source_mass_kg"] = 99.0
        intake["identity_sha256"] = _resign(intake)

        with self.assertRaisesRegex(ValueError, "drifted from deterministic repo rebuild"):
            verify_measured_mass_intake(intake, repo_root=REPO_ROOT)

    def test_verify_rejects_duplicate_component_ids(self):
        intake = build_measured_mass_intake(repo_root=REPO_ROOT)
        duplicate = json.loads(json.dumps(intake["components"][0]))
        intake["components"].append(duplicate)
        intake["identity_sha256"] = _resign(intake)

        with self.assertRaisesRegex(ValueError, "Duplicate measured mass intake component_id"):
            verify_measured_mass_intake(intake, repo_root=REPO_ROOT)

    def test_write_assembly_inertials_refuses_forged_intake_without_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            intake_path = Path(tmpdir) / "intake.json"
            output_path = Path(tmpdir) / "output.json"
            payload = write_measured_mass_intake(repo_root=REPO_ROOT, output_path=intake_path)
            payload["cad_priors"][0]["source_mass_kg"] = 99.0
            payload["identity_sha256"] = _resign(payload)
            intake_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "drifted from deterministic repo rebuild"):
                write_assembly_inertials(
                    repo_root=REPO_ROOT,
                    intake_path=intake_path,
                    output_path=output_path,
                )

            self.assertFalse(output_path.exists())

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

    def test_cli_supports_external_absolute_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            intake_path = tmp_path / "external-intake.json"
            output_path = tmp_path / "external-output.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--write-intake",
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "written")
            self.assertEqual(payload["intake"], str(intake_path))
            self.assertEqual(payload["output"], str(output_path))
            self.assertTrue(intake_path.exists())
            self.assertTrue(output_path.exists())

    def test_cli_supports_external_absolute_verify(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            intake_path = tmp_path / "external-intake.json"
            output_path = tmp_path / "external-output.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--write-intake",
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--verify",
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "verified")
            self.assertEqual(payload["intake"], str(intake_path))
            self.assertEqual(payload["output"], str(output_path))

    def test_cli_supports_external_absolute_require_ready_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            intake_path = tmp_path / "external-intake.json"
            output_path = tmp_path / "external-output.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--write-intake",
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--verify",
                    "--require-ready",
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "blocked_missing_measurements")
            self.assertEqual(payload["artifact"], str(output_path))
            self.assertFalse(payload["ready"])

    def test_cli_invalid_external_input_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            intake_path = tmp_path / "external-intake.json"
            output_path = tmp_path / "external-output.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--write-intake",
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            original_bytes = output_path.read_bytes()
            intake_payload = json.loads(intake_path.read_text(encoding="utf-8"))
            intake_payload["cad_priors"][0]["source_mass_kg"] = 99.0
            intake_payload["identity_sha256"] = _resign(intake_payload)
            intake_path.write_text(
                json.dumps(intake_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("drifted from deterministic repo rebuild", result.stderr)
            self.assertEqual(output_path.read_bytes(), original_bytes)


def _resign(payload: dict) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


if __name__ == "__main__":
    unittest.main()

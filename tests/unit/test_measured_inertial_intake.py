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
SYNTHETIC_FIXTURE_PATH = REPO_ROOT / "tests/fixtures/robot_lab/measured_mass/synthetic_complete.json"


class MeasuredInertialIntakeTests(unittest.TestCase):
    def _load_synthetic_fixture(self) -> dict:
        return json.loads(SYNTHETIC_FIXTURE_PATH.read_text(encoding="utf-8"))

    def _write_temp_synthetic_fixture(self, tmpdir: str, payload: dict) -> Path:
        fixture_path = Path(tmpdir) / "synthetic-variant.json"
        payload["identity_sha256"] = _resign(payload)
        fixture_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return fixture_path

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

    def test_synthetic_fixture_compiles_ready_with_golden_aggregates(self):
        intake = json.loads(SYNTHETIC_FIXTURE_PATH.read_text(encoding="utf-8"))
        verify_measured_mass_intake(intake, repo_root=REPO_ROOT)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "synthetic-ready.json"
            output = write_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=SYNTHETIC_FIXTURE_PATH,
                output_path=output_path,
            )
            verify_assembly_inertials(
                output,
                repo_root=REPO_ROOT,
                intake_path=SYNTHETIC_FIXTURE_PATH,
            )

        self.assertEqual(output["status"], "ready")
        self.assertEqual(output["qualification_scope"], "synthetic_test_only")
        self.assertEqual(output["aggregate_physical_properties"]["mass_kg"], 4.5)
        self.assertEqual(
            output["aggregate_physical_properties"]["center_of_mass_assembly_frame_m"],
            [0.35, 0.283333333, 0.033333333],
        )
        self.assertEqual(
            output["aggregate_physical_properties"]["inertia_about_com_assembly_frame_kg_m2"],
            [
                [0.073625, -0.053025, 0.26218125],
                [-0.053025, 1.1719375, 0.0126125],
                [0.26218125, 0.0126125, 1.11475],
            ],
        )

    def test_synthetic_ready_identity_is_stable_and_order_invariant(self):
        baseline = build_assembly_inertials(
            repo_root=REPO_ROOT,
            intake_path=SYNTHETIC_FIXTURE_PATH,
        )
        repeat = build_assembly_inertials(
            repo_root=REPO_ROOT,
            intake_path=SYNTHETIC_FIXTURE_PATH,
        )

        self.assertEqual(repeat, baseline)

        with tempfile.TemporaryDirectory() as tmpdir:
            reordered_path = Path(tmpdir) / "synthetic-reordered.json"
            payload = json.loads(SYNTHETIC_FIXTURE_PATH.read_text(encoding="utf-8"))
            payload["components"] = list(reversed(payload["components"]))
            payload["coverage_atoms"] = list(reversed(payload["coverage_atoms"]))
            payload["cad_priors"] = list(reversed(payload["cad_priors"]))
            payload["measurements"] = list(reversed(payload["measurements"]))
            payload["identity_sha256"] = _resign(payload)
            reordered_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            reordered = build_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=reordered_path,
            )

        self.assertEqual(reordered, baseline)
        self.assertEqual(reordered["identity_sha256"], baseline["identity_sha256"])

    def test_synthetic_path_refuses_checked_in_real_destinations(self):
        with self.assertRaisesRegex(ValueError, "cannot write to checked-in real artifact destinations"):
            write_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=SYNTHETIC_FIXTURE_PATH,
                output_path=DEFAULT_ASSEMBLY_INERTIALS_PATH,
            )

        with self.assertRaisesRegex(ValueError, "cannot write to checked-in real artifact destinations"):
            write_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=SYNTHETIC_FIXTURE_PATH,
                output_path=DEFAULT_MEASURED_MASS_INTAKE_PATH,
            )

    def test_cli_synthetic_fixture_reaches_ready_through_bounded_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "synthetic-ready.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake",
                    str(SYNTHETIC_FIXTURE_PATH),
                    "--output",
                    str(output_path),
                    "--require-ready",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "written")
            compiled = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(compiled["status"], "ready")
        self.assertEqual(compiled["qualification_scope"], "synthetic_test_only")

    def test_synthetic_exact_cover_rejects_missing_required_atom(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = self._load_synthetic_fixture()
            payload["measurements"] = [payload["measurements"][0]]
            intake_path = self._write_temp_synthetic_fixture(tmpdir, payload)

            with self.assertRaisesRegex(
                ValueError,
                "Synthetic measurements did not form an exact cover of required atoms",
            ):
                build_assembly_inertials(repo_root=REPO_ROOT, intake_path=intake_path)

    def test_synthetic_exact_cover_rejects_duplicate_active_atom_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = self._load_synthetic_fixture()
            duplicate = json.loads(json.dumps(payload["measurements"][0]))
            duplicate["measurement_id"] = "synthetic_alpha_measurement_duplicate"
            duplicate["evidence"] = [{"kind": "synthetic_scale_reading", "ref": "alpha-scale-duplicate"}]
            payload["measurements"][1] = duplicate
            intake_path = self._write_temp_synthetic_fixture(tmpdir, payload)

            with self.assertRaisesRegex(
                ValueError,
                "Synthetic coverage atom was selected more than once: alpha_structure_mass",
            ):
                build_assembly_inertials(repo_root=REPO_ROOT, intake_path=intake_path)

    def test_synthetic_exact_cover_rejects_ambiguous_multi_atom_measurement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = self._load_synthetic_fixture()
            payload["measurements"][0]["covered_atom_ids"] = [
                "alpha_structure_mass",
                "beta_structure_mass",
            ]
            intake_path = self._write_temp_synthetic_fixture(tmpdir, payload)

            with self.assertRaisesRegex(
                ValueError,
                "Synthetic measurements must cover exactly one atom",
            ):
                build_assembly_inertials(repo_root=REPO_ROOT, intake_path=intake_path)

    def test_synthetic_exact_cover_rejects_reused_measurement_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = self._load_synthetic_fixture()
            payload["measurements"][1]["evidence"] = json.loads(
                json.dumps(payload["measurements"][0]["evidence"])
            )
            intake_path = self._write_temp_synthetic_fixture(tmpdir, payload)

            with self.assertRaisesRegex(
                ValueError,
                "Synthetic measurement evidence was reused: synthetic_beta_measurement",
            ):
                build_assembly_inertials(repo_root=REPO_ROOT, intake_path=intake_path)

    def test_synthetic_exact_cover_rejects_invalid_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = self._load_synthetic_fixture()
            payload["cad_priors"][0]["body_frame_to_assembly"]["rotation_matrix"] = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 2.0],
            ]
            intake_path = self._write_temp_synthetic_fixture(tmpdir, payload)

            with self.assertRaisesRegex(
                ValueError,
                "synthetic_alpha_cad_prior rotation must be orthonormal",
            ):
                build_assembly_inertials(repo_root=REPO_ROOT, intake_path=intake_path)

    def test_synthetic_exact_cover_rejects_invalid_inertia_matrix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = self._load_synthetic_fixture()
            payload["cad_priors"][0]["source_inertia_about_com_body_frame_kg_m2"] = [
                [0.004, 0.0003, 0.0001],
                [0.9, 0.005, 0.0002],
                [0.0001, 0.0002, 0.006],
            ]
            intake_path = self._write_temp_synthetic_fixture(tmpdir, payload)

            with self.assertRaisesRegex(
                ValueError,
                "synthetic_alpha_cad_prior source inertia must be symmetric",
            ):
                build_assembly_inertials(repo_root=REPO_ROOT, intake_path=intake_path)


def _resign(payload: dict) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


if __name__ == "__main__":
    unittest.main()

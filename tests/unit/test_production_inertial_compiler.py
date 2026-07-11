from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.measured_inertial_intake import (
    DEFAULT_ASSEMBLY_INERTIALS_PATH,
    DEFAULT_MEASURED_MASS_INTAKE_PATH,
    build_assembly_inertials,
    verify_assembly_inertials,
    write_assembly_inertials,
)
from scenesmith.robot_lab.production_inertial_compiler import (
    DEFAULT_PRODUCTION_FIXTURE_PATH,
    DEFAULT_PRODUCTION_OUTPUT_FIXTURE_PATH,
    PHYSICAL_EVIDENCE_CLASS,
    PRODUCTION_INPUT_STATUS,
    SOURCE_MODES,
    build_production_fixture,
    compile_production_inertials,
    verify_production_fixture_artifacts,
    verify_production_intake,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
MEASURED_SCRIPT = REPO_ROOT / "scripts/robot_lab/write_measured_inertial_intake.py"
AUTHORITY_SCRIPT = REPO_ROOT / "scripts/robot_lab/compose_robot_authority.py"


class ProductionInertialCompilerTests(unittest.TestCase):
    def _fixture(self) -> dict:
        return json.loads((REPO_ROOT / DEFAULT_PRODUCTION_FIXTURE_PATH).read_text(encoding="utf-8"))

    def test_checked_in_fixture_and_output_match_deterministic_production_build(self):
        artifacts = verify_production_fixture_artifacts(repo_root=REPO_ROOT)
        self.assertEqual(artifacts["intake"], build_production_fixture(repo_root=REPO_ROOT))
        self.assertEqual(
            artifacts["output"],
            compile_production_inertials(artifacts["intake"], repo_root=REPO_ROOT),
        )

    def test_fixture_exercises_hierarchical_exact_cover_and_all_source_modes(self):
        output = compile_production_inertials(self._fixture(), repo_root=REPO_ROOT)

        self.assertEqual(output["qualification_scope"], "fixture_evidence")
        self.assertEqual(output["evidence_class"], "fixture")
        self.assertEqual(set(output["source_mode_counts"]), set(SOURCE_MODES))
        self.assertTrue(all(output["source_mode_counts"][mode] == 1 for mode in SOURCE_MODES))
        self.assertTrue(output["bom"]["acyclic"])
        self.assertTrue(output["bom"]["exact_cover_valid"])
        self.assertTrue(output["bom"]["unique_transform_paths"])
        self.assertEqual(len(output["bom"]["required_leaf_component_ids"]), 7)
        rigid = next(
            item
            for item in output["selected_component_results"]
            if item["source_mode"] == "measured_rigid_assembly"
        )
        self.assertEqual(
            rigid["covered_required_leaf_component_ids"],
            ["finger_left", "finger_right"],
        )
        self.assertEqual(
            output["capabilities"],
            {
                "artifact_schema_valid": True,
                "inertial_compilation_valid": True,
                "inertial_model_usable_for_simulation": True,
                "physical_measurement_evidence_verified": False,
            },
        )

    def test_fixture_has_golden_aggregate_mass_com_and_inertia(self):
        output = compile_production_inertials(self._fixture(), repo_root=REPO_ROOT)
        aggregate = output["aggregate_physical_properties"]

        self.assertEqual(aggregate["mass_kg"], 3.2)
        self.assertEqual(
            aggregate["center_of_mass_target_frame_m"],
            [0.016875, 0.4184375, 0.0],
        )
        self.assertEqual(
            aggregate["inertia_about_com_target_frame_kg_m2"],
            [
                [0.418985520833, 0.051635625, 0.0],
                [0.051635625, 0.020303194444, 0.0],
                [0.0, 0.0, 0.437746493056],
            ],
        )

    def test_output_preserves_raw_si_metrology_derivation_and_provenance(self):
        output = compile_production_inertials(self._fixture(), repo_root=REPO_ROOT)
        cad = next(
            item
            for item in output["selected_component_results"]
            if item["source_mode"] == "cad_scaled"
        )
        trace = cad["source_trace"]

        self.assertEqual(trace["raw_values_native"]["mass"], 1000.0)
        self.assertEqual(trace["native_units"]["mass"], "gram")
        self.assertEqual(trace["canonical_units"]["mass"], "kilogram")
        self.assertEqual(trace["si_values"]["mass_kg"], 1.0)
        self.assertEqual(trace["si_values"]["cad_reference_mass_kg"], 0.9)
        self.assertEqual(trace["derivation"]["mass"], "measured_scale")
        self.assertEqual(trace["derivation"]["center_of_mass"], "cad_reference")
        self.assertEqual(trace["derivation"]["inertia"], "cad_reference_mass_scaled")
        self.assertTrue(trace["provenance"]["device_id"])
        self.assertTrue(trace["provenance"]["calibration_id"])
        self.assertIn("repeatability", trace["metrology_native"])
        self.assertIn("approximation_uncertainty", trace["metrology_si"])
        self.assertTrue(trace["metrology_si"]["inherited_assumptions"])

    def test_same_production_schema_accepts_content_addressed_physical_input_locally(self):
        payload = self._fixture()
        payload["status"] = PRODUCTION_INPUT_STATUS
        payload["evidence_class"] = PHYSICAL_EVIDENCE_CLASS
        with tempfile.TemporaryDirectory() as tmpdir:
            for measurement in payload["measurements"]:
                measurement["evidence_class"] = PHYSICAL_EVIDENCE_CLASS
                evidence_path = Path(tmpdir) / f"{measurement['measurement_id']}.json"
                evidence_payload = {
                    "calibration_id": measurement["provenance"]["calibration_id"],
                    "device_id": measurement["provenance"]["device_id"],
                    "evidence_class": PHYSICAL_EVIDENCE_CLASS,
                    "measurement": measurement["measurement_id"],
                }
                evidence_path.write_text(
                    json.dumps(evidence_payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                measurement["evidence"] = [
                    {
                        "kind": "physical_measurement_record",
                        "ref": str(evidence_path),
                        "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                    }
                ]
            output = compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

        self.assertEqual(output["qualification_scope"], "physical_measurement_evidence")
        self.assertTrue(output["capabilities"]["physical_measurement_evidence_verified"])
        self.assertNotIn("simulation_training_ready", output)
        self.assertNotIn("physical_transfer_ready", output)
        self.assertNotIn("promotion_eligible", output)

    def test_production_compilation_is_input_list_order_invariant(self):
        baseline = compile_production_inertials(self._fixture(), repo_root=REPO_ROOT)
        reordered = self._fixture()
        reordered["components"].reverse()
        reordered["measurements"].reverse()
        for measurement in reordered["measurements"]:
            measurement["evidence"].reverse()
        reordered = _resign(reordered)

        self.assertEqual(
            compile_production_inertials(reordered, repo_root=REPO_ROOT),
            baseline,
        )

    def test_subnanometer_transform_contribution_survives_until_final_serialization(self):
        baseline = compile_production_inertials(self._fixture(), repo_root=REPO_ROOT)
        payload = self._fixture()
        component = _component(payload, "point_payload")
        component["transform_to_parent"]["translation"][0] += 1.23e-10
        changed = compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

        self.assertNotEqual(
            changed["aggregate_physical_properties"]["center_of_mass_target_frame_m"],
            baseline["aggregate_physical_properties"]["center_of_mass_target_frame_m"],
        )

    def test_missing_measurement_fails_exact_required_leaf_cover(self):
        payload = self._fixture()
        payload["measurements"] = [
            item for item in payload["measurements"] if item["source_mode"] != "point_mass"
        ]
        with self.assertRaisesRegex(ValueError, "exact required-leaf cover"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_selected_ancestor_and_descendant_are_rejected_before_double_counting(self):
        payload = self._fixture()
        extra = copy.deepcopy(
            next(item for item in payload["measurements"] if item["source_mode"] == "point_mass")
        )
        extra["measurement_id"] = "fixture_forbidden_finger_leaf"
        extra["component_id"] = "finger_left"
        payload["measurements"].append(extra)

        with self.assertRaisesRegex(ValueError, "ancestor and descendant"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_overlap_from_two_nonancestor_measurements_is_rejected(self):
        payload = self._fixture()
        rigid = next(
            item
            for item in payload["measurements"]
            if item["source_mode"] == "measured_rigid_assembly"
        )
        rigid["component_id"] = "wrist_group"
        with self.assertRaisesRegex(ValueError, "ancestor and descendant|overlap"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_bom_rejects_multiple_roots_unknown_parent_cycle_and_duplicate_frame(self):
        cases = {
            "exactly one declared root": lambda payload: _component(payload, "base_group").update(
                {"parent_component_id": None, "transform_to_parent": None}
            ),
            "parent is unknown": lambda payload: _component(payload, "base_group").update(
                {"parent_component_id": "missing_parent"}
            ),
            "cycle detected": lambda payload: _component(payload, "base_group").update(
                {"parent_component_id": "point_payload"}
            ),
            "Duplicate production BOM frame_id": lambda payload: _component(
                payload, "point_payload"
            ).update({"frame_id": "cad_link_frame"}),
        }
        for expected, mutate in cases.items():
            with self.subTest(expected=expected):
                payload = self._fixture()
                mutate(payload)
                with self.assertRaisesRegex(ValueError, expected):
                    compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_missing_transform_and_required_nonleaf_are_rejected(self):
        payload = self._fixture()
        _component(payload, "point_payload")["transform_to_parent"] = None
        with self.assertRaisesRegex(ValueError, "transform_to_parent is malformed"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

        payload = self._fixture()
        _component(payload, "gripper_assembly")["required_leaf"] = True
        with self.assertRaisesRegex(ValueError, "is not a leaf"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_scale_reading_cannot_claim_com_or_inertia_derivation(self):
        payload = self._fixture()
        cad = _measurement(payload, "cad_scaled")
        cad["derivation"]["center_of_mass"] = "measured_scale"
        with self.assertRaisesRegex(ValueError, "derivation drifted"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_units_device_calibration_and_metrology_are_mandatory(self):
        cases = {
            "Unsupported production mass unit": lambda item: item["native_units"].update(
                {"mass": "pound"}
            ),
            "calibration_id must be nonblank": lambda item: item["provenance"].update(
                {"calibration_id": " "}
            ),
            "inherited assumptions are required": lambda item: item["metrology"].update(
                {"inherited_assumptions": []}
            ),
            "metrology must be nonnegative": lambda item: item["metrology"][
                "uncertainty"
            ].update({"mass": -1.0}),
        }
        for expected, mutate in cases.items():
            with self.subTest(expected=expected):
                payload = self._fixture()
                mutate(payload["measurements"][0])
                with self.assertRaisesRegex(ValueError, expected):
                    compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_evidence_reuse_and_substitution_are_rejected(self):
        payload = self._fixture()
        payload["measurements"][1]["evidence"] = copy.deepcopy(
            payload["measurements"][0]["evidence"]
        )
        with self.assertRaisesRegex(ValueError, "evidence was reused"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

        payload = self._fixture()
        payload["measurements"][0]["evidence"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "evidence hash drifted"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

        payload = self._fixture()
        payload["measurements"][0]["provenance"]["calibration_id"] = "substituted-calibration"
        with self.assertRaisesRegex(ValueError, "evidence calibration mismatch"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_nonfinite_intermediate_overflow_fails_closed(self):
        payload = self._fixture()
        point = _measurement(payload, "point_mass")
        point["raw_values"]["mass"] = 1e308
        point["raw_values"]["center_of_mass"] = [1e308, 0.0, 0.0]
        with self.assertRaisesRegex(ValueError, "non-finite result"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_resigned_forged_global_authority_field_is_rejected(self):
        payload = self._fixture()
        payload["authority"] = {"physical_transfer_ready": True}
        with self.assertRaisesRegex(ValueError, "forbidden global-authority fields"):
            compile_production_inertials(_resign(payload), repo_root=REPO_ROOT)

    def test_fixture_cannot_overwrite_checked_in_current_arm_artifacts(self):
        for output_path in (
            DEFAULT_MEASURED_MASS_INTAKE_PATH,
            DEFAULT_ASSEMBLY_INERTIALS_PATH,
        ):
            with self.subTest(output_path=output_path), self.assertRaisesRegex(
                ValueError, "cannot write to checked-in real artifact destinations"
            ):
                write_assembly_inertials(
                    repo_root=REPO_ROOT,
                    intake_path=DEFAULT_PRODUCTION_FIXTURE_PATH,
                    output_path=output_path,
                )

    def test_integrated_measured_cli_and_verifier_use_production_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "production-output.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(MEASURED_SCRIPT),
                    "--intake",
                    str(DEFAULT_PRODUCTION_FIXTURE_PATH),
                    "--output",
                    str(output_path),
                    "--require-compilation-ready",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            output = json.loads(output_path.read_text(encoding="utf-8"))
            verify_assembly_inertials(
                output,
                repo_root=REPO_ROOT,
                intake_path=DEFAULT_PRODUCTION_FIXTURE_PATH,
            )
            self.assertEqual(
                output,
                build_assembly_inertials(
                    repo_root=REPO_ROOT,
                    intake_path=DEFAULT_PRODUCTION_FIXTURE_PATH,
                ),
            )

    def test_fixture_component_cannot_grant_global_authority_through_cli(self):
        result = subprocess.run(
            [
                sys.executable,
                str(AUTHORITY_SCRIPT),
                "--intake",
                str(DEFAULT_PRODUCTION_FIXTURE_PATH),
                "--inertial-artifact",
                str(DEFAULT_PRODUCTION_OUTPUT_FIXTURE_PATH),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["authority_granted"], [])
        self.assertEqual(
            decision["authority_withheld"],
            [
                "simulation_training_ready",
                "physical_transfer_ready",
                "promotion_eligible",
            ],
        )

    def test_current_arm_remains_blocked_and_unchanged_by_fixture_path(self):
        current = build_assembly_inertials(repo_root=REPO_ROOT)
        verify_assembly_inertials(current, repo_root=REPO_ROOT)
        fixture = compile_production_inertials(self._fixture(), repo_root=REPO_ROOT)

        self.assertEqual(current["status"], "blocked_missing_measurements")
        self.assertFalse(current["capabilities"]["inertial_compilation_valid"])
        self.assertEqual(fixture["qualification_scope"], "fixture_evidence")
        self.assertFalse(fixture["capabilities"]["physical_measurement_evidence_verified"])


def _component(payload: dict, component_id: str) -> dict:
    return next(item for item in payload["components"] if item["component_id"] == component_id)


def _measurement(payload: dict, source_mode: str) -> dict:
    return next(item for item in payload["measurements"] if item["source_mode"] == source_mode)


def _resign(payload: dict) -> dict:
    unsigned = copy.deepcopy(payload)
    unsigned.pop("identity_sha256", None)
    return sign_payload(unsigned)


if __name__ == "__main__":
    unittest.main()

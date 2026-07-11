from __future__ import annotations

import copy
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, sign_payload
from scenesmith.robot_lab.computed_twin_qualification import (
    DEFAULT_COMPUTED_QUALIFICATION_INPUT_PATH,
    DEFAULT_COMPUTED_QUALIFICATION_REPORT_PATH,
    DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH,
    DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS,
    build_fixture_metric_evidence,
    build_qualification_input,
    compose_qualification_authority,
    generate_computed_qualification_report,
    qualification_evidence_issuer,
    verify_computed_qualification_report,
    verify_computed_qualification_spec,
    verify_metric_evidence,
    verify_qualification_fixture_artifacts,
    verify_qualification_input,
)
from scenesmith.robot_lab.twin_contract import (
    build_twin_contract_examples,
    verify_twin_qualification_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class ComputedTwinQualificationTests(unittest.TestCase):
    def _bundle(self) -> dict:
        return verify_qualification_fixture_artifacts(repo_root=REPO_ROOT)

    def test_checked_in_fixture_is_computed_but_cannot_grant_authority(self):
        bundle = self._bundle()
        report = bundle["report"]

        self.assertEqual(
            report["capabilities"],
            {
                "held_out_twin_metrics_passed": False,
                "required_simulation_properties_available": False,
                "twin_qualification_computation_valid": True,
            },
        )
        self.assertTrue(
            all(metric["tolerance_status"] == "pass" for metric in report["metrics"])
        )
        self.assertTrue(
            all(metric["qualification_status"] == "withheld" for metric in report["metrics"])
        )
        self.assertEqual(bundle["decision"]["authority_granted"], [])
        self.assertEqual(
            bundle["decision"]["authority_withheld"],
            [
                "simulation_training_ready",
                "physical_transfer_ready",
                "promotion_eligible",
            ],
        )
        self.assertEqual(
            {claim["value"] for claim in bundle["claims"]},
            {False},
        )

    def test_generator_and_independent_verifier_reject_report_drift(self):
        bundle = self._bundle()
        report = bundle["report"]
        qualification_input = bundle["input"]
        mutations = (
            ("aggregate", lambda value: value["metrics"][0].__setitem__("aggregate_value", 0.0)),
            ("decision", lambda value: value["metrics"][0].__setitem__("decision_value", 0.0)),
            ("tolerance", lambda value: value["metrics"][0]["tolerance"].__setitem__("max_value", 99.0)),
            ("status", lambda value: value["metrics"][0].__setitem__("qualification_status", "pass")),
            ("reasons", lambda value: value["metrics"][0].__setitem__("reason_codes", [])),
            (
                "capability",
                lambda value: value["capabilities"].__setitem__(
                    "required_simulation_properties_available",
                    True,
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(report)
                mutate(changed)
                changed = sign_payload(changed)
                with self.assertRaisesRegex(ValueError, "recomputation|drifted"):
                    verify_computed_qualification_report(
                        changed,
                        qualification_input=qualification_input,
                        repo_root=REPO_ROOT,
                    )

    def test_caller_declared_status_is_rejected_at_every_input_boundary(self):
        bundle = self._bundle()
        evidence = copy.deepcopy(next(iter(bundle["evidence"].values())))
        evidence["status"] = "pass"
        evidence = sign_payload(evidence)
        with self.assertRaisesRegex(ValueError, "fields|status"):
            verify_metric_evidence(
                evidence,
                spec=bundle["spec"],
                evaluation_time=bundle["input"]["evaluation_time"],
                composition_mode="fixture",
            )

        qualification_input = copy.deepcopy(bundle["input"])
        qualification_input["status"] = "pass"
        qualification_input = sign_payload(qualification_input)
        with self.assertRaisesRegex(ValueError, "fields|status"):
            verify_qualification_input(qualification_input, repo_root=REPO_ROOT)

    def test_metric_evidence_rejects_bad_samples_units_conditions_and_uncertainty(self):
        bundle = self._bundle()
        base = copy.deepcopy(bundle["evidence"]["sim_joint_limit_projection_error"])
        mutations = (
            ("nonfinite", lambda value: value["samples"][0].__setitem__("value", "NaN"), "finite"),
            ("negative", lambda value: value["samples"][0].__setitem__("value", -0.01), "minimum"),
            ("sample_count", lambda value: value.__setitem__("declared_sample_count", 99), "sample count"),
            ("trajectory_ids", lambda value: value.__setitem__("held_out_trajectory_ids", ["wrong"]), "trajectory"),
            ("units", lambda value: value.__setitem__("units", "degree"), "units"),
            ("condition", lambda value: value["conditions"][0].__setitem__("value", 1.0), "condition"),
            ("uncertainty", lambda value: value["uncertainty"].__setitem__("value", -1.0), "uncertainty"),
            ("confidence", lambda value: value["uncertainty"].__setitem__("confidence_level", 0.0), "confidence"),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(base)
                mutate(changed)
                changed = sign_payload(changed)
                with self.assertRaisesRegex(ValueError, message):
                    verify_metric_evidence(
                        changed,
                        spec=bundle["spec"],
                        evaluation_time=bundle["input"]["evaluation_time"],
                        composition_mode="fixture",
                    )

    def test_fixture_evidence_cannot_impersonate_physical_evidence(self):
        bundle = self._bundle()
        evidence = copy.deepcopy(bundle["evidence"]["physical_gripper_contact_latency"])
        evidence["qualification_scope"] = "physical_evidence"
        evidence["provenance_class"] = "physical"
        evidence["evidence_mode"] = "physical_run"
        evidence = sign_payload(evidence)
        with self.assertRaisesRegex(ValueError, "issuer|fixture composition"):
            verify_metric_evidence(
                evidence,
                spec=bundle["spec"],
                evaluation_time=bundle["input"]["evaluation_time"],
                composition_mode="fixture",
            )

        evidence["issuer"] = qualification_evidence_issuer("physical")
        evidence = sign_payload(evidence)
        with self.assertRaisesRegex(ValueError, "fixture composition"):
            verify_metric_evidence(
                evidence,
                spec=bundle["spec"],
                evaluation_time=bundle["input"]["evaluation_time"],
                composition_mode="fixture",
            )
        with self.assertRaisesRegex(ValueError, "Fixture-path"):
            verify_metric_evidence(
                evidence,
                spec=bundle["spec"],
                evaluation_time=bundle["input"]["evaluation_time"],
                composition_mode="production",
                artifact_path=DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS[
                    "physical_gripper_contact_latency"
                ],
            )

    def test_resigned_spec_cannot_loosen_code_pinned_evidence_rules(self):
        bundle = self._bundle()
        spec = copy.deepcopy(bundle["spec"])
        simulation_rule = next(
            item
            for item in spec["metric_rules"]
            if item["metric_id"] == "sim_joint_limit_projection_error"
        )
        simulation_rule["required_evidence_modes"].append("fixture_trace")
        simulation_rule["required_evidence_modes"].sort()
        spec = sign_payload(spec)
        with self.assertRaisesRegex(ValueError, "code-pinned"):
            verify_computed_qualification_spec(spec, repo_root=REPO_ROOT)

    def test_simulation_profile_does_not_preauthorize_physical_report(self):
        bundle = self._bundle()
        qualification_input = copy.deepcopy(bundle["input"])
        qualification_input["requested_proof_state"] = "physical_qualified"
        qualification_input = sign_payload(qualification_input)
        with self.assertRaisesRegex(ValueError, "profile.*does not pre-authorize"):
            verify_qualification_input(qualification_input, repo_root=REPO_ROOT)

    def test_stale_refs_substitution_and_expired_input_fail_closed(self):
        bundle = self._bundle()
        mutations = (
            (
                "profile",
                lambda value: value["profile_ref"].__setitem__("identity_sha256", "0" * 64),
                "profile|linkage",
            ),
            (
                "spec",
                lambda value: value["spec_ref"].__setitem__("file_sha256", "0" * 64),
                "spec|linkage",
            ),
            (
                "evidence",
                lambda value: value["metric_evidence_refs"][0]["artifact_ref"].__setitem__(
                    "identity_sha256",
                    "0" * 64,
                ),
                "evidence|linkage",
            ),
            (
                "expired",
                lambda value: value["validity"].__setitem__(
                    "valid_until",
                    "2026-07-11T02:13:00-05:00",
                ),
                "expired|validity",
            ),
            (
                "extended",
                lambda value: value["validity"].update(
                    {
                        "valid_until": "2026-07-13T02:10:00-05:00",
                        "max_age_seconds": 172800,
                    }
                ),
                "code-pinned maximum",
            ),
            (
                "freshness_substitution",
                lambda value: value["validity"].__setitem__(
                    "observed_at",
                    "2026-07-11T02:11:00-05:00",
                ),
                "freshness does not match",
            ),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(bundle["input"])
                mutate(changed)
                changed = sign_payload(changed)
                with self.assertRaisesRegex(ValueError, message):
                    verify_qualification_input(changed, repo_root=REPO_ROOT)

    def test_missing_optional_metric_is_explicitly_not_run(self):
        qualification_input = build_qualification_input(
            repo_root=REPO_ROOT,
            spec_path=DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH,
            metric_evidence_paths=[
                DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS[
                    "sim_joint_limit_projection_error"
                ]
            ],
            composition_mode="fixture",
        )
        report = generate_computed_qualification_report(
            qualification_input,
            repo_root=REPO_ROOT,
        )
        physical = next(
            metric
            for metric in report["metrics"]
            if metric["metric_id"] == "physical_gripper_contact_latency"
        )
        self.assertEqual(physical["qualification_status"], "not_run")
        self.assertEqual(physical["reason_codes"], ["METRIC_NOT_RUN"])
        verify_computed_qualification_report(
            report,
            qualification_input=qualification_input,
            repo_root=REPO_ROOT,
        )

    def test_missing_required_metric_is_withheld_not_inferred(self):
        qualification_input = build_qualification_input(
            repo_root=REPO_ROOT,
            metric_evidence_paths=[
                DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS[
                    "physical_gripper_contact_latency"
                ]
            ],
            composition_mode="fixture",
        )
        report = generate_computed_qualification_report(
            qualification_input,
            repo_root=REPO_ROOT,
        )
        self.assertEqual(
            report["summary"]["not_run_metric_ids"],
            ["sim_joint_limit_projection_error"],
        )
        self.assertFalse(report["summary"]["all_required_metrics_passed"])
        self.assertFalse(
            report["capabilities"]["required_simulation_properties_available"]
        )

    def test_ephemeral_production_shape_computes_boundary_without_global_grant(self):
        with tempfile.TemporaryDirectory(
            dir=REPO_ROOT / "configurations" / "robot_lab"
        ) as tmpdir:
            evidence_path = Path(tmpdir) / "simulation-evidence.json"
            relative_path = evidence_path.relative_to(REPO_ROOT)
            for sample_value, expected_status in ((0.048, "pass"), (0.049, "fail")):
                with self.subTest(sample_value=sample_value):
                    evidence = build_fixture_metric_evidence(
                        "sim_joint_limit_projection_error"
                    )
                    evidence["qualification_scope"] = "simulation_evidence"
                    evidence["provenance_class"] = "simulation"
                    evidence["evidence_mode"] = "simulation_trace"
                    evidence["issuer"] = qualification_evidence_issuer("simulation")
                    evidence["samples"][-1]["value"] = sample_value
                    evidence = sign_payload(evidence)
                    dump_canonical_json(evidence_path, evidence)
                    qualification_input = build_qualification_input(
                        repo_root=REPO_ROOT,
                        metric_evidence_paths=[relative_path],
                        composition_mode="production",
                    )
                    report = generate_computed_qualification_report(
                        qualification_input,
                        repo_root=REPO_ROOT,
                    )
                    simulation = next(
                        item
                        for item in report["metrics"]
                        if item["metric_id"] == "sim_joint_limit_projection_error"
                    )
                    self.assertEqual(simulation["qualification_status"], expected_status)
                    self.assertEqual(
                        report["capabilities"][
                            "required_simulation_properties_available"
                        ],
                        expected_status == "pass",
                    )
                    authority = compose_qualification_authority(
                        report,
                        qualification_input=qualification_input,
                        repo_root=REPO_ROOT,
                    )
                    self.assertEqual(authority["decision"]["authority_granted"], [])

    def test_sample_identity_time_and_minimum_counts_fail_closed(self):
        bundle = self._bundle()
        base = bundle["evidence"]["sim_joint_limit_projection_error"]
        mutations = (
            (
                "duplicate_sample",
                lambda value: value["samples"][1].__setitem__(
                    "sample_id",
                    value["samples"][0]["sample_id"],
                ),
                "Duplicate qualification sample_id",
            ),
            (
                "too_few_samples",
                lambda value: (
                    value["samples"].pop(),
                    value.__setitem__("declared_sample_count", 2),
                ),
                "below the spec",
            ),
            (
                "future_sample",
                lambda value: value["samples"][0].__setitem__(
                    "observed_at",
                    "2026-07-11T02:15:00-05:00",
                ),
                "after evaluation",
            ),
            (
                "wrong_subject",
                lambda value: value.__setitem__("subject_id", "other_robot"),
                "subject",
            ),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(base)
                mutate(changed)
                changed["samples"].sort(key=lambda item: item["sample_id"])
                changed = sign_payload(changed)
                with self.assertRaisesRegex(ValueError, message):
                    verify_metric_evidence(
                        changed,
                        spec=bundle["spec"],
                        evaluation_time=bundle["input"]["evaluation_time"],
                        composition_mode="fixture",
                    )

    def test_production_mode_rejects_fixture_refs_aliases_and_reuse(self):
        with self.assertRaisesRegex(ValueError, "Fixture evidence"):
            build_qualification_input(
                repo_root=REPO_ROOT,
                composition_mode="production",
            )

        bundle = self._bundle()
        aliased = copy.deepcopy(bundle["input"])
        path = aliased["metric_evidence_refs"][0]["artifact_ref"]["path"]
        aliased["metric_evidence_refs"][0]["artifact_ref"]["path"] = f"./{path}"
        aliased = sign_payload(aliased)
        with self.assertRaisesRegex(ValueError, "canonical repo-relative"):
            verify_qualification_input(aliased, repo_root=REPO_ROOT)

        reused = copy.deepcopy(bundle["input"])
        reused["metric_evidence_refs"].append(
            copy.deepcopy(reused["metric_evidence_refs"][0])
        )
        reused["metric_evidence_refs"].sort(
            key=lambda item: (
                item["metric_id"],
                item["artifact_ref"]["identity_sha256"],
            )
        )
        reused = sign_payload(reused)
        with self.assertRaisesRegex(ValueError, "Duplicate qualification metric evidence"):
            verify_qualification_input(reused, repo_root=REPO_ROOT)

    def test_builders_canonicalize_semantically_irrelevant_order(self):
        left = build_qualification_input(
            repo_root=REPO_ROOT,
            spec_path=DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH,
            metric_evidence_paths=list(DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS.values()),
            composition_mode="fixture",
        )
        right = build_qualification_input(
            repo_root=REPO_ROOT,
            spec_path=DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH,
            metric_evidence_paths=list(reversed(DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS.values())),
            composition_mode="fixture",
        )
        self.assertEqual(left, right)

        evidence = build_fixture_metric_evidence("sim_joint_limit_projection_error")
        reversed_evidence = build_fixture_metric_evidence(
            "sim_joint_limit_projection_error",
            reverse_inputs=True,
        )
        self.assertEqual(evidence, reversed_evidence)

    def test_legacy_v1_report_cannot_carry_caller_declared_execution(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        report = copy.deepcopy(examples["report"])
        report["metrics"][0].update(
            {
                "status": "pass",
                "measured_value": 0.01,
                "evidence_mode": "simulation_trace",
                "evidence_refs": ["caller-declared.json"],
            }
        )
        report = sign_payload(report)
        with self.assertRaisesRegex(ValueError, "Legacy.*computed"):
            verify_twin_qualification_report(
                report,
                repo_root=REPO_ROOT,
                twin_profile=examples["profile"],
                twin_spec=examples["spec"],
            )

    def test_default_paths_are_distinct_from_legacy_scaffold(self):
        self.assertNotEqual(
            DEFAULT_COMPUTED_QUALIFICATION_REPORT_PATH.name,
            "pi05_twin_qualification_report.simulation_only.json",
        )
        self.assertTrue(DEFAULT_COMPUTED_QUALIFICATION_INPUT_PATH.parts[:2] == ("tests", "fixtures"))


if __name__ == "__main__":
    unittest.main()

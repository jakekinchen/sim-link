from __future__ import annotations

import hashlib
import json
import unittest

from pathlib import Path

from scenesmith.robot_lab.twin_contract import (
    DEFAULT_TWIN_PROFILE_PATH,
    DEFAULT_TWIN_QUALIFICATION_REPORT_PATH,
    DEFAULT_TWIN_QUALIFICATION_SPEC_PATH,
    build_twin_contract_examples,
    verify_twin_contract_examples,
    verify_twin_profile,
    verify_twin_qualification_report,
    verify_twin_qualification_spec,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class TwinContractTests(unittest.TestCase):
    def test_build_and_verify_examples(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)

        verify_twin_profile(examples["profile"], repo_root=REPO_ROOT)
        verify_twin_qualification_spec(
            examples["spec"],
            repo_root=REPO_ROOT,
            twin_profile=examples["profile"],
        )
        verify_twin_qualification_report(
            examples["report"],
            repo_root=REPO_ROOT,
            twin_profile=examples["profile"],
            twin_spec=examples["spec"],
        )

        self.assertEqual(examples["profile"]["proof_state"], "simulation_only")
        self.assertEqual(examples["report"]["qualification_state"], "simulation_only_unqualified")
        self.assertEqual(
            examples["profile"]["dependency_lock_ref"]["path"],
            "configurations/robot_lab/pi05_robotics_dependency_lock.json",
        )

    def test_checked_in_examples_match_deterministic_build(self):
        expected = build_twin_contract_examples(repo_root=REPO_ROOT)
        observed = {
            "profile": json.loads((REPO_ROOT / DEFAULT_TWIN_PROFILE_PATH).read_text(encoding="utf-8")),
            "spec": json.loads((REPO_ROOT / DEFAULT_TWIN_QUALIFICATION_SPEC_PATH).read_text(encoding="utf-8")),
            "report": json.loads((REPO_ROOT / DEFAULT_TWIN_QUALIFICATION_REPORT_PATH).read_text(encoding="utf-8")),
        }
        self.assertEqual(observed, expected)

    def test_verify_checked_in_examples_against_current_dependency_lock(self):
        payload = verify_twin_contract_examples(repo_root=REPO_ROOT)
        self.assertEqual(payload["profile"]["dependency_lock_ref"]["identity_sha256"], payload["spec"]["dependency_lock_ref"]["identity_sha256"])
        self.assertEqual(payload["profile"]["identity_sha256"], payload["report"]["profile_identity_sha256"])

    def test_verify_rejects_invalid_parameter_origin(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        profile = dict(examples["profile"])
        profile["sections"] = json.loads(json.dumps(profile["sections"]))
        profile["sections"]["actuators"]["parameters"][0]["origin"] = "guessed"
        profile["identity_sha256"] = _resign(profile)

        with self.assertRaisesRegex(ValueError, "parameter origin is invalid"):
            verify_twin_profile(profile, repo_root=REPO_ROOT)

    def test_verify_rejects_invalid_units_when_resigned(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        profile = dict(examples["profile"])
        profile["sections"] = json.loads(json.dumps(profile["sections"]))
        profile["sections"]["actuators"]["parameters"][0]["units"] = "ampere"
        profile["identity_sha256"] = _resign(profile)

        with self.assertRaisesRegex(ValueError, "parameter units are invalid"):
            verify_twin_profile(profile, repo_root=REPO_ROOT)

    def test_verify_rejects_reversed_uncertainty_bounds(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        profile = dict(examples["profile"])
        profile["sections"] = json.loads(json.dumps(profile["sections"]))
        profile["sections"]["structural_model_identity"]["parameters"][0]["uncertainty"] = {
            "lower": 2.0,
            "upper": 1.0,
        }
        profile["identity_sha256"] = _resign(profile)

        with self.assertRaisesRegex(ValueError, "uncertainty bounds are reversed"):
            verify_twin_profile(profile, repo_root=REPO_ROOT)

    def test_verify_rejects_missing_dependency_lock_linkage(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        spec = dict(examples["spec"])
        spec.pop("dependency_lock_ref", None)
        spec["identity_sha256"] = _resign(spec)

        with self.assertRaisesRegex(ValueError, "dependency lock linkage is missing"):
            verify_twin_qualification_spec(
                spec,
                repo_root=REPO_ROOT,
                twin_profile=examples["profile"],
            )

    def test_verify_rejects_tampered_profile_identity(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        examples["profile"]["profile_name"] = "tampered"

        with self.assertRaisesRegex(ValueError, "Twin profile identity hash is invalid"):
            verify_twin_profile(examples["profile"], repo_root=REPO_ROOT)

    def test_verify_rejects_physical_qualified_with_not_run_metric(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        report = dict(examples["report"])
        report["metrics"] = json.loads(json.dumps(report["metrics"]))
        report["proof_state"] = "physical_qualified"
        report["qualification_state"] = "physical_qualified"
        report["metrics"][1]["status"] = "not_run"
        report["identity_sha256"] = _resign(report)

        with self.assertRaisesRegex(ValueError, "require every metric to pass"):
            verify_twin_qualification_report(
                report,
                repo_root=REPO_ROOT,
                twin_profile=examples["profile"],
                twin_spec=examples["spec"],
            )

    def test_verify_rejects_physical_qualified_with_simulation_only_evidence(self):
        examples = build_twin_contract_examples(repo_root=REPO_ROOT)
        report = dict(examples["report"])
        report["metrics"] = json.loads(json.dumps(report["metrics"]))
        report["proof_state"] = "physical_qualified"
        report["qualification_state"] = "physical_qualified"
        report["metrics"][0]["evidence_mode"] = "simulation_trace"
        report["metrics"][1] = {
            "metric_id": "physical_gripper_contact_latency",
            "status": "pass",
            "measured_value": 21.0,
            "units": "millisecond",
            "evidence_mode": "simulation_trace",
            "evidence_refs": ["simulated_contact_trace.json"],
        }
        report["identity_sha256"] = _resign(report)

        with self.assertRaisesRegex(ValueError, "require the spec-declared evidence mode"):
            verify_twin_qualification_report(
                report,
                repo_root=REPO_ROOT,
                twin_profile=examples["profile"],
                twin_spec=examples["spec"],
            )


def _resign(payload: dict) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


if __name__ == "__main__":
    unittest.main()

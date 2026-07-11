from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.authority_composer import (
    DEFAULT_AUTHORITY_CONTRACT_PATH,
    DEFAULT_AUTHORITY_DECISION_PATH,
    GLOBAL_DECISION_IDS,
    build_authority_contract,
    build_capability_claim,
    build_composition_request,
    build_evidence_ref,
    compose_authority,
    require_global_decision,
    validate_authority_contract,
    verify_authority_artifacts,
    verify_authority_decision,
)
from scenesmith.robot_lab.measured_inertial_intake import (
    build_assembly_inertials,
    write_assembly_inertials,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/robot_lab/compose_robot_authority.py"
SYNTHETIC_INTAKE_PATH = (
    REPO_ROOT / "tests/fixtures/robot_lab/measured_mass/synthetic_complete.json"
)
SUBJECT_ID = "pi05_so101_sorting_system"
SCOPE_ID = "pi05_so101_authority"
EVALUATION_TIME = "2026-07-11T02:14:07-05:00"


class AuthorityComposerTests(unittest.TestCase):
    def test_contract_has_exact_global_decisions_and_valid_graph(self):
        contract = build_authority_contract()

        validate_authority_contract(contract)

        self.assertEqual(
            [item["decision_id"] for item in contract["global_decisions"]],
            list(GLOBAL_DECISION_IDS),
        )
        self.assertEqual(
            contract["schema_version"],
            "scenesmith.authority_composition_contract.v1",
        )
        self.assertIn("FORGED_GLOBAL_AUTHORITY_FIELD", contract["denial_reasons"])

    def test_contract_rejects_unknown_duplicate_ambiguous_and_cyclic_terms(self):
        mutators = {
            "unknown prerequisite": lambda contract: contract["global_decisions"][0][
                "expression"
            ]["terms"].append({"kind": "prerequisite", "id": "unknown_gate"}),
            "duplicate expression term": lambda contract: contract["global_decisions"][0][
                "expression"
            ]["terms"].append(
                json.loads(
                    json.dumps(contract["global_decisions"][0]["expression"]["terms"][0])
                )
            ),
            "ambiguous expression term": lambda contract: contract["global_decisions"][0][
                "expression"
            ]["terms"][0].update({"prerequisite_id": "structural_contract_valid"}),
            "cyclic decision graph": lambda contract: contract["global_decisions"][0].update(
                {
                    "expression": {
                        "operator": "all",
                        "terms": [
                            {"kind": "decision", "id": "physical_transfer_ready"}
                        ],
                    }
                }
            ),
        }
        expected = {
            "unknown prerequisite": "unknown prerequisite",
            "duplicate expression term": "Duplicate expression term",
            "ambiguous expression term": "ambiguous",
            "cyclic decision graph": "cycle",
        }
        for label, mutate in mutators.items():
            with self.subTest(label=label):
                contract = _unsigned_copy(build_authority_contract())
                mutate(contract)
                contract = sign_payload(contract)
                with self.assertRaisesRegex(ValueError, expected[label]):
                    validate_authority_contract(contract)

    def test_all_positive_authorized_prerequisites_are_mechanically_composed(self):
        claims = _all_prerequisite_claims()
        request = build_composition_request(
            subject_id=SUBJECT_ID,
            scope_id=SCOPE_ID,
            evaluation_time=EVALUATION_TIME,
            claims=claims,
        )

        decision = compose_authority(request)
        verify_authority_decision(decision, request=request)

        self.assertEqual(decision["authority_granted"], list(GLOBAL_DECISION_IDS))
        for result in decision["global_decisions"]:
            self.assertTrue(result["granted"])
            self.assertFalse(result["missing_prerequisite_ids"])
            self.assertFalse(result["denial_reason_codes"])
            self.assertTrue(result["consumed_evidence_identities"])
        require_global_decision(
            decision,
            request=request,
            decision_id="simulation_training_ready",
        )

    def test_fixture_composition_mode_cannot_grant_with_complete_positive_claims(self):
        request = build_composition_request(
            subject_id=SUBJECT_ID,
            scope_id=SCOPE_ID,
            evaluation_time=EVALUATION_TIME,
            claims=_all_prerequisite_claims(),
            composition_mode="fixture",
        )
        decision = compose_authority(request)

        self.assertEqual(decision["authority_granted"], [])
        for result in decision["global_decisions"]:
            self.assertFalse(result["granted"])
            self.assertIn(
                "NON_AUTHORIZING_COMPOSITION_MODE",
                result["denial_reason_codes"],
            )

    def test_missing_prerequisite_fails_closed_with_stable_reason(self):
        claims = [
            claim
            for claim in _all_prerequisite_claims()
            if claim["capability_id"] != "experience_compiler_valid"
        ]
        decision = _compose(claims)
        simulation = _decision(decision, "simulation_training_ready")

        self.assertFalse(simulation["granted"])
        self.assertIn("experience_compiler_valid", simulation["missing_prerequisite_ids"])
        self.assertIn("MISSING_PREREQUISITE", simulation["denial_reason_codes"])
        self.assertFalse(_decision(decision, "physical_transfer_ready")["granted"])

    def test_unknown_duplicate_and_contradictory_claims_are_rejected(self):
        valid = _claim_for("structural_contract_valid")
        unknown = json.loads(json.dumps(valid))
        unknown["claim_id"] = "claim_unknown"
        unknown["capability_id"] = "unknown_capability"
        unknown = sign_payload(_unsigned_copy(unknown))
        with self.assertRaisesRegex(ValueError, "Unknown capability"):
            build_composition_request(
                subject_id=SUBJECT_ID,
                scope_id=SCOPE_ID,
                evaluation_time=EVALUATION_TIME,
                claims=[unknown],
            )

        with self.assertRaisesRegex(ValueError, "Duplicate claim identity"):
            build_composition_request(
                subject_id=SUBJECT_ID,
                scope_id=SCOPE_ID,
                evaluation_time=EVALUATION_TIME,
                claims=[valid, valid],
            )

        contradiction = _claim_for(
            "structural_contract_valid",
            claim_id="claim_structural_contract_invalid",
            value=False,
        )
        with self.assertRaisesRegex(ValueError, "Contradictory capability claims"):
            build_composition_request(
                subject_id=SUBJECT_ID,
                scope_id=SCOPE_ID,
                evaluation_time=EVALUATION_TIME,
                claims=[valid, contradiction],
            )

    def test_forged_component_global_authority_field_explicitly_denies_everything(self):
        claims = _all_prerequisite_claims()
        forged = _unsigned_copy(claims[0])
        forged["simulation_training_ready"] = True
        claims[0] = sign_payload(forged)
        request = _resign_request_with_claims(claims)

        decision = compose_authority(request)

        self.assertEqual(decision["authority_granted"], [])
        self.assertEqual(decision["rejected_component_fields"], ["simulation_training_ready"])
        for result in decision["global_decisions"]:
            self.assertFalse(result["granted"])
            self.assertIn(
                "FORGED_GLOBAL_AUTHORITY_FIELD",
                result["denial_reason_codes"],
            )

    def test_nested_forged_authority_object_cannot_grant_global_decision(self):
        claims = _all_prerequisite_claims()
        forged = _unsigned_copy(claims[0])
        forged["authority"] = {"promotion_eligible": True}
        claims[0] = sign_payload(forged)
        decision = compose_authority(_resign_request_with_claims(claims))

        self.assertEqual(decision["authority_granted"], [])
        self.assertEqual(
            decision["rejected_component_fields"],
            ["authority", "promotion_eligible"],
        )

    def test_stale_expired_and_not_yet_valid_evidence_fail_closed(self):
        cases = {
            "EVIDENCE_STALE": {
                "observed_at": "2026-07-01T00:00:00-05:00",
                "valid_from": "2026-07-01T00:00:00-05:00",
                "valid_until": "2026-07-12T00:00:00-05:00",
                "max_age_seconds": 3600,
            },
            "EVIDENCE_EXPIRED": {
                "observed_at": "2026-07-10T00:00:00-05:00",
                "valid_from": "2026-07-10T00:00:00-05:00",
                "valid_until": "2026-07-11T01:00:00-05:00",
                "max_age_seconds": 172800,
            },
            "EVIDENCE_NOT_YET_VALID": {
                "observed_at": "2026-07-11T03:00:00-05:00",
                "valid_from": "2026-07-11T03:00:00-05:00",
                "valid_until": "2026-07-12T00:00:00-05:00",
                "max_age_seconds": 86400,
            },
        }
        for code, validity in cases.items():
            with self.subTest(code=code):
                claim = _claim_for("structural_contract_valid", validity=validity)
                result = _decision(_compose([claim]), "simulation_training_ready")
                self.assertFalse(result["granted"])
                self.assertIn(code, result["denial_reason_codes"])

    def test_provenance_issuer_subject_scope_and_evidence_substitution_fail_closed(self):
        base = "required_simulation_properties_available"
        contract = build_authority_contract()
        spec = _prerequisite_spec(contract, base)
        valid_issuer = spec["authorized_issuers"][0]
        cases = {
            "PROVENANCE_CLASS_NOT_ALLOWED": _claim_for(base, provenance_class="fixture"),
            "ISSUER_NOT_AUTHORIZED": _claim_for(
                base,
                issuer={
                    "authority_id": "untrusted.writer.v1",
                    "authority_identity_sha256": "f" * 64,
                },
            ),
            "SUBJECT_MISMATCH": _claim_for(base, subject_id="different_robot"),
            "SCOPE_MISMATCH": _claim_for(base, scope_id="different_scope"),
            "EVIDENCE_SUBSTITUTION": _claim_for(
                base,
                evidence_subject_id="different_robot",
                issuer=valid_issuer,
            ),
        }
        for code, claim in cases.items():
            with self.subTest(code=code):
                result = _decision(_compose([claim]), "simulation_training_ready")
                self.assertFalse(result["granted"])
                self.assertIn(code, result["denial_reason_codes"])

    def test_fixture_synthetic_and_replay_evidence_cannot_impersonate_physical(self):
        for provenance in ("fixture", "synthetic", "replay"):
            with self.subTest(provenance=provenance):
                claim = _claim_for(
                    "physical_hardware_identity_verified",
                    provenance_class=provenance,
                )
                result = _decision(_compose([claim]), "physical_transfer_ready")
                self.assertFalse(result["granted"])
                self.assertIn("PROVENANCE_CLASS_NOT_ALLOWED", result["denial_reason_codes"])

    def test_evidence_identity_tamper_is_rejected_even_when_outer_payload_is_resigned(self):
        claim = _unsigned_copy(_claim_for("structural_contract_valid"))
        claim["evidence_refs"][0]["artifact_identity_sha256"] = "0" * 64
        claim = sign_payload(claim)

        with self.assertRaisesRegex(ValueError, "evidence identity hash is invalid"):
            build_composition_request(
                subject_id=SUBJECT_ID,
                scope_id=SCOPE_ID,
                evaluation_time=EVALUATION_TIME,
                claims=[claim],
            )

    def test_input_order_does_not_change_request_or_composition_identity(self):
        claims = _all_prerequisite_claims()
        left_request = build_composition_request(
            subject_id=SUBJECT_ID,
            scope_id=SCOPE_ID,
            evaluation_time=EVALUATION_TIME,
            claims=claims,
        )
        right_request = build_composition_request(
            subject_id=SUBJECT_ID,
            scope_id=SCOPE_ID,
            evaluation_time=EVALUATION_TIME,
            claims=list(reversed(claims)),
        )

        self.assertEqual(left_request, right_request)
        self.assertEqual(compose_authority(left_request), compose_authority(right_request))

    def test_checked_in_contract_and_current_denial_match_production_rebuild(self):
        verified = verify_authority_artifacts(repo_root=REPO_ROOT)

        observed_contract = json.loads(
            (REPO_ROOT / DEFAULT_AUTHORITY_CONTRACT_PATH).read_text(encoding="utf-8")
        )
        observed_decision = json.loads(
            (REPO_ROOT / DEFAULT_AUTHORITY_DECISION_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(observed_contract, verified["contract"])
        self.assertEqual(observed_decision, verified["decision"])
        self.assertEqual(observed_decision["authority_granted"], [])
        self.assertEqual(
            observed_decision["authority_withheld"],
            list(GLOBAL_DECISION_IDS),
        )

    def test_product_cli_denies_blocked_and_synthetic_inertial_artifacts(self):
        checked = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--verify"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(checked.returncode, 0, msg=checked.stderr)
        checked_payload = json.loads(checked.stdout)
        self.assertEqual(checked_payload["authority_granted"], [])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "synthetic-inertials.json"
            write_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=SYNTHETIC_INTAKE_PATH,
                output_path=output_path,
            )
            compiled = build_assembly_inertials(
                repo_root=REPO_ROOT,
                intake_path=SYNTHETIC_INTAKE_PATH,
            )
            self.assertEqual(compiled["qualification_scope"], "synthetic_test_only")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake",
                    str(SYNTHETIC_INTAKE_PATH),
                    "--inertial-artifact",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["authority_granted"], [])
        self.assertEqual(payload["authority_withheld"], list(GLOBAL_DECISION_IDS))


def _compose(claims: list[dict]) -> dict:
    return compose_authority(
        build_composition_request(
            subject_id=SUBJECT_ID,
            scope_id=SCOPE_ID,
            evaluation_time=EVALUATION_TIME,
            claims=claims,
        )
    )


def _all_prerequisite_claims() -> list[dict]:
    contract = build_authority_contract()
    return [
        _claim_for(spec["prerequisite_id"])
        for spec in contract["prerequisites"]
    ]


def _claim_for(
    prerequisite_id: str,
    *,
    claim_id: str | None = None,
    value: bool = True,
    subject_id: str = SUBJECT_ID,
    scope_id: str = SCOPE_ID,
    provenance_class: str | None = None,
    issuer: dict | None = None,
    validity: dict | None = None,
    evidence_subject_id: str | None = None,
) -> dict:
    contract = build_authority_contract()
    spec = _prerequisite_spec(contract, prerequisite_id)
    provenance = provenance_class or spec["allowed_provenance_classes"][0]
    selected_issuer = issuer or spec["authorized_issuers"][0]
    artifact_digest = hashlib.sha256(f"artifact:{prerequisite_id}".encode()).hexdigest()
    evidence_refs = []
    if value:
        evidence_refs.append(
            build_evidence_ref(
                artifact_kind=f"{prerequisite_id}_artifact",
                artifact_schema_version="scenesmith.test_evidence.v1",
                artifact_identity_sha256=artifact_digest,
                subject_id=evidence_subject_id or subject_id,
                scope_id=scope_id,
                provenance_class=provenance,
            )
        )
    return build_capability_claim(
        claim_id=claim_id or f"claim_{prerequisite_id}",
        capability_id=prerequisite_id,
        value=value,
        subject_id=subject_id,
        scope_id=scope_id,
        provenance_class=provenance,
        issuer=selected_issuer,
        validity=validity
        or {
            "observed_at": "2026-07-11T01:00:00-05:00",
            "valid_from": "2026-07-11T00:00:00-05:00",
            "valid_until": "2026-07-12T00:00:00-05:00",
            "max_age_seconds": 86400,
        },
        evidence_refs=evidence_refs,
    )


def _prerequisite_spec(contract: dict, prerequisite_id: str) -> dict:
    return next(
        item
        for item in contract["prerequisites"]
        if item["prerequisite_id"] == prerequisite_id
    )


def _decision(payload: dict, decision_id: str) -> dict:
    return next(
        item for item in payload["global_decisions"] if item["decision_id"] == decision_id
    )


def _unsigned_copy(payload: dict) -> dict:
    copied = json.loads(json.dumps(payload))
    copied.pop("identity_sha256", None)
    return copied


def _resign_request_with_claims(claims: list[dict]) -> dict:
    request = build_composition_request(
        subject_id=SUBJECT_ID,
        scope_id=SCOPE_ID,
        evaluation_time=EVALUATION_TIME,
        claims=_all_prerequisite_claims(),
    )
    unsigned = _unsigned_copy(request)
    unsigned["claims"] = claims
    return sign_payload(unsigned)


if __name__ == "__main__":
    unittest.main()

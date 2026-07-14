from __future__ import annotations

import json
import tempfile
import unittest

from datetime import datetime
from pathlib import Path

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, sign_payload
from scenesmith.robot_lab.authority_composer import build_authority_contract, compose_authority
from scenesmith.robot_lab.simulation_training_authority import (
    OWNER_GRANT_PATH,
    build_production_authority,
    require_active_simulation_training_authority,
    verify_production_authority,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class SimulationTrainingAuthorityTests(unittest.TestCase):
    def test_contract_requires_explicit_owner_training_authority(self):
        contract = build_authority_contract()
        simulation = next(
            item for item in contract["global_decisions"] if item["decision_id"] == "simulation_training_ready"
        )
        self.assertIn(
            {"kind": "prerequisite", "id": "required_training_authority_present"},
            simulation["expression"]["terms"],
        )

    def test_production_authority_grants_only_simulation_training(self):
        verified = verify_production_authority(repo_root=REPO_ROOT)
        self.assertEqual(verified["decision"]["authority_granted"], ["simulation_training_ready"])
        self.assertEqual(
            verified["decision"]["authority_withheld"],
            ["physical_transfer_ready", "promotion_eligible"],
        )

    def test_missing_owner_claim_fails_closed(self):
        request, _decision = build_production_authority(repo_root=REPO_ROOT)
        stripped = json.loads(json.dumps(request))
        stripped["claims"] = [
            claim
            for claim in stripped["claims"]
            if claim["capability_id"] != "required_training_authority_present"
        ]
        decision = compose_authority(sign_payload(stripped))
        simulation = next(
            item for item in decision["global_decisions"] if item["decision_id"] == "simulation_training_ready"
        )
        self.assertFalse(simulation["granted"])
        self.assertIn("required_training_authority_present", simulation["missing_prerequisite_ids"])

    def test_modified_owner_grant_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "owner-grant.json"
            owner = json.loads((REPO_ROOT / OWNER_GRANT_PATH).read_text(encoding="utf-8"))
            owner["physical_transfer_authorized"] = True
            dump_canonical_json(target, sign_payload(owner))
            with self.assertRaisesRegex(ValueError, "Owner simulation-training grant drifted"):
                build_production_authority(repo_root=REPO_ROOT, owner_grant_path=target)

    def test_live_authority_rejects_expired_owner_grant(self):
        with self.assertRaisesRegex(ValueError, "has expired"):
            require_active_simulation_training_authority(
                repo_root=REPO_ROOT,
                now=datetime.fromisoformat("2026-07-21T03:05:01-05:00"),
            )

from __future__ import annotations

import copy
import unittest

from datetime import datetime

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    verify_spec_file,
)
from scenesmith.robot_lab.t20_36h_simulation_training_authority import (
    build_owner_grant,
    require_active_authority,
    verify_authority,
    verify_owner_grant,
)


class T2036hSimulationTrainingAuthorityTests(unittest.TestCase):
    def test_production_composition_grants_one_smolvla_attempt_only(self) -> None:
        verified = require_active_authority(
            now=datetime.fromisoformat("2026-07-15T20:05:00-05:00")
        )
        self.assertEqual(
            verified["decision"]["authority_granted"],
            ["simulation_training_ready"],
        )
        current = verify_authority()
        self.assertEqual(current, verified)

    def test_owner_grant_rejects_scope_escalation(self) -> None:
        spec = verify_spec_file()
        owner = build_owner_grant(training_spec=spec)
        self.assertEqual(owner["authorized_attempt_count"], 1)
        self.assertTrue(owner["smolvla_entry_authorized"])
        self.assertFalse(owner["policy_track_selection_authorized"])
        drift = copy.deepcopy(owner)
        drift["gate_c_authorized"] = True
        with self.assertRaises(ValueError):
            verify_owner_grant(sign_payload(drift), training_spec=spec)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import unittest

from datetime import datetime

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    verify_spec_file,
)
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (
    verify_contract_file,
)
from scenesmith.robot_lab.t20_36j_simulation_training_authority import (
    EXPECTED_OFFLINE_INSTALLS,
    build_owner_grant,
    require_active_authority,
    verify_authority,
    verify_owner_grant,
)


class T2036jSimulationTrainingAuthorityTests(unittest.TestCase):
    def test_production_composition_grants_one_replacement_only(self) -> None:
        verified = require_active_authority(
            now=datetime.fromisoformat("2026-07-16T01:00:00-05:00")
        )
        self.assertEqual(
            verified["decision"]["authority_granted"],
            ["simulation_training_ready"],
        )
        self.assertEqual(verified, verify_authority())

    def test_owner_grant_binds_exact_offline_install_and_no_escalation(self) -> None:
        spec = verify_spec_file()
        contract = verify_contract_file()
        owner = build_owner_grant(
            training_spec=spec,
            corrected_contract=contract,
        )
        self.assertEqual(
            owner["exact_offline_install"],
            [
                {"package": package, "version": version}
                for package, version in sorted(EXPECTED_OFFLINE_INSTALLS.items())
            ],
        )
        self.assertFalse(owner["network_access_authorized"])
        self.assertEqual(owner["authorized_attempt_count"], 1)
        self.assertFalse(owner["retry_or_sweep_authorized"])
        drift = copy.deepcopy(owner)
        drift["gate_c_authorized"] = True
        with self.assertRaises(ValueError):
            verify_owner_grant(
                sign_payload(drift),
                training_spec=spec,
                corrected_contract=contract,
            )

    def test_authority_expires_at_owner_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "expired"):
            require_active_authority(
                now=datetime.fromisoformat("2026-07-16T08:33:38-05:00")
            )


if __name__ == "__main__":
    unittest.main()

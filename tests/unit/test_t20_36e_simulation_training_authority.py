from __future__ import annotations

import copy
import tempfile
import unittest

from datetime import datetime
from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import (
    COORDINATE_SOURCE_PATH,
    DATASET_INFO_PATH,
    DATASET_MANIFEST_PATH,
    DATASET_STATS_PATH,
    GATE_B_SPEC_PATH,
    LOCAL_PREFLIGHT_PATH,
    SPEC_PATH,
)
from scenesmith.robot_lab.t20_36e_simulation_training_authority import (
    DECISION_PATH,
    OWNER_GRANT_PATH,
    REQUEST_PATH,
    T20_23_DECISION_PATH,
    T20_23_REQUEST_PATH,
    build_owner_grant,
    build_production_authority,
    require_active_authority,
    verify_owner_grant,
)


class T2036eSimulationTrainingAuthorityTests(unittest.TestCase):
    def test_production_composition_grants_training_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._copy_sources(Path(directory))
            spec = load_strict_json(root / SPEC_PATH)
            owner = build_owner_grant(training_spec=spec, repo_root=root)
            dump_canonical_json(root / OWNER_GRANT_PATH, owner)
            request, decision = build_production_authority(repo_root=root)
            dump_canonical_json(root / REQUEST_PATH, request)
            dump_canonical_json(root / DECISION_PATH, decision)
            verified = require_active_authority(
                repo_root=root,
                now=datetime.fromisoformat("2026-07-15T20:00:00-05:00"),
            )
            self.assertEqual(
                verified["decision"]["authority_granted"],
                ["simulation_training_ready"],
            )
            self.assertEqual(owner["authorized_attempt_count"], 1)
            self.assertFalse(owner["gate_c_authorized"])
            self.assertFalse(owner["smolvla_entry_authorized"])

    def test_owner_grant_rejects_scope_escalation(self) -> None:
        spec = load_strict_json(SPEC_PATH)
        owner = build_owner_grant(training_spec=spec)
        drift = copy.deepcopy(owner)
        drift["gate_c_authorized"] = True
        with self.assertRaises(ValueError):
            verify_owner_grant(sign_payload(drift), training_spec=spec)

    def _copy_sources(self, root: Path) -> Path:
        paths = (
            SPEC_PATH,
            LOCAL_PREFLIGHT_PATH,
            GATE_B_SPEC_PATH,
            DATASET_MANIFEST_PATH,
            DATASET_INFO_PATH,
            DATASET_STATS_PATH,
            COORDINATE_SOURCE_PATH,
            T20_23_REQUEST_PATH,
            T20_23_DECISION_PATH,
        )
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(relative.read_bytes())
        return root


if __name__ == "__main__":
    unittest.main()

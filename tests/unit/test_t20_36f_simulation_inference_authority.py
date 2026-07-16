from __future__ import annotations

import copy
import tempfile
import unittest

from datetime import datetime
from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
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
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (
    RESULT_PATH as SOURCE_RESULT_PATH,
    RUNTIME_PREFLIGHT_PATH as SOURCE_RUNTIME_PATH,
    TRAINING_PERMIT_PATH as SOURCE_PERMIT_PATH,
)
from scenesmith.robot_lab.t20_23_simulation_training_authority import (
    DECISION_PATH as T20_23_DECISION_PATH,
    REQUEST_PATH as T20_23_REQUEST_PATH,
)
from scenesmith.robot_lab.t20_36e_simulation_training_authority import (
    DECISION_PATH as SOURCE_DECISION_PATH,
    OWNER_GRANT_PATH as SOURCE_OWNER_PATH,
    REQUEST_PATH as SOURCE_REQUEST_PATH,
)
from scenesmith.robot_lab.t20_36f_simulation_inference_authority import (
    DECISION_PATH,
    OWNER_GRANT_PATH,
    REQUEST_PATH,
    build_owner_grant,
    build_production_authority,
    require_active_authority,
    verify_owner_grant,
)


class T2036fSimulationInferenceAuthorityTests(unittest.TestCase):
    def test_composition_grants_only_central_ready_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._copy_sources(Path(directory))
            from scenesmith.robot_lab.t20_36f_act_decode_localization import (
                load_verified_sources,
            )

            sources = load_verified_sources(repo_root=root)
            owner = build_owner_grant(sources=sources, repo_root=root)
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
            self.assertFalse(owner["optimizer_authorized"])
            self.assertFalse(owner["smolvla_entry_authorized"])

    def test_owner_grant_rejects_optimizer_escalation(self) -> None:
        from scenesmith.robot_lab.t20_36f_act_decode_localization import (
            load_verified_sources,
        )

        sources = load_verified_sources()
        owner = build_owner_grant(sources=sources)
        drift = copy.deepcopy(owner)
        drift["optimizer_authorized"] = True
        with self.assertRaises(ValueError):
            verify_owner_grant(sign_payload(drift), sources=sources)

    def _copy_sources(self, root: Path) -> Path:
        tracked = (
            SPEC_PATH,
            LOCAL_PREFLIGHT_PATH,
            GATE_B_SPEC_PATH,
            DATASET_MANIFEST_PATH,
            DATASET_INFO_PATH,
            DATASET_STATS_PATH,
            COORDINATE_SOURCE_PATH,
            SOURCE_RESULT_PATH,
            SOURCE_RUNTIME_PATH,
            SOURCE_PERMIT_PATH,
            SOURCE_OWNER_PATH,
            SOURCE_REQUEST_PATH,
            SOURCE_DECISION_PATH,
            T20_23_REQUEST_PATH,
            T20_23_DECISION_PATH,
        )
        ignored = (
            Path(
                "outputs/robot_lab/"
                "t20_36e_exact_act_gate_b_control_run_001/attempt.json"
            ),
            Path(
                "outputs/robot_lab/"
                "t20_36e_exact_act_gate_b_control_run_001/run_summary.json"
            ),
        )
        for relative in (*tracked, *ignored):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(relative.read_bytes())
        return root


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36m_tensor_retention import (
    build_retention_receipt,
)


class T2036mTensorRetentionTest(unittest.TestCase):
    def test_tracked_tensor_reconstructs_exact_negative_score(self) -> None:
        from scenesmith.robot_lab.artifact_contract import load_strict_json
        from scenesmith.robot_lab.t20_36m_tensor_reproduction import load_verified_sources
        from scenesmith.robot_lab.t20_36m_tensor_retention import (
            REPO_ROOT,
            RESULT_PATH,
            RETENTION_RECEIPT_PATH,
            TRACKED_TENSOR_PATH,
        )

        sources = load_verified_sources(repo_root=REPO_ROOT)
        tensor = load_strict_json(REPO_ROOT / TRACKED_TENSOR_PATH)
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        receipt = load_strict_json(REPO_ROOT / RETENTION_RECEIPT_PATH)
        rebuilt = build_retention_receipt(
            tensor_artifact=tensor,
            result=result,
            frozen_gate=sources["frozen_gate"],
            target=receipt["target_action"],
            repo_root=REPO_ROOT,
        )
        self.assertEqual(rebuilt, receipt)
        self.assertEqual(receipt["rescored_total_violation_count"], 162)

    def test_tensor_value_mutation_is_rejected(self) -> None:
        from scenesmith.robot_lab.artifact_contract import load_strict_json
        from scenesmith.robot_lab.t20_36m_tensor_reproduction import load_verified_sources
        from scenesmith.robot_lab.t20_36m_tensor_retention import (
            REPO_ROOT,
            RESULT_PATH,
            RETENTION_RECEIPT_PATH,
            TRACKED_TENSOR_PATH,
        )

        sources = load_verified_sources(repo_root=REPO_ROOT)
        tensor = copy.deepcopy(load_strict_json(REPO_ROOT / TRACKED_TENSOR_PATH))
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        receipt = load_strict_json(REPO_ROOT / RETENTION_RECEIPT_PATH)
        tensor["rows"][0]["first"][0][0] += 0.001
        tensor = sign_payload({k: v for k, v in tensor.items() if k != "identity_sha256"})
        with self.assertRaisesRegex(ValueError, "lineage|hash or repeat"):
            build_retention_receipt(
                tensor_artifact=tensor,
                result=result,
                frozen_gate=sources["frozen_gate"],
                target=receipt["target_action"],
                repo_root=REPO_ROOT,
            )


if __name__ == "__main__":
    unittest.main()

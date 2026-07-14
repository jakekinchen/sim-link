"""Tests for immutable T18.2 logical source/cycle buffers."""
from __future__ import annotations
import copy, subprocess, unittest
from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.logical_source_cycle_buffers import REPO_ROOT, _source_window_ids, append_logical_cycle, build_initial_buffer_registry, verify_initial_buffer_registry
class LogicalSourceCycleBufferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None: cls.registry = build_initial_buffer_registry()
    def test_initial_cycle_is_exact_unique_and_deterministic(self) -> None:
        verify_initial_buffer_registry(self.registry)
        self.assertEqual(self.registry["realized_cycle_count"], 1)
        self.assertEqual(self.registry["realized_window_count"], 192)
        self.assertEqual(self.registry["cycles"][0]["cycle_id"], "0001")
        self.assertTrue(self.registry["cycles"][0]["immutable"])
        self.assertFalse(self.registry["buffer_materialized"])
    def test_append_rejects_prior_mutation_and_duplicate_reuse(self) -> None:
        mutated = copy.deepcopy(self.registry); mutated["cycles"][0]["window_ids"][0] = "0" * 64; mutated = sign_payload(mutated)
        with self.assertRaisesRegex(ValueError, "digest drifted"): append_logical_cycle(mutated, "0002", ["1" * 64])
        with self.assertRaisesRegex(ValueError, "reuses"): append_logical_cycle(self.registry, "0002", [self.registry["cycles"][0]["window_ids"][0]])
        with self.assertRaisesRegex(ValueError, "absent source"): append_logical_cycle(self.registry, "0002", ["0" * 64])
        unused = next(iter(_source_window_ids() - set(self.registry["cycles"][0]["window_ids"])))
        appended = append_logical_cycle(self.registry, "0002", [unused])
        self.assertEqual(appended["realized_cycle_count"], 2)
        self.assertEqual(appended["realized_window_count"], 193)
    def test_authority_escalation_and_raw_rewrite_are_rejected(self) -> None:
        elevated = dict(self.registry); elevated["buffer_materialized"] = True
        with self.assertRaisesRegex(ValueError, "identity"): verify_initial_buffer_registry(elevated)
        with self.assertRaisesRegex(ValueError, "authority flag"): verify_initial_buffer_registry(sign_payload(elevated))
        result = subprocess.run([str(REPO_ROOT / ".mujoco_venv/bin/python"), str(REPO_ROOT / "scripts/robot_lab/write_logical_source_cycle_buffers.py"), "--rewrite"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0); self.assertIn("immutable", result.stderr)
if __name__ == "__main__": unittest.main()

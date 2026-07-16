import copy
import hashlib
import unittest

from scenesmith.robot_lab.act_grasp_closed_loop import PHASE_PLAN, ROLLOUT_FRAMES
from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID
from scenesmith.robot_lab.t20_44_r2_smolvla_contracts import CHECKPOINT_SCHEDULE
from scenesmith.robot_lab.t20_44_r2_smolvla_runner import (
    build_comparison_rows,
    build_result,
    build_run_summary,
    build_trace,
    verify_result,
    verify_trace,
)


class T2044R2SmolVLARunnerTest(unittest.TestCase):
    def test_comparison_rows_bind_chunk_50_and_receding_10(self) -> None:
        source, candidate = self._frames()
        chunk = build_comparison_rows(
            source_frames=source, candidate_frames=candidate, n_action_steps=50
        )
        receding = build_comparison_rows(
            source_frames=source, candidate_frames=candidate, n_action_steps=10
        )
        self.assertEqual(chunk[-1]["chunk_index"], 4)
        self.assertEqual(chunk[-1]["chunk_offset"], 43)
        self.assertEqual(receding[-1]["chunk_index"], 24)
        self.assertEqual(receding[-1]["chunk_offset"], 3)

    def test_trace_rejects_unmasked_tail_or_wrong_decode_start(self) -> None:
        trace = self._trace(update=500, n_action_steps=50, strict=False)
        verify_trace(trace)
        mutated = copy.deepcopy(trace)
        mutated["decode_rows"][-1]["executed_length"] = 50
        with self.assertRaises(ValueError):
            verify_trace(mutated)

    def test_first_gate_c_selection_is_earliest_then_chunk_50(self) -> None:
        run = self._run(pass_update=2500, pass_variants=(True, True))
        self.assertEqual(run["first_gate_c_pass"]["optimizer_update_count"], 2500)
        self.assertEqual(run["first_gate_c_pass"]["variant_id"], "chunk_50")
        result = build_result(run=run)
        verify_result(result, run=run)
        self.assertEqual(result["status"], "verified_gate_c_success")
        self.assertTrue(result["simulation_policy_accepted"])
        self.assertFalse(result["promotion_eligible"])

    def test_negative_run_closes_without_retry(self) -> None:
        run = self._run(pass_update=None, pass_variants=(False, False))
        result = build_result(run=run)
        self.assertEqual(result["status"], "verified_terminal_negative")
        self.assertFalse(result["gate_c_passed"])
        self.assertFalse(result["retry_authorized"])

    def _run(self, *, pass_update, pass_variants) -> dict:
        checkpoints = []
        evaluations = []
        for update in CHECKPOINT_SCHEDULE:
            tree = [{"path": "model.safetensors", "size_bytes": 1, "sha256": "a" * 64}]
            checkpoints.append(
                {
                    "optimizer_update_count": update,
                    "path": f"outputs/checkpoints/{update}",
                    "tree": tree,
                    "identity_sha256": hashlib.sha256(
                        canonical_json_bytes(tree)
                    ).hexdigest(),
                }
            )
            flags = pass_variants if update == pass_update else (False, False)
            evaluations.append(
                {
                    "optimizer_update_count": update,
                    "variants": [
                        self._variant("chunk_50", 50, flags[0], update),
                        self._variant("receding_10", 10, flags[1], update),
                    ],
                }
            )
        return build_run_summary(
            attempt={"identity_sha256": "1" * 64},
            spec={"identity_sha256": "2" * 64},
            optimizer_update_count=5000,
            losses=[1.0] * 5000,
            gradient_norms=[1.0] * 5000,
            learning_rates=[1e-4] * 5000,
            checkpoints=checkpoints,
            evaluations=evaluations,
        )

    @staticmethod
    def _variant(variant_id, n_action_steps, passed, update):
        return {
            "variant_id": variant_id,
            "n_action_steps": n_action_steps,
            "strict_v2_passed": passed,
            "terminal_outcome": "strict_success"
            if passed
            else "no_strict_grasp_contact",
            "trace_path": f"outputs/{update}_{variant_id}.json",
            "trace_identity_sha256": hashlib.sha256(
                f"trace-{update}-{variant_id}".encode()
            ).hexdigest(),
            "video_path": f"outputs/{update}_{variant_id}.mp4",
            "video_file_sha256": hashlib.sha256(
                f"video-{update}-{variant_id}".encode()
            ).hexdigest(),
            "video_manifest_path": f"outputs/{update}_{variant_id}.manifest.json",
            "video_manifest_identity_sha256": hashlib.sha256(
                f"manifest-{update}-{variant_id}".encode()
            ).hexdigest(),
        }

    def _trace(self, *, update, n_action_steps, strict):
        source, candidate = self._frames()
        rows = build_comparison_rows(
            source_frames=source,
            candidate_frames=candidate,
            n_action_steps=n_action_steps,
        )
        starts = list(range(0, ROLLOUT_FRAMES, n_action_steps))
        decode_rows = []
        for start in starts:
            length = min(n_action_steps, ROLLOUT_FRAMES - start)
            decode_rows.append(
                {
                    "decode_start_frame": start,
                    "checkpoint_update": update,
                    "noise_seed": 20260901 + update * 100 + n_action_steps * 10 + start,
                    "base_noise_sha256": "f" * 64,
                    "n_action_steps": n_action_steps,
                    "predicted_chunk_length": 50,
                    "source_comparison_length": min(50, ROLLOUT_FRAMES - start),
                    "executed_length": length,
                    "unexecuted_tail_count": 50 - length,
                    "physical_action_chunk_sha256": "a" * 64,
                    "executed_action_sha256": "b" * 64,
                    "uniform_report_only_threshold_rad": 0.05,
                    "uniform_report_only_maximum_error_rad": 0.0,
                    "uniform_report_only_passed": True,
                    "frozen_gate_identity_sha256": (
                        "463477dc91e3fb36b0550b88d461a788709a7258f9825ad6644f98bf0c77e48f"
                    ),
                    "frozen_amended_gate_passed": True,
                    "frozen_amended_gate_violation_count": 0,
                    "frozen_amended_gate_violations": [],
                }
            )
        requested = hashlib.sha256(
            __import__("json")
            .dumps(
                [row["candidate_requested_action_rad"] for row in rows],
                separators=(",", ":"),
            )
            .encode()
        ).hexdigest()
        margins = {"test": {"passed": strict, "margin": 1.0 if strict else -1.0}}
        rollout = sign_payload(
            {
                "seed": 0,
                "frame_count": 244,
                "policy_action_sequence_sha256": requested,
                "projected_action_frame_count": 0,
                "active_assist_frame_count": 0,
                "simulation_semantic_strict_success": strict,
                "gate_margins": margins,
            }
        )
        return build_trace(
            update=update,
            variant_id="chunk_50" if n_action_steps == 50 else "receding_10",
            n_action_steps=n_action_steps,
            checkpoint_identity_sha256="c" * 64,
            source_ref={
                "path": "source.json",
                "file_sha256": "d" * 64,
                "raw_rollout_identity_sha256": "e" * 64,
            },
            rows=rows,
            decode_rows=decode_rows,
            closed_loop=rollout,
        )

    @staticmethod
    def _frames():
        phases = [phase for phase, count in PHASE_PLAN for _ in range(count)]
        source = []
        candidate = []
        for index, phase in enumerate(phases):
            action = [0.01 * joint for joint in range(6)]
            qpos = [0.02 * joint for joint in range(6)]
            source.append(
                {
                    "frame_index": index,
                    "source_phase": phase,
                    "actions": {
                        "requested": {"values": action},
                        "sent": {"values": action},
                    },
                    "observations": {
                        "joint_position_mujoco_rad": qpos,
                        "joint_velocity_mujoco_rad_s": [0.0] * 6,
                    },
                }
            )
            candidate.append(
                {
                    "phase": phase,
                    "policy_requested_action": action,
                    "policy_applied_action": action,
                    "mujoco_qpos": qpos,
                    "mujoco_qvel": [0.0] * 6,
                    "cube_positions_m": {OBJECT_ID: [0.22, 0.0, 0.325]},
                    "t20_44_strict_contact": False,
                }
            )
        return source, candidate


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import hashlib
import json
import unittest

from scenesmith.robot_lab.act_grasp_closed_loop import PHASE_PLAN
from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36_bounded_corrected_coverage import (
    INFERENCE_SEEDS,
    OPTIMIZER_UPDATES,
    RUN_SCHEMA_VERSION,
    build_mirror_ref,
    build_result,
    build_runtime_preflight,
    build_trace,
    build_training_permit,
    build_training_spec,
    load_source_artifacts,
)


class T2036BoundedCorrectedCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.canonical_sources = load_source_artifacts()

    def setUp(self) -> None:
        self.threshold = copy.deepcopy(self.canonical_sources["threshold"])
        self.sources = copy.deepcopy(self.canonical_sources)
        self.spec = build_training_spec(**self.sources)
        self.authority = "f" * 64

    def test_spec_binds_gate_b_pass_coverage_and_unchanged_processor(self) -> None:
        self.assertEqual(
            self.spec["campaign"]["coverage_unique_sample_count"], 500
        )
        self.assertEqual(
            self.spec["processor_contract"]["source"],
            "unchanged_t20_35x_processor_and_statistics",
        )
        self.assertTrue(
            self.spec["ordered_closed_loop_evaluation"][
                "gate_b_required_before_any_rollout"
            ]
        )
        drifted = copy.deepcopy(self.sources)
        drifted["x_result"] = sign_payload(
            {**drifted["x_result"], "gate_b_passed": False}
        )
        with self.assertRaisesRegex(ValueError, "Gate B|identity"):
            build_training_spec(**drifted)

    def test_spec_rejects_reordered_or_duplicate_coverage(self) -> None:
        for mutate in (
            lambda rows: rows.reverse(),
            lambda rows: rows.__setitem__(1, rows[0]),
        ):
            sources = copy.deepcopy(self.sources)
            rows = sources["sampler_audit"]["campaigns"]["recovery_augmented"][
                "sampled_indices"
            ]
            mutate(rows)
            sources["sampler_audit"] = sign_payload(sources["sampler_audit"])
            with self.assertRaisesRegex(ValueError, "identity|schedule"):
                build_training_spec(**sources)

    def test_preflight_and_permit_fail_closed(self) -> None:
        preflight = build_runtime_preflight(
            spec=self.spec,
            authority_identity=self.authority,
            python_major_minor=[3, 12],
            dependency_versions=self.spec["required_dependency_versions"],
            mps_available=True,
            lerobot_stack_identity_sha256="e" * 64,
            ffmpeg_version="8.0.1",
            render_smoke_verified=True,
            free_disk_bytes=10 * 1024 * 1024 * 1024,
            source_checkpoint_tree_verified=True,
            coverage_dataset_tree_verified=True,
            attempt_exists=False,
            result_exists=False,
        )
        permit = build_training_permit(
            spec=self.spec,
            authority_identity=self.authority,
            runtime_preflight=preflight,
        )
        self.assertEqual(permit["authorized_attempt_count"], 1)
        self.assertTrue(permit["ordered_gate_enforcement_required"])
        with self.assertRaisesRegex(ValueError, "failed closed"):
            build_runtime_preflight(
                spec=self.spec,
                authority_identity=self.authority,
                python_major_minor=[3, 12],
                dependency_versions=self.spec["required_dependency_versions"],
                mps_available=True,
                lerobot_stack_identity_sha256="e" * 64,
                ffmpeg_version="8.0.1",
                render_smoke_verified=True,
                free_disk_bytes=10 * 1024 * 1024 * 1024,
                source_checkpoint_tree_verified=True,
                coverage_dataset_tree_verified=False,
                attempt_exists=False,
                result_exists=False,
            )

    def test_gate_b_failure_forbids_rollout(self) -> None:
        run = self._run(gate_b=False)
        result = build_result(
            spec=self.spec,
            run=run,
            authority_identity=self.authority,
            traces=[],
            mirror_refs=[],
            threshold=self.threshold,
        )
        self.assertEqual(
            result["decision"], "gate_b_regressed_stop_before_closed_loop"
        )
        with self.assertRaisesRegex(ValueError, "coverage"):
            build_result(
                spec=self.spec,
                run=run,
                authority_identity=self.authority,
                traces=[self._trace(0, strict=False)],
                mirror_refs=[self._mirror_ref(0, strict=False)],
                threshold=self.threshold,
            )

    def test_gate_c_failure_stops_before_held_out(self) -> None:
        trace = self._trace(0, strict=False)
        result = build_result(
            spec=self.spec,
            run=self._run(gate_b=True),
            authority_identity=self.authority,
            traces=[trace],
            mirror_refs=[self._mirror_ref_for_trace(trace)],
            threshold=self.threshold,
        )
        self.assertEqual(result["decision"], "gate_c_failed_stop_before_held_out")
        self.assertEqual(result["evaluation_seeds_reached"], [0])

    def test_gate_c_pass_requires_both_held_out_in_order(self) -> None:
        traces = [self._trace(seed, strict=True) for seed in (0, 6, 7)]
        mirrors = [self._mirror_ref_for_trace(trace) for trace in traces]
        result = build_result(
            spec=self.spec,
            run=self._run(gate_b=True),
            authority_identity=self.authority,
            traces=traces,
            mirror_refs=mirrors,
            threshold=self.threshold,
        )
        self.assertTrue(result["candidate_three_seed_strict_success"])
        self.assertFalse(result["simulation_policy_accepted"])
        with self.assertRaisesRegex(ValueError, "coverage"):
            build_result(
                spec=self.spec,
                run=self._run(gate_b=True),
                authority_identity=self.authority,
                traces=[traces[0], traces[2], traces[1]],
                mirror_refs=[mirrors[0], mirrors[2], mirrors[1]],
                threshold=self.threshold,
            )

    def test_mirror_must_be_signed_and_content_addressed(self) -> None:
        trace = self._trace(0, strict=False)
        ref = self._mirror_ref_for_trace(trace)
        self.assertEqual(ref["trace_identity_sha256"], trace["identity_sha256"])
        manifest = self._mirror_manifest(trace)
        manifest["output_mp4"] = "/tmp/not-content-addressed.mp4"
        manifest = sign_payload(manifest)
        with self.assertRaisesRegex(ValueError, "content addressed"):
            build_mirror_ref(trace=trace, manifest=manifest)

    def _run(self, *, gate_b: bool) -> dict:
        values = [1.0] * OPTIMIZER_UPDATES
        ratio = 0.01 if gate_b else 0.2
        final_standard = ratio * self.spec["gate_b"][
            "source_gate_baseline_objective_mean"
        ]
        decoded = [
            {
                "inference_seed": seed,
                "maximum_absolute_error_rad": 0.01 if gate_b else 0.1,
            }
            for seed in self.spec["gate_b"]["inference_seeds"]
        ]
        return sign_payload(
            {
                "schema_version": RUN_SCHEMA_VERSION,
                "task_id": "T20.36",
                "training_spec_identity_sha256": self.spec["identity_sha256"],
                "authority_decision_identity_sha256": self.authority,
                "optimizer_update_count": OPTIMIZER_UPDATES,
                "coverage_sample_index_by_update": self.spec["campaign"][
                    "coverage_sample_index_by_update"
                ],
                "correction_example_index_by_update": self.spec["campaign"][
                    "correction_example_index_by_update"
                ],
                "standard_flow_seed_by_update": self.spec["campaign"][
                    "standard_flow_seed_by_update"
                ],
                "per_update_standard_coverage_objective": values,
                "per_update_time_joint_weighted_correction_objective": values,
                "per_update_total_objective": [2.0] * OPTIMIZER_UPDATES,
                "gradient_norms_before_clip": values,
                "decoded_action_chunks": decoded,
                "gate_b_passed": gate_b,
                "final_standard_objective_mean": final_standard,
                "final_to_source_gate_baseline_objective_ratio": ratio,
                "objective_ratio_within_threshold": gate_b,
                "all_decoded_chunks_within_threshold": gate_b,
                "checkpoint_identity_sha256": "d" * 64,
                "optimizer_training": True,
                "closed_loop_rollout": False,
                "checkpoint_mutated": False,
                "dataset_mutated": False,
                "statistics_changed": False,
                "simulation_policy_accepted": False,
                "physical_actuation": False,
                "external_compute_started": False,
                "brev_compute_started": False,
                "physical_transfer_ready": False,
                "promotion_eligible": False,
            }
        )

    def _trace(self, seed: int, *, strict: bool) -> dict:
        rows = []
        frame_index = 0
        for phase, count in PHASE_PLAN:
            for _ in range(count):
                values = [0.0] * 6
                rows.append(
                    {
                        "frame_index": frame_index,
                        "phase": phase,
                        "chunk_index": frame_index // 5,
                        "chunk_offset": frame_index % 5,
                        "source_requested_action_rad": values,
                        "source_applied_action_rad": values,
                        "candidate_requested_action_rad": values,
                        "candidate_applied_action_rad": values,
                        "source_qpos_rad": values,
                        "candidate_qpos_rad": values,
                        "source_qvel_rad_s": values,
                        "candidate_qvel_rad_s": values,
                        "candidate_anchor_position_m": [0.2, 0.0, 0.325],
                        "candidate_strict_contact": False,
                    }
                )
                frame_index += 1
        rollout = sign_payload(
            {
                "seed": seed,
                "frame_count": 244,
                "projected_action_frame_count": 0,
                "active_assist_frame_count": 0,
                "simulation_semantic_strict_success": strict,
                "terminal_outcome": "strict_success" if strict else "failure",
                "policy_action_sequence_sha256": hashlib.sha256(
                    json.dumps(
                        [row["candidate_requested_action_rad"] for row in rows],
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest(),
            }
        )
        return build_trace(
            threshold=self.threshold,
            seed=seed,
            inference_seed=INFERENCE_SEEDS[seed],
            source_episode_file_sha256="a" * 64,
            source_episode_identity_sha256="b" * 64,
            run_identity_sha256="c" * 64,
            checkpoint_identity_sha256="d" * 64,
            rows=rows,
            closed_loop=rollout,
        )

    def _mirror_ref(self, seed: int, *, strict: bool) -> dict:
        return self._mirror_ref_for_trace(self._trace(seed, strict=strict))

    def _mirror_ref_for_trace(self, trace: dict) -> dict:
        return build_mirror_ref(trace=trace, manifest=self._mirror_manifest(trace))

    @staticmethod
    def _mirror_manifest(trace: dict) -> dict:
        return sign_payload(
            {
                "schema_version": "scenesmith.rollout_mirror_render.v1",
                "purpose": "diagnostic visualization of signed trace evidence; no authority",
                "trace_path": "/tmp/trace.json",
                "trace_identity_sha256": trace["identity_sha256"],
                "adapter_id": trace["adapter_id"],
                "seed": trace["seed"],
                "seed_role": trace["seed_role"],
                "frame_count": 244,
                "panels": ["policy", "expert"],
                "anchor_orientation": "held",
                "output_mp4": f"/tmp/{trace['identity_sha256']}.mp4",
                "output_sha256": "e" * 64,
                "output_bytes": 123,
            }
        )

if __name__ == "__main__":
    unittest.main()

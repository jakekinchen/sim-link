"""Deterministic, non-executing F0c fork-day-one training package."""

from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "F0c"
ACTIVATION_COMMIT = "126121d28b2c495332a71436b2313e0ccb54c69f"
SPEC_PATH = Path("configurations/robot_lab/f0c_release_targeted_continuation_spec.json")
OWNER_DIRECTION_PATH = Path(
    "docs/autonomous-workflow/owner-direction-2026-07-17-final-overnight.md"
)
BRIEF_PATH = Path("docs/briefs/234-f0c-release-targeted-first-training-task.md")

CHECKPOINT_PATH = Path(
    "outputs/robot_lab/t20_43c_r2_act_replacement_run_001/checkpoints/step_10000"
)
CHECKPOINT_IDENTITY = (
    "c77ee36250f921dbdfc7b19802ab8705c9795b298fa14d4a2b1825acf68451ab"
)
CHECKPOINT_TREE = (
    {
        "path": "config.json",
        "sha256": "1b2ba89880e421180962a0c862b37bfc854d16e5f8811e82210a64ecf6d09aaf",
        "size_bytes": 1714,
    },
    {
        "path": "model.safetensors",
        "sha256": "673c87a5c411997e5a0e146702df95a0e301ba8585ec1cba64dca25b6d55170c",
        "size_bytes": 206494928,
    },
)

SOURCE_IDENTITIES = {
    "r0_result": "d238379bce62d884833da0a449535e3dc24f988b8da573513ae684bbb19a5969",
    "r0_mixture": "37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df",
    "r0_statistics": "02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae",
    "r2_result": "bf2c8b466597ac23ff76ad88e8697b7b5d70a09b9016bc11442010243c984327",
    "r2_retention": "e565e17a5d4f8a52c4d894d3d61f03cf4b38beaf1df0bec3b83ade7f05afc023",
    "r2_final": "be11a258b6662baa10341acac13fe09055cd4ded7c2eaba4236d466977dfac5e",
    "f0": "807d3da7e21bbf3ec846454bb13aa6a2cb92eac4f6dffe8d86becb0ad777e5f9",
    "f0a": "278e8bc772dc879622a226abe22665d320421925045ad9b3cb1f88b1c31153a4",
    "f0b_spec": "ddf71cf91bcfcd4a1d40573a4ce5cfd648ee9dc141b3b6186bfbbd5fc16184ce",
    "f0b_result": "8fb34ff4a0619d59f414ec6bb81cb028fd5cf3d31bb26c4655a9dd41855f185d",
}

SOURCE_PATHS = {
    "r0_result": Path("configurations/robot_lab/t20_42_r0_generation_result.json"),
    "r0_mixture": Path(
        "configurations/robot_lab/t20_42_r0_dataset_mixture_manifest.json"
    ),
    "r0_statistics": Path(
        "configurations/robot_lab/t20_42_r0_dataset_statistics.json"
    ),
    "r2_result": Path(
        "configurations/robot_lab/t20_43c_r2_act_standard_result.json"
    ),
    "r2_retention": Path(
        "configurations/robot_lab/t20_43c_r2_act_retention_receipt.json"
    ),
    "r2_final": Path(
        "configurations/robot_lab/t20_43c_r2_act_final_receipt.json"
    ),
    "f0": Path("configurations/robot_lab/f0_release_gap_diagnosis.json"),
    "f0a": Path("configurations/robot_lab/f0a_chunk_phase_observability.json"),
    "f0b_spec": Path(
        "configurations/robot_lab/f0b_hybrid_tail_cadence_spec.json"
    ),
    "f0b_result": Path(
        "configurations/robot_lab/f0b_hybrid_tail_cadence_result.json"
    ),
}

JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]
PHYSICAL_L1_COEFFICIENTS = [
    0.013616426547530116,
    1.153008898269766,
    0.4279690527814028,
    0.7369730539120705,
    0.9721244211024305,
    2.6963081473868007,
]

FALSE_EXECUTION_FIELDS = {
    "attempt_marker_created": False,
    "checkpoint_tensor_read": False,
    "model_constructed": False,
    "model_loaded": False,
    "model_inference": False,
    "optimizer_created": False,
    "optimizer_training": False,
    "rollout_executed": False,
    "gate_c_executed": False,
    "gate_c_passed": False,
    "retry_authorized": False,
    "receding_10_authorized": False,
    "dataset_mutated": False,
    "statistics_mutated": False,
    "network_accessed": False,
    "external_compute_started": False,
    "brev_compute_started": False,
    "hardware_accessed": False,
    "physical_transfer_ready": False,
    "promotion_eligible": False,
}


def _require_unaliased_regular_file(path: Path, *, root: Path) -> None:
    relative = path.relative_to(root)
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"F0c input path is aliased: {relative.as_posix()}")
    if not path.is_file():
        raise ValueError(f"F0c input is not a regular file: {relative.as_posix()}")


def _sha_file(path: Path, *, root: Path) -> str:
    _require_unaliased_regular_file(path, root=root)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_ref(path: Path, *, repo_root: Path) -> dict[str, Any]:
    resolved = repo_root / path
    return {
        "path": path.as_posix(),
        "file_sha256": _sha_file(resolved, root=repo_root),
        "size_bytes": resolved.stat().st_size,
    }


def _signed_ref(
    name: str, payload: dict[str, Any], *, repo_root: Path
) -> dict[str, Any]:
    path = SOURCE_PATHS[name]
    return {
        **_file_ref(path, repo_root=repo_root),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
    }


def load_and_verify_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources: dict[str, Any] = {}
    for name, relative in SOURCE_PATHS.items():
        path = root / relative
        _require_unaliased_regular_file(path, root=root)
        payload = load_strict_json(path)
        verify_signed_payload(payload, label=f"F0c {name}")
        if payload.get("identity_sha256") != SOURCE_IDENTITIES[name]:
            raise ValueError(f"F0c source identity drifted: {name}")
        sources[name] = payload

    checkpoint = sources["f0b_spec"].get("checkpoint")
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("path") != CHECKPOINT_PATH.as_posix()
        or checkpoint.get("identity_sha256") != CHECKPOINT_IDENTITY
        or checkpoint.get("tree") != list(CHECKPOINT_TREE)
    ):
        raise ValueError("F0c immutable checkpoint reference drifted")
    for row in CHECKPOINT_TREE:
        path = root / CHECKPOINT_PATH / row["path"]
        if (
            path.stat().st_size != row["size_bytes"]
            or _sha_file(path, root=root) != row["sha256"]
        ):
            raise ValueError(f"F0c checkpoint byte drift: {row['path']}")

    findings = sources["f0"].get("findings")
    if not isinstance(findings, dict) or findings != {
        "gripper_physical_l1_underweight_supported": True,
        "normalization_defect": False,
        "release_mixture_underweight_defect": False,
        "tail_coverage_defect": False,
        "twenty_frame_release_sequence_delay_counterexample": True,
    }:
        raise ValueError("F0c diagnosis route drifted")
    return sources


def build_package(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = load_and_verify_sources(repo_root=root)
    source_refs = {
        name: _signed_ref(name, payload, repo_root=root)
        for name, payload in sorted(sources.items())
    }
    return sign_payload(
        {
            "schema_version": "scenesmith.f0c_release_targeted_continuation_spec.v1",
            "task_id": TASK_ID,
            "status": "packaged_for_fork_day_one",
            "activation_commit": ACTIVATION_COMMIT,
            "owner_direction_ref": _file_ref(OWNER_DIRECTION_PATH, repo_root=root),
            "brief_ref": _file_ref(BRIEF_PATH, repo_root=root),
            "source_refs": source_refs,
            "completion_budget": {
                "assessed_at": "2026-07-17T08:35:52-05:00",
                "cutoff": "2026-07-17T10:00:00-05:00",
                "available_seconds": 5048,
                "historical_r2_run_seconds": 7732,
                "historical_slowest_2500_update_seconds": 1983,
                "estimated_2000_update_seconds": 1586.4,
                "reviewed_boundary_count": 4,
                "reserve_seconds_per_reviewed_boundary": 1200,
                "minimum_complete_boundary_seconds": 6386.4,
                "shortfall_seconds": 1338.4,
                "execute_before_cutoff": False,
                "decision": "package_for_fork_day_one_without_marker_or_model_action",
            },
            "immutable_checkpoint": {
                "path": CHECKPOINT_PATH.as_posix(),
                "identity_sha256": CHECKPOINT_IDENTITY,
                "source_optimizer_update_count": 10000,
                "load_count_ceiling": 1,
                "tree": list(CHECKPOINT_TREE),
                "overwrite_allowed": False,
            },
            "dataset": {
                "root": "outputs/robot_lab/t20_42_r0_generation_run_001/lerobot_dataset",
                "repo_id": "scenesmith/t20-42-r0-anchor-grasp-train",
                "episode_count": 129,
                "frame_count": 31366,
                "window_count": 59904,
                "normalization": "MEAN_STD",
                "held_out_rows_in_training": 0,
                "mutation_allowed": False,
            },
            "continuation": {
                "device": "mps",
                "dtype": "float32",
                "training_seed": 20260801,
                "batch_size": 8,
                "maximum_optimizer_updates": 2000,
                "optimizer": "AdamW",
                "optimizer_state": "fresh_empty",
                "learning_rate": 1e-5,
                "backbone_learning_rate": 1e-5,
                "weight_decay": 1e-4,
                "gradient_clip_norm": 10.0,
                "scheduler": None,
                "one_attempt_only": True,
                "retry_or_sweep_allowed": False,
            },
            "release_correction": {
                "selected_mechanism": "phase_oversampling_plus_physical_l1_joint_weighting",
                "rejected_as_defects": [
                    "tail_window_starvation",
                    "open_gripper_normalization_headroom",
                    "aggregate_release_mixture_underweight",
                    "tail_cadence_only",
                ],
                "phase_start_importance_weights": {
                    "release": 4.0,
                    "release_settle": 4.0,
                    "all_other_eligible_phases": 1.0,
                },
                "sampler_requirements": [
                    "deterministic_seeded_stream",
                    "episode_boundaries_preserved",
                    "tail_padding_preserved",
                    "held_out_exclusion_preserved",
                    "full_importance_audit_retained",
                ],
                "joint_names": list(JOINT_NAMES),
                "normalized_l1_joint_coefficients": list(PHYSICAL_L1_COEFFICIENTS),
                "coefficient_formula": "f0_normalized_unit_to_physical_radian_jacobian_active_mean_one",
                "action_valid_mask_applied_before_reduction": True,
                "kl_and_non_action_terms_unchanged": True,
                "new_episode_generation": False,
            },
            "evaluation": {
                "variant": "chunk_50",
                "receding_10_in_scope": False,
                "simulation_seed": 0,
                "source_episode_index": 0,
                "frame_count": 244,
                "continuation_update_schedule": [0, 500, 1000, 2000],
                "update_0_retained_comparator_reproduction_required": True,
                "n_action_steps": 50,
                "queue_reset_count": 1,
                "decode_starts": [0, 50, 100, 150, 200],
                "executed_lengths": [50, 50, 50, 50, 44],
                "unexecuted_terminal_actions_masked": 6,
                "oracle": "strict_v2_only",
                "stop_and_preserve_on_first_gate_c_pass": True,
                "terminal_negative_if_no_pass_by_update": 2000,
            },
            "authority_requirements": [
                "implementation_reviewed_and_exact_on_origin",
                "fresh_owner_grant_attribution",
                "fresh_central_authority_request_and_decision",
                "fresh_runtime_preflight",
                "fresh_one_use_permit",
                "separate_pre_run_acceptance_exact_on_origin",
                "training_lock_mechanically_opened_by_central_composer",
                "marker_written_before_checkpoint_deserialization",
            ],
            "required_terminal_evidence": [
                "finite_losses_and_gradient_norms",
                "sampler_and_phase_importance_audit",
                "checkpoint_and_update_identities",
                "full_decoded_chunk_tensors",
                "all_244_executed_actions_and_observations",
                "strict_v2_per_frame_margins",
                "retained_comparator_hashes",
                "signed_mp4_and_manifest",
                "result_scorecard_retention_and_final_receipts",
                "independent_reconstruction",
            ],
            "day_one": {
                "package_check_command": "external/lerobot/.venv/bin/python scripts/robot_lab/write_f0c_release_targeted_package.py --check",
                "focused_test_command": "external/lerobot/.venv/bin/python -m unittest tests/unit/test_f0c_release_targeted_package.py",
                "future_execution_command": "external/lerobot/.venv/bin/python scripts/robot_lab/run_f0c_release_targeted_continuation.py --spec configurations/robot_lab/f0c_release_targeted_continuation_spec.json --started-at \"$(date -Iseconds)\"",
                "execution_entrypoint_implemented": False,
                "execution_requires_new_reviewed_slice": True,
            },
            **FALSE_EXECUTION_FIELDS,
        }
    )


def verify_package(payload: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> None:
    verify_signed_payload(payload, label="F0c release-targeted package")
    expected = build_package(repo_root=repo_root)
    if payload != expected:
        raise ValueError("F0c release-targeted package drifted")


def write_package(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    payload = build_package(repo_root=root)
    dump_canonical_json(root / SPEC_PATH, payload)
    verify_package(load_strict_json(root / SPEC_PATH), repo_root=root)
    return payload

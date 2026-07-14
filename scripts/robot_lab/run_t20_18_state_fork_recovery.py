#!/usr/bin/env python3
"""Capture T20.17 visited states and generate bounded T20.18 recovery forks."""

from __future__ import annotations

import hashlib
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.robot_lab.run_t20_17_clean_base_closed_loop import run_frozen_candidate
from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    _evaluate,
    phase_for_frame,
)
from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.causal_sort_expert import CausalSortExpert, CausalSortExpertConfig
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (
    all_robot_object_contact_geoms,
    nonpad_robot_object_contacts,
)
from scenesmith.robot_lab.gripper_contact_semantics import (
    FIXED_PAD_SITE,
    MOVING_PAD_SITE,
    aggregate_pad_contacts,
    apply_explicit_pad_proxy_contact_model,
    compiled_pad_geom_roles,
    extract_pad_contacts,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID, _bind_anchor_geometry, _raw_frame, _scene
from scenesmith.robot_lab.mujoco_export import prepare_mujoco_so101_assets, render_mujoco_xml
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    BASE_ANCHOR_POSITION_M,
    EPISODE_SPECS,
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.snapshot_branch_corrections import verify_snapshot_branch_manifest
from scenesmith.robot_lab.t20_17_clean_base_campaign import RUN_ROOT, RUN_SUMMARY_PATH, verify_run_summary
from scenesmith.robot_lab.t20_17_clean_base_preflight import SOURCE_MANIFEST_PATH
from scenesmith.robot_lab.t20_18_state_fork_recovery import (
    build_branch_record,
    build_recovery_manifest,
    capture_integration_state,
    restore_integration_state,
    select_parent_snapshots,
)


SEED = 6
T18_4_PATH = Path("configurations/robot_lab/t18_4_snapshot_branch_corrections.json")
RESULT_GATE_PATH = Path("configurations/robot_lab/t20_17_clean_base_result_gate.json")
EVALUATION_PATH = RUN_ROOT / "held_out_seed_6_closed_loop.json"
TRAINING_PATH = RUN_ROOT / RUN_SUMMARY_PATH
OUTPUT_PATH = Path("outputs/robot_lab/t20_18_state_fork_recovery.json")
GATE_PATH = Path("configurations/robot_lab/t20_18_state_fork_recovery_gate.json")


def main() -> int:
    output = REPO_ROOT / OUTPUT_PATH
    gate_path = REPO_ROOT / GATE_PATH
    if output.exists() or gate_path.exists():
        raise FileExistsError("T20.18 output already exists; immutable evidence cannot be overwritten")
    sources = _load_and_verify_sources()
    captures: list[dict[str, Any]] = []

    def capture(expert: Any, row: dict[str, Any], requested: np.ndarray) -> None:
        object_body = expert.cube_body_ids[OBJECT_ID]
        object_pose = np.concatenate(
            [expert.data.xpos[object_body], expert.data.xquat[object_body]]
        ).astype(float).tolist()
        captures.append(
            capture_integration_state(
                expert.mujoco,
                expert.model,
                expert.data,
                frame_index=row["frame_index"],
                phase=row["phase"],
                observation_state=row["mujoco_qpos"] + row["mujoco_qvel"],
                requested_action=requested.astype(float).tolist(),
                applied_action=row["mujoco_requested_action"],
                object_pose=object_pose,
                source_evaluation_identity_sha256=sources["evaluation"]["identity_sha256"],
            )
        )

    reproduced = run_frozen_candidate(simulator_state_observer=capture)
    _verify_exact_candidate_reproduction(sources["evaluation"], reproduced, captures)
    parents = select_parent_snapshots(captures)
    source_frames = sources["source_episode"]["frames"]
    branches: list[dict[str, Any]] = []
    for parent_index, parent in enumerate(parents):
        start = parent["frame_index"]
        suffix = source_frames[start:]
        actions = [row["actions"]["measured"]["values"] for row in suffix]
        action_ids = [row["record_identity_sha256"] for row in suffix]
        perturbations = (
            ("nominal", {"joint_delta_rad": [0.0] * 6}),
            (
                "bounded_joint_offset",
                {
                    "joint_delta_rad": [
                        0.01 if joint == parent_index % 5 else 0.0 for joint in range(6)
                    ]
                },
            ),
        )
        for label, perturbation in perturbations:
            first = _run_branch(parent, perturbation, actions)
            second = _run_branch(parent, perturbation, actions)
            first_sha = _sha_value(first)
            second_sha = _sha_value(second)
            branch = build_branch_record(
                parent,
                generation_reason=f"{parent['phase_role']}_{label}_measured_source_suffix",
                perturbation=perturbation,
                measured_actions=actions,
                action_source_record_ids=action_ids,
                observed_result=first["observed_result"],
                replay_evidence={
                    "first_trace_sha256": first_sha,
                    "second_trace_sha256": second_sha,
                    "frame_count": first["frame_count"],
                    "absolute_tolerance": 0.0,
                },
            )
            branch["trace_summary"] = first
            unsigned = {key: value for key, value in branch.items() if key != "branch_id"}
            branch["branch_id"] = _sha_value(unsigned)
            branches.append(branch)

    manifest = build_recovery_manifest(
        source_refs=sources["source_refs"],
        t18_4_identity_sha256=sources["t18_4"]["identity_sha256"],
        t20_17_evaluation_identity_sha256=sources["evaluation"]["identity_sha256"],
        t20_17_action_sequence_sha256=sources["evaluation"]["closed_loop"][
            "policy_action_sequence_sha256"
        ],
        reproduced_action_sequence_sha256=reproduced["closed_loop"][
            "policy_action_sequence_sha256"
        ],
        reproduced_terminal_outcome=reproduced["closed_loop"]["terminal_outcome"],
        parents=parents,
        branches=branches,
    )
    dump_canonical_json(output, manifest)
    counts = Counter(row["outcome_class"] for row in branches)
    gate = sign_payload(
        {
            "schema_version": "scenesmith.t20_18_state_fork_recovery_gate.v1",
            "task_id": "T20.18",
            "artifact_path": OUTPUT_PATH.as_posix(),
            "artifact_file_sha256": _sha_file(output),
            "artifact_identity_sha256": manifest["identity_sha256"],
            "parent_count": len(parents),
            "branch_count": len(branches),
            "outcome_class_counts": dict(sorted(counts.items())),
            "exact_candidate_reproduced": True,
            "deterministic_replay_verified": True,
            "actions_padded": False,
            "actions_inferred": False,
            "optimizer_training": False,
            "dataset_mixture_frozen": False,
            "simulation_training_ready": False,
            "simulation_policy_accepted": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_granted": ["t20_18_state_fork_recovery_evidence_generated"],
            "authority_not_granted": [
                "optimizer_training",
                "dataset_mixture_frozen",
                "simulation_training_ready",
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )
    dump_canonical_json(gate_path, gate)
    print(manifest["identity_sha256"], gate["identity_sha256"], dict(counts))
    return 0


def _load_and_verify_sources() -> dict[str, Any]:
    t18_4_path = REPO_ROOT / T18_4_PATH
    result_path = REPO_ROOT / RESULT_GATE_PATH
    evaluation_path = REPO_ROOT / EVALUATION_PATH
    training_path = REPO_ROOT / TRAINING_PATH
    t18_4 = load_strict_json(t18_4_path)
    result = load_strict_json(result_path)
    evaluation = load_strict_json(evaluation_path)
    training = load_strict_json(training_path)
    verify_snapshot_branch_manifest(t18_4)
    verify_signed_payload(result, label="T20.17 result gate")
    verify_signed_payload(evaluation, label="T20.17 evaluation")
    verify_signed_payload(training, label="T20.17 training summary")
    verify_run_summary(training)
    if result["evaluation_ref"]["file_sha256"] != _sha_file(evaluation_path):
        raise ValueError("T20.17 result gate evaluation binding drifted")
    if result["training_ref"]["file_sha256"] != _sha_file(training_path):
        raise ValueError("T20.17 result gate training binding drifted")
    source_manifest = load_strict_json(REPO_ROOT / SOURCE_MANIFEST_PATH)
    verify_episode_store(source_manifest, default_store_root())
    entry = next(row for row in source_manifest["episodes"] if row["seed"] == SEED)
    source_path = default_store_root() / entry["relative_path"]
    if _sha_file(source_path) != entry["episode_file_sha256"]:
        raise ValueError("T20.18 held-out source episode drifted")
    source_episode = load_strict_json(source_path)
    adapter_rel = Path("training/checkpoints/last/pretrained_model/adapter_model.safetensors")
    adapter_path = REPO_ROOT / RUN_ROOT / adapter_rel
    adapter_row = next(
        row for row in training["checkpoint_tree"] if row["path"] == "adapter_model.safetensors"
    )
    if _sha_file(adapter_path) != adapter_row["sha256"]:
        raise ValueError("T20.18 adapter bytes drifted")

    def ref(path: Path, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        row = {"path": path.relative_to(REPO_ROOT).as_posix(), "file_sha256": _sha_file(path)}
        if payload is not None:
            row["identity_sha256"] = payload["identity_sha256"]
        return row

    source_refs = {
        "t18_4_manifest": ref(t18_4_path, t18_4),
        "t20_17_result_gate": ref(result_path, result),
        "t20_17_evaluation": ref(evaluation_path, evaluation),
        "t20_17_training_summary": ref(training_path, training),
        "t20_17_adapter": ref(adapter_path),
        "held_out_source_episode": {
            "path": source_path.relative_to(REPO_ROOT).as_posix(),
            "file_sha256": _sha_file(source_path),
            "identity_sha256": entry["raw_rollout_record_identity_sha256"],
        },
    }
    return {
        "t18_4": t18_4,
        "result": result,
        "evaluation": evaluation,
        "training": training,
        "source_episode": source_episode,
        "source_refs": source_refs,
    }


def _verify_exact_candidate_reproduction(
    expected: dict[str, Any], reproduced: dict[str, Any], captures: list[dict[str, Any]]
) -> None:
    if canonical_json_bytes(expected) != canonical_json_bytes(reproduced):
        raise ValueError("T20.18 candidate replay did not reproduce exact T20.17 evidence")
    if len(captures) != expected["closed_loop"]["frame_count"]:
        raise ValueError("T20.18 visited-state capture count drifted")


def _run_branch(
    parent: dict[str, Any], perturbation: dict[str, Any], actions: list[list[float]]
) -> dict[str, Any]:
    spec = next(row for row in EPISODE_SPECS if row["seed"] == SEED)
    offset_x, offset_y = spec["planar_offset_m"]
    initial_position = np.asarray(
        [
            BASE_ANCHOR_POSITION_M[0] + offset_x,
            BASE_ANCHOR_POSITION_M[1] + offset_y,
            BASE_ANCHOR_POSITION_M[2],
        ],
        dtype=np.float64,
    )
    scene = _scene(initial_position_m=initial_position.tolist())
    frames: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="scenesmith-t20-18-branch-") as directory:
        root = Path(directory)
        robot_xml = prepare_mujoco_so101_assets(root, scene.robot.base_position_m)
        apply_explicit_pad_proxy_contact_model(robot_xml)
        scene_xml = root / "scene.xml"
        scene_xml.write_text(render_mujoco_xml(scene), encoding="utf-8")
        _bind_anchor_geometry(scene_xml)
        expert: CausalSortExpert | None = None
        pad_roles: dict[int, str] = {}
        object_body = fixed_site = moving_site = -1

        def retain(frame: dict[str, Any], images: dict[str, np.ndarray]) -> None:
            del images
            assert expert is not None
            row = _raw_frame(expert, frame)
            contacts = extract_pad_contacts(
                expert.mujoco,
                expert.model,
                expert.data,
                object_body_id=object_body,
                pad_geom_roles=pad_roles,
            )
            rotation = np.asarray(expert.data.xmat[object_body]).reshape(3, 3)
            closing_world = expert.data.site_xpos[moving_site] - expert.data.site_xpos[fixed_site]
            closing_object = rotation.T @ closing_world
            row["pad_contacts"] = contacts
            row["pad_contact_aggregate"] = (
                aggregate_pad_contacts(contacts, closing_object.tolist()) if contacts else None
            )
            row["nonpad_robot_object_contacts"] = nonpad_robot_object_contacts(
                expert, object_body, set(pad_roles)
            )
            row["all_robot_object_contact_geoms"] = all_robot_object_contact_geoms(
                expert, object_body
            )
            frames.append(row)

        expert = CausalSortExpert(
            scene,
            scene_xml,
            seed=1701 + SEED,
            frame_sink=retain,
            config=CausalSortExpertConfig(image_size=256, capture_images=False),
        )
        try:
            pad_roles = compiled_pad_geom_roles(expert.mujoco, expert.model)
            fixed_site = expert._id(expert.mujoco.mjtObj.mjOBJ_SITE, FIXED_PAD_SITE)
            moving_site = expert._id(expert.mujoco.mjtObj.mjOBJ_SITE, MOVING_PAD_SITE)
            object_body = expert.cube_body_ids[OBJECT_ID]
            restore_integration_state(expert.mujoco, expert.model, expert.data, parent)
            joint_delta = np.asarray(perturbation.get("joint_delta_rad", [0.0] * 6))
            expert.data.qpos[: expert.model.nu] += joint_delta
            lower = expert.model.jnt_range[: expert.model.nu, 0]
            upper = expert.model.jnt_range[: expert.model.nu, 1]
            if np.any(expert.data.qpos[: expert.model.nu] < lower) or np.any(
                expert.data.qpos[: expert.model.nu] > upper
            ):
                raise ValueError("T20.18 branch perturbation exits robot joint bounds")
            expert.mujoco.mj_forward(expert.model, expert.data)
            expert.frame_index = parent["frame_index"]
            for offset, action in enumerate(actions):
                frame_index = parent["frame_index"] + offset
                expert._record_and_step(phase_for_frame(frame_index), np.asarray(action))
            anchor_final = expert.data.xpos[object_body].copy()
            final_state = np.empty(
                expert.mujoco.mj_stateSize(
                    expert.model, expert.mujoco.mjtState.mjSTATE_INTEGRATION
                )
            )
            expert.mujoco.mj_getState(
                expert.model,
                expert.data,
                final_state,
                expert.mujoco.mjtState.mjSTATE_INTEGRATION,
            )
        finally:
            expert.close()
    evidence = _evaluate(
        frames,
        anchor_start=initial_position,
        anchor_final=anchor_final,
        projected_frames=[],
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    )
    observed = {
        "simulation_semantic_strict_success": evidence["simulation_semantic_strict_success"],
        "strict_contact_frame_count": sum(evidence["strict_v2_valid_frame_counts"].values()),
        "maximum_anchor_lift_m": evidence["maximum_anchor_lift_m"],
    }
    return {
        "frame_count": len(frames),
        "frame_records_sha256": _sha_value(frames),
        "final_integration_state_sha256": _sha_value(final_state.astype(float).tolist()),
        "terminal_outcome": evidence["terminal_outcome"],
        "observed_result": observed,
    }


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha_value(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

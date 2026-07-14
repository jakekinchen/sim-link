"""Append-only generation of source-bound scripted MuJoCo grasp episodes."""

from __future__ import annotations

import hashlib
import json
import os

from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.experience_compiler import (
    compile_projections,
    verify_compilation,
    write_compilation,
)
from scenesmith.robot_lab.experience_records import (
    ACTION_VARIANTS,
    CONTRACT_PATH,
    FRAME_SCHEMA_VERSION,
    JOINT_NAMES,
    RAW_ROLLOUT_SCHEMA_VERSION,
    REPO_ROOT,
    sign_record,
    validate_frame_records,
    validate_raw_rollout_record,
    verify_experience_record_contract,
)
from scenesmith.robot_lab.geometry_derived_unilateral_grasp import (
    SCHEMA_VERSION as GRASP_SCHEMA_VERSION,
)
from scenesmith.robot_lab.geometry_first_grasp_search import _run_candidate
from scenesmith.robot_lab.grasp_evidence import (
    KEYFRAME_IMAGE_SIZE,
    encode_png_image,
    validate_rendered_keyframes,
)
from scenesmith.robot_lab.strict_grasp import (
    evaluate_antipodal_contact_witness,
    strict_grasp_spec_v2,
)


SCHEMA_VERSION = "scenesmith.scripted_grasp_episode_store.v1"
STORE_RELATIVE_ROOT = Path("outputs/robot_lab/t17_5b_raw_store")
MANIFEST_PATH = Path("configurations/robot_lab/t17_5b_episode_generation_manifest.json")
COMPILE_OUTPUT_DIR = Path("configurations/robot_lab/t17_5b_compile")
WINDOW_OUTPUT_DIR = Path("configurations/robot_lab/t17_5b_window_index")
NORMALIZATION_PATH = Path("configurations/robot_lab/normalization_bundle.json")
GEOMETRY_GRASP_PATH = Path("configurations/robot_lab/geometry_derived_unilateral_grasp.json")
BASE_ANCHOR_POSITION_M = (0.22, 0.0, 0.325)
RECORDING_STABLE_HOLD_FRAMES = 64
PROMPT_TEXT = "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."

EPISODE_SPECS = (
    {"seed": 0, "planar_offset_m": [0.0, 0.0], "yaw_offset_rad": 0.0},
    {"seed": 1, "planar_offset_m": [0.001, 0.0], "yaw_offset_rad": 0.015},
    {"seed": 2, "planar_offset_m": [-0.001, 0.0], "yaw_offset_rad": -0.015},
    {"seed": 3, "planar_offset_m": [0.0, 0.001], "yaw_offset_rad": 0.03},
    {"seed": 4, "planar_offset_m": [0.0, -0.001], "yaw_offset_rad": -0.03},
    {"seed": 5, "planar_offset_m": [0.001, 0.001], "yaw_offset_rad": 0.01},
    {"seed": 6, "planar_offset_m": [-0.001, 0.001], "yaw_offset_rad": -0.01},
    {"seed": 7, "planar_offset_m": [0.001, -0.001], "yaw_offset_rad": 0.0},
)

_PHASES = {
    "approach": "approach",
    "pregrasp": "pregrasp",
    "close": "close",
    "grasp_hold": "grasp_confirmed",
    "unassisted_lift": "lift",
    "unsupported_lift_hold": "stable_hold",
    "recording_stable_hold": "stable_hold",
    "lower": "lower",
    "release": "release",
    "release_settle": "release",
    "retreat": "retreat",
}


def default_store_root(*, repo_root: Path = REPO_ROOT) -> Path:
    return repo_root / STORE_RELATIVE_ROOT


def generate_episode_payload(spec: dict[str, Any]) -> dict[str, Any]:
    """Run one bounded unassisted episode and convert it into raw records."""

    _validate_episode_spec(spec)
    contract = load_strict_json(REPO_ROOT / CONTRACT_PATH)
    verify_experience_record_contract(contract, repo_root=REPO_ROOT)
    grasp = load_strict_json(REPO_ROOT / GEOMETRY_GRASP_PATH)
    verify_signed_payload(grasp, label="geometry-derived source grasp")
    if grasp.get("schema_version") != GRASP_SCHEMA_VERSION or not grasp.get(
        "unassisted_mujoco_grasp_success"
    ):
        raise ValueError("Geometry-derived source grasp is not an accepted simulation proof")

    captured: list[tuple[dict[str, Any], dict[str, np.ndarray]]] = []

    def retain(frame: dict[str, Any], images: dict[str, np.ndarray]) -> None:
        captured.append((frame, images))

    request = dict(grasp["trajectory"]["request"])
    request["object_yaw_rad"] += spec["yaw_offset_rad"]
    offset_x, offset_y = spec["planar_offset_m"]
    result = _run_candidate(
        request,
        explicit_pad_proxy_only=True,
        pad_midpoint_targeting=True,
        post_yaw_settle_seconds=grasp["trajectory"]["post_yaw_settle_seconds"],
        best_principal_axis_alignment=True,
        center_selected_axis_offset=True,
        close_target_override_rad=grasp["derivation"]["derived_close_target_rad"],
        vertical_target_override_m=grasp["derivation"]["pad_midpoint_vertical_offset_m"],
        selected_axis_clearance_m=grasp["derivation"]["fixed_jaw_clearance_m"],
        execute_full_lift_cycle=True,
        capture_keyframes=True,
        recording_stable_hold_frames=RECORDING_STABLE_HOLD_FRAMES,
        scene_initial_position_m=(
            BASE_ANCHOR_POSITION_M[0] + offset_x,
            BASE_ANCHOR_POSITION_M[1] + offset_y,
            BASE_ANCHOR_POSITION_M[2],
        ),
        recording_sink=retain,
    )
    if len(captured) != sum(result["full_lift_cycle"]["phase_frame_counts"].values()) + 14 + 18 + 36 + 12 + RECORDING_STABLE_HOLD_FRAMES:
        raise ValueError("Recorded frame count is inconsistent with scripted phase plan")
    payload = _build_episode_payload(
        captured,
        spec=spec,
        contract=contract,
        grasp=grasp,
        result=result,
    )
    raw = payload["raw_rollout"]
    validate_raw_rollout_record(raw, contract["source_grasp_artifact_ref"])
    validate_frame_records(payload["frames"], raw)
    validate_rendered_keyframes(payload["rendered_keyframes"])
    return payload


def generate_store(store_root: Path) -> dict[str, Any]:
    """Generate the fixed episode set into an append-only content-addressed root."""

    store_root = Path(store_root)
    store_root.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for spec in EPISODE_SPECS:
        try:
            payload = generate_episode_payload(dict(spec))
        except (RuntimeError, ValueError) as exc:
            if spec["seed"] == 0:
                raise ValueError("Seed 0 failed the verified scripted grasp replay") from exc
            failures.append(
                {
                    "seed": spec["seed"],
                    "spec": spec,
                    "terminal_outcome": "runtime_failure",
                    "strict_success": False,
                    "error": str(exc),
                }
            )
            continue
        entry = _write_episode_payload(payload, store_root)
        entries.append(entry)
    manifest = _build_store_manifest(entries, failures)
    verify_episode_store(manifest, store_root)
    return manifest


def verify_episode_store(manifest: dict[str, Any], store_root: Path) -> None:
    """Verify all referenced append-only raw bytes and record contracts."""

    verify_signed_payload(manifest, label="scripted grasp episode store manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Episode-store manifest schema drifted")
    if manifest.get("store_root") != str(STORE_RELATIVE_ROOT):
        raise ValueError("Episode-store root drifted")
    if manifest.get("configured_episode_count") != len(EPISODE_SPECS):
        raise ValueError("Episode-store configured count drifted")
    if manifest.get("episode_specs") != list(EPISODE_SPECS):
        raise ValueError("Episode-store fixed episode specification drifted")
    contract = load_strict_json(REPO_ROOT / CONTRACT_PATH)
    grasp = load_strict_json(REPO_ROOT / GEOMETRY_GRASP_PATH)
    verify_experience_record_contract(contract, repo_root=REPO_ROOT)
    verify_signed_payload(grasp, label="geometry-derived source grasp")
    if manifest.get("source_experience_identity_sha256") != contract.get(
        "identity_sha256"
    ):
        raise ValueError("Episode-store source experience identity drifted")
    if manifest.get("source_grasp_identity_sha256") != grasp.get("identity_sha256"):
        raise ValueError("Episode-store source grasp identity drifted")
    entries = manifest.get("episodes")
    failures = manifest.get("runtime_failures")
    if not isinstance(entries, list) or not isinstance(failures, list):
        raise ValueError("Episode-store entries are invalid")
    if manifest.get("realized_episode_count") != len(entries):
        raise ValueError("Episode-store realized count drifted")
    if len(entries) + len(failures) != len(EPISODE_SPECS):
        raise ValueError("Episode-store configured/realized accounting drifted")
    store_root = Path(store_root).resolve()
    seen_seeds: set[int] = set()
    for entry in entries:
        seed = _require_seed(entry.get("seed"))
        if seed in seen_seeds:
            raise ValueError("Episode-store seed is duplicated")
        if entry.get("spec") != EPISODE_SPECS[seed]:
            raise ValueError("Episode-store episode specification drifted")
        seen_seeds.add(seed)
        path = _resolve_store_path(store_root, entry.get("relative_path"))
        if not path.is_file() or _sha256_file(path) != entry.get("episode_file_sha256"):
            raise ValueError("Episode-store raw byte hash drifted")
        payload = load_strict_json(path)
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Episode payload schema drifted")
        raw = payload.get("raw_rollout")
        validate_raw_rollout_record(raw, contract["source_grasp_artifact_ref"])
        validate_frame_records(payload.get("frames"), raw)
        validate_rendered_keyframes(payload.get("rendered_keyframes"))
        if raw.get("record_identity_sha256") != entry.get("raw_rollout_record_identity_sha256"):
            raise ValueError("Episode-store raw rollout identity drifted")
        if entry.get("frame_count") != len(payload.get("frames", [])):
            raise ValueError("Episode-store frame count drifted")
        outcome = payload.get("outcome")
        if outcome != entry.get("outcome"):
            raise ValueError("Episode-store outcome drifted")
        if seed == 0:
            if not outcome.get("strict_success"):
                raise ValueError("Seed 0 does not retain strict success")
            validate_rendered_keyframes(entry.get("proof_keyframes"))
        elif not outcome.get("strict_success"):
            validate_rendered_keyframes(entry.get("proof_keyframes"))
    for failure in failures:
        seed = _require_seed(failure.get("seed"))
        if seed in seen_seeds or failure.get("terminal_outcome") != "runtime_failure":
            raise ValueError("Episode-store runtime failure accounting drifted")
        if failure.get("spec") != EPISODE_SPECS[seed]:
            raise ValueError("Episode-store runtime failure specification drifted")
        if failure.get("strict_success") is not False:
            raise ValueError("Episode-store runtime failure strict-success drifted")
        seen_seeds.add(seed)
    if seen_seeds != {spec["seed"] for spec in EPISODE_SPECS}:
        raise ValueError("Episode-store seed coverage drifted")
    for field in (
        "training_eligible",
        "simulation_training_ready",
        "optimizer_training",
        "physical_actuation",
        "raw_bytes_rewritten",
    ):
        if manifest.get(field) is not False:
            raise ValueError(f"Episode-store authority flag drifted: {field}")


def compile_episode_store(
    manifest: dict[str, Any],
    store_root: Path,
    output_dir: Path,
    *,
    manifest_file_sha256: str,
) -> dict[str, Any]:
    """Compile the store into a new T17.4-path frame and segment view."""

    verify_episode_store(manifest, store_root)
    normalization = load_strict_json(REPO_ROOT / NORMALIZATION_PATH)
    projections = []
    for entry in manifest["episodes"]:
        payload = load_strict_json(_resolve_store_path(Path(store_root).resolve(), entry["relative_path"]))
        projections.append(
            {"raw_rollout": payload["raw_rollout"], "frames": payload["frames"]}
        )
    if not projections:
        raise ValueError("Episode store has no realizable raw rollouts")
    result = compile_projections(
        projections,
        source_experience_identity=load_strict_json(REPO_ROOT / CONTRACT_PATH)["identity_sha256"],
        source_normalization_identity=normalization["identity_sha256"],
        source_episode_store_manifest_sha256=manifest_file_sha256,
    )
    written = write_compilation(result, Path(output_dir))
    verify_compilation(Path(output_dir))
    if written["manifest"]["eligible_frame_count"] <= 0 or written["manifest"]["segment_count"] <= 0:
        raise ValueError("Generated episode compilation is empty")
    return written


def _build_episode_payload(
    captured: list[tuple[dict[str, Any], dict[str, np.ndarray]]],
    *,
    spec: dict[str, Any],
    contract: dict[str, Any],
    grasp: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    if not captured:
        raise ValueError("Scripted episode captured no frames")
    timestamps = [_timestamp_ns(frame["time_s"]) for frame, _images in captured]
    if timestamps != sorted(set(timestamps)):
        raise ValueError("Captured simulator timestamps are not strictly increasing")
    raw_payload = {
        "generator_schema_version": SCHEMA_VERSION,
        "source_grasp_identity_sha256": grasp["identity_sha256"],
        "episode_spec": spec,
        "recording_stable_hold_frames": RECORDING_STABLE_HOLD_FRAMES,
        "captured_frame_count": len(captured),
    }
    raw_payload_sha256 = _sha256(raw_payload)
    raw = {
        "schema_version": RAW_ROLLOUT_SCHEMA_VERSION,
        "rollout_id": f"rollout-{raw_payload_sha256[:24]}",
        "source_class": "mujoco_expert",
        "proof_mode": "simulation_unassisted",
        "controller_owner": "geometry_derived_mujoco_expert",
        "control_mode": "scripted_mujoco_expert",
        "prompt": {"text": PROMPT_TEXT, "identity_sha256": _sha256(PROMPT_TEXT)},
        "object_identity": "simulation_anchor_50x35x30mm",
        "workcell_identity": "scenesmith_mujoco_anchor_fixture",
        "environment_identity": "geometry_derived_unilateral_grasp_v1",
        "coordinate_contract_ref": contract["coordinate_contract_ref"],
        "preprocessing_identity": "not_applicable_simulator_state_projection",
        "twin_profile_ref": contract["twin_profile_ref"],
        "source_artifact_ref": contract["source_grasp_artifact_ref"],
        "start_timestamp_ns": timestamps[0],
        "end_timestamp_ns": timestamps[-1],
        "frame_count": len(captured),
        "raw_payload_append_only": True,
        "raw_payload": raw_payload,
        "raw_payload_sha256": raw_payload_sha256,
        "evidence": [
            {
                "kind": "signed_simulation_artifact",
                "ref": contract["source_grasp_artifact_ref"]["path"],
                "sha256": contract["source_grasp_artifact_ref"]["file_sha256"],
            }
        ],
    }
    raw = sign_record(raw)
    frames = _build_frames(captured, raw=raw)
    outcome = _outcome(result, spec)
    return {
        "schema_version": SCHEMA_VERSION,
        "episode_spec": spec,
        "raw_rollout": raw,
        "frames": frames,
        "outcome": outcome,
        "rendered_keyframes": result["rendered_keyframes"],
        "source_grasp_identity_sha256": grasp["identity_sha256"],
        "raw_bytes_rewritten": False,
        "training_eligible": False,
        "simulation_training_ready": False,
        "optimizer_training": False,
        "physical_actuation": False,
    }


def _build_frames(
    captured: list[tuple[dict[str, Any], dict[str, np.ndarray]]], *, raw: dict[str, Any]
) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    prior_phase: str | None = None
    phase_order = list(_PHASES)
    for index, (source, images) in enumerate(captured):
        source_phase = source.get("phase")
        task_phase = _PHASES.get(source_phase)
        if task_phase is None:
            raise ValueError(f"Recorded source phase is unsupported: {source_phase!r}")
        requested = _six_values(source.get("mujoco_requested_action"), "requested action")
        achieved = _six_values(source.get("mujoco_qpos"), "joint position")
        velocities = _six_values(source.get("mujoco_qvel"), "joint velocity")
        effort = _six_values(source.get("mujoco_actuator_effort"), "actuator effort")
        strict_valid = _strict_valid(source)
        events: list[str] = []
        if index == 0:
            events.extend(["rollout_start", "reset", "scene_change"])
        if source_phase != prior_phase:
            events.append("phase_change")
        if index == len(captured) - 1:
            events.append("rollout_end")
        pointer = f"/raw_episode/frames/{index}"
        frame = {
            "schema_version": FRAME_SCHEMA_VERSION,
            "frame_id": f"{raw['rollout_id']}-frame-{index:06d}",
            "rollout_id": raw["rollout_id"],
            "frame_index": index,
            "timestamp_ns": _timestamp_ns(source["time_s"]),
            "task_phase": task_phase,
            "source_phase": source_phase,
            "source_class": raw["source_class"],
            "proof_mode": raw["proof_mode"],
            "controller_owner": raw["controller_owner"],
            "control_mode": raw["control_mode"],
            "actions": _actions(requested, raw["source_artifact_ref"], pointer),
            "requested_gripper_pose": _sourced(
                requested[5], raw["source_artifact_ref"], pointer + "/mujoco_requested_action/5"
            ),
            "achieved_gripper_pose": _sourced(
                achieved[5], raw["source_artifact_ref"], pointer + "/mujoco_qpos/5"
            ),
            "contact_geometry_witness": _sourced(
                {
                    "strict_v2_valid": strict_valid,
                    "pad_contact_present": bool(source.get("pad_contact_aggregate")),
                    "nonpad_robot_object_contact": bool(source.get("nonpad_robot_object_contacts")),
                },
                raw["source_artifact_ref"],
                pointer + "/contact_geometry",
                units="structured",
            ),
            "aperture": _sourced(
                requested[5], raw["source_artifact_ref"], pointer + "/mujoco_requested_action/5"
            ),
            "effort": _sourced(
                effort, raw["source_artifact_ref"], pointer + "/mujoco_actuator_effort", units="newton_meter"
            ),
            "reward": _derived_reward(float(strict_valid), raw["source_artifact_ref"], pointer),
            "progress": _derived_progress(
                float(phase_order.index(source_phase) + 1) / len(phase_order),
                raw["source_artifact_ref"],
                pointer,
            ),
            "strict_evaluator_result": {
                "valid": strict_valid,
                "evaluator": "strict_anchor_grasp_evaluator_v2",
                "provenance": _provenance(raw["source_artifact_ref"], pointer + "/pad_contact_aggregate"),
            },
            "boundary_events": sorted(set(events)),
            "actor_input_field_names": [
                "observation.top_rgb",
                "observation.wrist_rgb",
                "observation.joint_position",
                "observation.joint_velocity",
            ],
            "observations": {
                "top": encode_png_image(images["top"], image_size=KEYFRAME_IMAGE_SIZE),
                "wrist": encode_png_image(images["wrist"], image_size=KEYFRAME_IMAGE_SIZE),
                "joint_position_mujoco_rad": achieved,
                "joint_velocity_mujoco_rad_s": velocities,
            },
        }
        frame["record_identity_sha256"] = sign_record(frame)["record_identity_sha256"]
        frames.append(frame)
        prior_phase = source_phase
    return frames


def _actions(
    requested: list[float], source_ref: dict[str, Any], pointer: str
) -> dict[str, dict[str, Any]]:
    actions: dict[str, dict[str, Any]] = {
        "requested": {
            "state": "observed",
            "representation": "absolute_joint_radians_plus_gripper_radians",
            "units": "radian",
            "ordered_joint_names": list(JOINT_NAMES),
            "values": requested,
            "provenance": _provenance(source_ref, pointer + "/mujoco_requested_action"),
            "reason": None,
        }
    }
    for variant in ACTION_VARIANTS[1:]:
        actions[variant] = {
            "state": "derived",
            "representation": "absolute_joint_radians_plus_gripper_radians",
            "units": "radian",
            "ordered_joint_names": list(JOINT_NAMES),
            "values": requested,
            "provenance": _provenance(
                source_ref,
                pointer + "/mujoco_requested_action",
                derivation=(
                    "scripted MuJoCo expert has no separate proposal, projection, "
                    "transport, or actuator-command stage; value equals requested action"
                ),
            ),
            "reason": None,
        }
    return actions


def _outcome(result: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    cycle = result["full_lift_cycle"]
    strict_counts = cycle["strict_v2_valid_frame_counts"]
    required = {
        "grasp_hold": 8,
        "unassisted_lift": 24,
        "unsupported_lift_hold": 12,
        "lower": 24,
    }
    cycle_margins = {
        f"{name}_strict_v2": _margin(strict_counts.get(name), count, ">=")
        for name, count in required.items()
    }
    cycle_margins["unsupported_lift_support_free"] = _margin(
        cycle.get("unsupported_lift_hold_frame_count"),
        required["unsupported_lift_hold"],
        ">=",
    )
    assist_count = cycle.get("active_assist_frame_count")
    cycle_margins["active_assist_frames"] = {
        "measured": assist_count,
        "threshold": 0,
        "comparison": "==",
        "margin": -assist_count if isinstance(assist_count, int) else None,
        "passed": assist_count == 0,
    }
    original_cycle_valid = all(margin["passed"] for margin in cycle_margins.values())
    recording_hold = result.get("recording_stable_hold")
    if not isinstance(recording_hold, dict):
        raise ValueError("Recording stable hold is missing")
    hold_valid = recording_hold.get("strict_v2_valid_frame_count") == RECORDING_STABLE_HOLD_FRAMES
    strict_success = bool(result.get("setup_valid") and original_cycle_valid and hold_valid)
    margins = {**dict(result.get("gate_margins", {})), **cycle_margins}
    margins["recording_stable_hold_strict_v2"] = _margin(
        recording_hold.get("strict_v2_valid_frame_count"),
        RECORDING_STABLE_HOLD_FRAMES,
        ">=",
    )
    return {
        "seed": spec["seed"],
        "terminal_outcome": "strict_success" if strict_success else "strict_failure",
        "strict_success": strict_success,
        "strict_v2_valid_frame_counts": strict_counts,
        "recording_stable_hold": recording_hold,
        "gate_margins": margins,
        "failed_gate_margins": [
            {"gate": name, **margin}
            for name, margin in margins.items()
            if not margin["passed"]
        ],
    }


def _write_episode_payload(payload: dict[str, Any], store_root: Path) -> dict[str, Any]:
    temporary = store_root / ".episode.tmp.json"
    dump_canonical_json(temporary, payload)
    content = temporary.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    relative_path = f"{digest}.json"
    destination = store_root / relative_path
    if destination.exists():
        if destination.read_bytes() != content:
            raise ValueError("Append-only episode store hash collision")
        temporary.unlink()
    else:
        os.replace(temporary, destination)
    outcome = payload["outcome"]
    proof_keyframes = (
        payload["rendered_keyframes"]
        if payload["episode_spec"]["seed"] == 0 or not outcome["strict_success"]
        else []
    )
    return {
        "seed": payload["episode_spec"]["seed"],
        "spec": payload["episode_spec"],
        "relative_path": relative_path,
        "episode_file_sha256": digest,
        "raw_rollout_record_identity_sha256": payload["raw_rollout"]["record_identity_sha256"],
        "frame_count": len(payload["frames"]),
        "outcome": outcome,
        "proof_keyframes": proof_keyframes,
    }


def _build_store_manifest(
    entries: list[dict[str, Any]], failures: list[dict[str, Any]]
) -> dict[str, Any]:
    contract = load_strict_json(REPO_ROOT / CONTRACT_PATH)
    grasp = load_strict_json(REPO_ROOT / GEOMETRY_GRASP_PATH)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "store_root": str(STORE_RELATIVE_ROOT),
            "source_experience_identity_sha256": contract["identity_sha256"],
            "source_grasp_identity_sha256": grasp["identity_sha256"],
            "episode_specs": list(EPISODE_SPECS),
            "configured_episode_count": len(EPISODE_SPECS),
            "realized_episode_count": len(entries),
            "runtime_failure_count": len(failures),
            "episodes": entries,
            "runtime_failures": failures,
            "recording_stable_hold_frames": RECORDING_STABLE_HOLD_FRAMES,
            "raw_bytes_rewritten": False,
            "training_eligible": False,
            "simulation_training_ready": False,
            "optimizer_training": False,
            "physical_actuation": False,
        }
    )


def _strict_valid(source: dict[str, Any]) -> bool:
    aggregate = source.get("pad_contact_aggregate")
    if not isinstance(aggregate, dict) or not isinstance(aggregate.get("strict_v2_witness"), dict):
        return False
    requirement = strict_grasp_spec_v2()["antipodal_contact_requirement"]
    return bool(
        evaluate_antipodal_contact_witness(aggregate["strict_v2_witness"], requirement)[
            "valid"
        ]
    )


def _provenance(
    source_ref: dict[str, Any], pointer: str, *, derivation: str | None = None
) -> dict[str, Any]:
    value = {
        "state": "derived" if derivation is not None else "observed",
        "source_ref": source_ref,
        "source_pointer": pointer,
    }
    if derivation is not None:
        value["derivation"] = derivation
    return value


def _sourced(
    value: Any, source_ref: dict[str, Any], pointer: str, *, units: str = "radian"
) -> dict[str, Any]:
    return {
        "state": "observed",
        "value": value,
        "units": units,
        "provenance": _provenance(source_ref, pointer),
        "reason": None,
    }


def _derived_reward(value: float, source_ref: dict[str, Any], pointer: str) -> dict[str, Any]:
    return {
        "state": "derived",
        "value": value,
        "components": ["strict_v2_frame_valid"],
        "provenance": _provenance(
            source_ref, pointer + "/strict_v2", derivation="strict-v2 evaluator output"
        ),
        "reason": None,
    }


def _derived_progress(value: float, source_ref: dict[str, Any], pointer: str) -> dict[str, Any]:
    return {
        "state": "derived",
        "value": value,
        "components": ["source_phase_ordinal"],
        "provenance": _provenance(
            source_ref, pointer + "/phase", derivation="fixed scripted phase order"
        ),
        "reason": None,
    }


def _margin(measured: Any, threshold: int, comparison: str) -> dict[str, Any]:
    if isinstance(measured, bool) or not isinstance(measured, (int, float)):
        return {"measured": measured, "threshold": threshold, "comparison": comparison, "margin": None, "passed": False}
    margin = measured - threshold
    return {
        "measured": measured,
        "threshold": threshold,
        "comparison": comparison,
        "margin": margin,
        "passed": measured >= threshold,
    }


def _validate_episode_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise ValueError("Episode specification is invalid")
    seed = _require_seed(spec.get("seed"))
    if seed not in {entry["seed"] for entry in EPISODE_SPECS} or spec != EPISODE_SPECS[seed]:
        raise ValueError("Episode specification is not one of the fixed seeds")
    offset = spec.get("planar_offset_m")
    yaw = spec.get("yaw_offset_rad")
    if (
        not isinstance(offset, list)
        or len(offset) != 2
        or any(isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or abs(value) > 0.001 for value in offset)
        or isinstance(yaw, bool)
        or not isinstance(yaw, (int, float))
        or not np.isfinite(yaw)
        or abs(yaw) > 0.03
    ):
        raise ValueError("Episode randomization exceeds the declared envelope")


def _six_values(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != len(JOINT_NAMES):
        raise ValueError(f"Recorded {label} must contain six values")
    result = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)) or not np.isfinite(item):
            raise ValueError(f"Recorded {label} contains a non-finite value")
        result.append(float(item))
    return result


def _timestamp_ns(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError("Captured simulator time is invalid")
    return round(float(value) * 1_000_000_000)


def _resolve_store_path(store_root: Path, relative_path: Any) -> Path:
    if not isinstance(relative_path, str) or not relative_path.endswith(".json"):
        raise ValueError("Episode-store relative path is invalid")
    resolved = (store_root / relative_path).resolve()
    if resolved.parent != store_root:
        raise ValueError("Episode-store path escapes its root")
    return resolved


def _require_seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Episode seed is invalid")
    return value


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

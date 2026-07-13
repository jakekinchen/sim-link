"""Grasp-specific position IK with fixed wrist variables and explicit object yaw."""

from __future__ import annotations

import math
import tempfile

from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.causal_sort_expert import SIMULATION_HOME
from scenesmith.robot_lab.gripper_contact_semantics import (
    FIXED_PAD_SITE,
    MOVING_PAD_SITE,
    apply_gripper_contact_identities,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID, _bind_anchor_geometry, _scene
from scenesmith.robot_lab.mujoco_export import prepare_mujoco_so101_assets, render_mujoco_xml


SCHEMA_VERSION = "scenesmith.grasp_pose_solver_fixture.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
GEOMETRY_AUDIT = REPO_ROOT / "configurations/robot_lab/gripper_geometry_audit.json"
POSITION_TOLERANCE_M = 0.001
WRIST_TOLERANCE_RAD = 1e-9
OBJECT_YAW_TOLERANCE_RAD = 1e-9
CANDIDATES = (
    (-0.5, -1.2, -0.6, (0.0, 0.0, 0.0)),
    (-0.2, -0.4, -0.2, (0.002, 0.0, 0.0)),
    (0.2, 0.4, 0.2, (0.0, -0.002, 0.0)),
    (0.5, 1.2, 0.6, (-0.0005, 0.0005, 0.0)),
)


def solve_grasp_pose(
    mujoco: Any,
    model: Any,
    data: Any,
    *,
    gripper_site_id: int,
    target_position_m: list[float],
    wrist_flex_rad: float,
    wrist_roll_rad: float,
    maximum_residual_m: float = POSITION_TOLERANCE_M,
) -> dict[str, Any]:
    """Solve shoulder/elbow position while wrist flex/roll remain fixed."""

    target = _finite_vector(target_position_m, 3, "target position")
    requested = {
        "wrist_flex": _finite(wrist_flex_rad, "wrist flex"),
        "wrist_roll": _finite(wrist_roll_rad, "wrist roll"),
    }
    solve_names = ("shoulder_pan", "shoulder_lift", "elbow_flex")
    fixed_names = ("wrist_flex", "wrist_roll")
    solve_joints = [_joint(mujoco, model, name) for name in solve_names]
    fixed_joints = [_joint(mujoco, model, name) for name in fixed_names]
    solve_qpos = [int(model.jnt_qposadr[joint]) for joint in solve_joints]
    solve_dofs = [int(model.jnt_dofadr[joint]) for joint in solve_joints]
    fixed_qpos = [int(model.jnt_qposadr[joint]) for joint in fixed_joints]
    for name, joint in zip(fixed_names, fixed_joints, strict=True):
        value = requested[name]
        if value < model.jnt_range[joint, 0] or value > model.jnt_range[joint, 1]:
            raise ValueError(f"Requested {name} is outside the compiled joint range")
    if not math.isfinite(maximum_residual_m) or maximum_residual_m <= 0.0:
        raise ValueError("Maximum residual must be finite and positive")
    current = data.qpos.copy()
    starts = [current.copy(), current.copy()]
    starts[1][: model.nu] = np.asarray(SIMULATION_HOME, dtype=np.float64)
    best: tuple[float, np.ndarray] | None = None
    for start in starts:
        shadow = mujoco.MjData(model)
        shadow.qpos[:] = start
        shadow.qvel[:] = 0.0
        shadow.qpos[fixed_qpos] = [requested["wrist_flex"], requested["wrist_roll"]]
        reference = shadow.qpos[solve_qpos].copy()
        for _ in range(600):
            mujoco.mj_forward(model, shadow)
            error = target - shadow.site_xpos[gripper_site_id]
            if float(np.linalg.norm(error)) <= 1e-5:
                break
            jac_pos = np.zeros((3, model.nv), dtype=np.float64)
            jac_rot = np.zeros((3, model.nv), dtype=np.float64)
            mujoco.mj_jacSite(model, shadow, jac_pos, jac_rot, gripper_site_id)
            jacobian = jac_pos[:, solve_dofs]
            delta = jacobian.T @ np.linalg.solve(
                jacobian @ jacobian.T + 2e-4 * np.eye(3),
                error,
            )
            delta += 0.002 * (reference - shadow.qpos[solve_qpos])
            shadow.qpos[solve_qpos] += np.clip(delta, -0.06, 0.06)
            for joint, address in zip(solve_joints, solve_qpos, strict=True):
                shadow.qpos[address] = np.clip(
                    shadow.qpos[address],
                    model.jnt_range[joint, 0] + 0.01,
                    model.jnt_range[joint, 1] - 0.01,
                )
            shadow.qpos[fixed_qpos] = [requested["wrist_flex"], requested["wrist_roll"]]
        mujoco.mj_forward(model, shadow)
        residual = float(np.linalg.norm(target - shadow.site_xpos[gripper_site_id]))
        if math.isfinite(residual) and (best is None or residual < best[0]):
            best = (residual, shadow.qpos.copy())
    if best is None or best[0] > maximum_residual_m:
        raise ValueError(f"Fixed-wrist grasp IK residual exceeds limit: {best}")
    residual, qpos = best
    achieved = {
        name: float(qpos[address])
        for name, address in zip(fixed_names, fixed_qpos, strict=True)
    }
    for name in fixed_names:
        if abs(achieved[name] - requested[name]) > WRIST_TOLERANCE_RAD:
            raise ValueError(f"Requested {name} was not achieved")
    return {
        "qpos": qpos,
        "position_residual_m": residual,
        "requested_wrist_flex_rad": requested["wrist_flex"],
        "achieved_wrist_flex_rad": achieved["wrist_flex"],
        "requested_wrist_roll_rad": requested["wrist_roll"],
        "achieved_wrist_roll_rad": achieved["wrist_roll"],
        "solved_joint_names": list(solve_names),
        "fixed_joint_names": list(fixed_names),
    }


def apply_and_read_object_yaw(
    mujoco: Any,
    model: Any,
    data: Any,
    *,
    object_joint_name: str,
    object_body_name: str,
    yaw_rad: float,
) -> float:
    """Apply free-joint world-z yaw and independently read it from body xquat."""

    requested = _finite(yaw_rad, "object yaw")
    joint = _joint(mujoco, model, object_joint_name)
    if int(model.jnt_type[joint]) != int(mujoco.mjtJoint.mjJNT_FREE):
        raise ValueError("Object joint is not free")
    address = int(model.jnt_qposadr[joint])
    data.qpos[address + 3 : address + 7] = [
        math.cos(requested / 2.0),
        0.0,
        0.0,
        math.sin(requested / 2.0),
    ]
    mujoco.mj_forward(model, data)
    body = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, object_body_name))
    if body < 0:
        raise ValueError("Object body is missing")
    achieved = _read_body_yaw(data, body)
    if abs(_angle_difference(achieved, requested)) > OBJECT_YAW_TOLERANCE_RAD:
        raise ValueError("Requested object yaw was not achieved")
    return achieved


def build_grasp_pose_solver_fixture() -> dict[str, Any]:
    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise RuntimeError("mujoco is required for grasp pose solving") from exc
    audit = load_strict_json(GEOMETRY_AUDIT)
    verify_signed_payload(audit, label="source gripper geometry audit")
    results = []
    with tempfile.TemporaryDirectory(prefix="scenesmith-grasp-pose-") as directory:
        root = Path(directory)
        robot_xml = prepare_mujoco_so101_assets(root, _scene().robot.base_position_m)
        apply_gripper_contact_identities(robot_xml)
        scene_xml = root / "scene.xml"
        scene_xml.write_text(render_mujoco_xml(_scene()), encoding="utf-8")
        _bind_anchor_geometry(scene_xml)
        model = mujoco.MjModel.from_xml_path(str(scene_xml))
        data = mujoco.MjData(model)
        site = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "gripperframe"))
        fixed_site = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, FIXED_PAD_SITE))
        moving_site = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, MOVING_PAD_SITE))
        for index, (flex, roll, yaw, offsets) in enumerate(CANDIDATES):
            reference = mujoco.MjData(model)
            reference.qpos[: model.nu] = np.asarray(SIMULATION_HOME)
            reference.qpos[_qpos(mujoco, model, "wrist_flex")] = flex
            reference.qpos[_qpos(mujoco, model, "wrist_roll")] = roll
            reference.qpos[_qpos(mujoco, model, "gripper")] = 1.6
            mujoco.mj_forward(model, reference)
            target = reference.site_xpos[site] + np.asarray(offsets)
            requested_rotation = np.asarray(reference.site_xmat[site]).reshape(3, 3)
            requested_closing = _unit(
                reference.site_xpos[moving_site] - reference.site_xpos[fixed_site]
            )
            data.qpos[: model.nu] = np.asarray(SIMULATION_HOME)
            data.qpos[_qpos(mujoco, model, "gripper")] = 1.6
            achieved_yaw = apply_and_read_object_yaw(
                mujoco,
                model,
                data,
                object_joint_name=f"{OBJECT_ID}_free",
                object_body_name=OBJECT_ID,
                yaw_rad=yaw,
            )
            initial_collisions = _forbidden_self_contacts(mujoco, model, data)
            solved = solve_grasp_pose(
                mujoco,
                model,
                data,
                gripper_site_id=site,
                target_position_m=target.tolist(),
                wrist_flex_rad=flex,
                wrist_roll_rad=roll,
            )
            data.qpos[:] = solved.pop("qpos")
            mujoco.mj_forward(model, data)
            object_body = int(
                mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, OBJECT_ID)
            )
            achieved_yaw = _read_body_yaw(data, object_body)
            rotation = np.asarray(data.site_xmat[site]).reshape(3, 3)
            closing = _unit(data.site_xpos[moving_site] - data.site_xpos[fixed_site])
            collisions = _forbidden_self_contacts(mujoco, model, data)
            achieved_position = data.site_xpos[site].copy()
            accepted = (
                solved["position_residual_m"] <= POSITION_TOLERANCE_M
                and not initial_collisions
                and not collisions
                and abs(_angle_difference(achieved_yaw, yaw)) <= OBJECT_YAW_TOLERANCE_RAD
            )
            results.append(
                {
                    "candidate_index": index,
                    "requested_pregrasp_position_m": _rounded(target),
                    "achieved_pregrasp_position_m": _rounded(achieved_position),
                    "requested_lateral_x_offset_m": offsets[0],
                    "requested_lateral_y_offset_m": offsets[1],
                    "requested_vertical_offset_m": offsets[2],
                    **solved,
                    "requested_object_yaw_rad": yaw,
                    "achieved_object_yaw_rad": achieved_yaw,
                    "requested_approach_axis_world": _rounded(
                        requested_rotation[:, 2]
                    ),
                    "achieved_gripper_rotation_matrix": [_rounded(row) for row in rotation],
                    "achieved_approach_axis_world": _rounded(rotation[:, 2]),
                    "requested_closing_axis_world": _rounded(requested_closing),
                    "achieved_closing_axis_world": _rounded(closing),
                    "initial_forbidden_self_collision_pairs": initial_collisions,
                    "forbidden_self_collision_pairs": collisions,
                    "accepted_before_contact_simulation": accepted,
                }
            )
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "deterministic_fixed_wrist_position_ik_and_object_yaw_fixture",
            "source_gripper_geometry_audit_identity_sha256": audit["identity_sha256"],
            "position_tolerance_m": POSITION_TOLERANCE_M,
            "wrist_tolerance_rad": WRIST_TOLERANCE_RAD,
            "object_yaw_tolerance_rad": OBJECT_YAW_TOLERANCE_RAD,
            "approach_axis_definition": "gripperframe_local_positive_z",
            "closing_axis_definition": "fixed_pad_reference_to_moving_pad_reference",
            "candidate_count": len(results),
            "accepted_candidate_count": sum(row["accepted_before_contact_simulation"] for row in results),
            "candidates": results,
            "orientation_search_executed": False,
            "contact_simulation_executed": False,
            "actual_mujoco_grasp_success": False,
            "simulation_training_ready": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "local_capabilities": ["fixed_wrist_grasp_position_ik_valid", "explicit_object_yaw_application_valid"],
            "authority_not_granted": ["orientation_search_executed", "unassisted_mujoco_grasp_success", "simulation_training_ready", "physical_actuation"],
        }
    )


def verify_grasp_pose_solver_fixture(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="grasp pose solver fixture")
    candidates = payload.get("candidates", [])
    if payload.get("candidate_count") != len(candidates) or not candidates:
        raise ValueError("Grasp pose candidate count drifted")
    if payload.get("accepted_candidate_count") != len(candidates):
        raise ValueError("A deterministic pose candidate failed")
    if any(not row.get("accepted_before_contact_simulation") for row in candidates):
        raise ValueError("Unachieved pose candidate was accepted")
    if any(
        row.get("initial_forbidden_self_collision_pairs")
        or row.get("forbidden_self_collision_pairs")
        for row in candidates
    ):
        raise ValueError("Collision-invalid pose candidate was accepted")
    if payload.get("orientation_search_executed") is not False:
        raise ValueError("Pose fixture overclaimed orientation search")


def _forbidden_self_contacts(mujoco: Any, model: Any, data: Any) -> list[list[str]]:
    base = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base"))
    robot = {body for body in range(model.nbody) if body == base or _descends(model, body, base)}
    pairs = set()
    for index in range(data.ncon):
        contact = data.contact[index]
        left = int(model.geom_bodyid[contact.geom1])
        right = int(model.geom_bodyid[contact.geom2])
        if left not in robot or right not in robot or left == right:
            continue
        if int(model.body_parentid[left]) == right or int(model.body_parentid[right]) == left:
            continue
        names = tuple(sorted((_body_name(mujoco, model, left), _body_name(mujoco, model, right))))
        pairs.add(names)
    return [list(pair) for pair in sorted(pairs)]


def _descends(model: Any, body: int, root: int) -> bool:
    current = body
    while current > 0:
        current = int(model.body_parentid[current])
        if current == root:
            return True
    return False


def _body_name(mujoco: Any, model: Any, body: int) -> str:
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body) or "world"


def _joint(mujoco: Any, model: Any, name: str) -> int:
    joint = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name))
    if joint < 0:
        raise ValueError(f"Joint is missing: {name}")
    return joint


def _qpos(mujoco: Any, model: Any, name: str) -> int:
    return int(model.jnt_qposadr[_joint(mujoco, model, name)])


def _finite(value: float, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _finite_vector(values: list[float], length: int, label: str) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64)
    if vector.shape != (length,) or not np.isfinite(vector).all():
        raise ValueError(f"{label} must contain {length} finite values")
    return vector


def _angle_difference(left: float, right: float) -> float:
    return math.atan2(math.sin(left - right), math.cos(left - right))


def _read_body_yaw(data: Any, body_id: int) -> float:
    w, x, y, z = [float(value) for value in data.xquat[body_id]]
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("Axis must be finite and nonzero")
    return vector / norm


def _rounded(values: Any) -> list[float]:
    vector = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(vector).all():
        raise ValueError("Pose output contains non-finite values")
    return [round(float(value), 9) for value in vector]

"""Truthful SO-101 gripper geometry and MuJoCo contact semantics."""

from __future__ import annotations

import hashlib
import json
import math
import tempfile
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.causal_sort_expert import SIMULATION_HOME
from scenesmith.robot_lab.mujoco_anchor_grasp import (
    ANCHOR_DIMENSIONS_M,
    OBJECT_ID,
    PINNED_MJCF,
    _bind_anchor_geometry,
    _scene,
)
from scenesmith.robot_lab.mujoco_export import (
    prepare_mujoco_so101_assets,
    render_mujoco_xml,
)


SCHEMA_VERSION = "scenesmith.gripper_geometry_audit.v1"
SEMANTIC_MODEL_VERSION = "scenesmith.so101_gripper_contact_semantics.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
MENAGERIE_MODEL = (
    REPO_ROOT / "third_party/mujoco_menagerie/robotstudio_so101/so101.xml"
)
FIXED_PAD_GEOM = "fixed_fingertip_pad_collision"
MOVING_PAD_GEOM = "moving_fingertip_pad_collision"
FIXED_JAW_COMPOSITE_GEOM = "fixed_jaw_composite_collision"
MOVING_JAW_COMPOSITE_GEOM = "moving_jaw_composite_collision"
SHELL_GEOM = "gripper_servo_shell_collision"
FIXED_PAD_SITE = "fixed_fingertip_pad_reference"
MOVING_PAD_SITE = "moving_fingertip_pad_reference"
# Reference points correspond to the explicit fingertip collision primitives in
# the pinned derived Menagerie model. Sites do not alter collision geometry.
FIXED_PAD_REFERENCE_LOCAL_M = (-0.009, 0.0, -0.0982)
MOVING_PAD_REFERENCE_LOCAL_M = (-0.0113, -0.076, 0.01875)
PAD_HALF_SIZE_M = (0.001, 0.004, 0.004)


def apply_gripper_contact_identities(robot_xml_path: Path) -> dict[str, Any]:
    """Name existing jaw collisions and add non-colliding pad reference sites."""

    tree = ET.parse(robot_xml_path)
    root = tree.getroot()
    before = _collision_geometry_digest(root)
    gripper = root.find(".//body[@name='gripper']")
    moving = root.find(".//body[@name='moving_jaw_so101_v1']")
    if gripper is None or moving is None:
        raise ValueError("SO-101 gripper bodies are missing")
    fixed_composite = _active_mesh_geom(gripper, "wrist_roll_follower_so101_v1")
    shell = _active_mesh_geom(gripper, "sts3215_03a_v1")
    moving_composite = _active_mesh_geom(moving, "moving_jaw_so101_v1")
    fixed_composite.set("name", FIXED_JAW_COMPOSITE_GEOM)
    shell.set("name", SHELL_GEOM)
    moving_composite.set("name", MOVING_JAW_COMPOSITE_GEOM)
    _ensure_pad_geom(gripper, FIXED_PAD_GEOM, FIXED_PAD_REFERENCE_LOCAL_M)
    _ensure_pad_geom(moving, MOVING_PAD_GEOM, MOVING_PAD_REFERENCE_LOCAL_M)
    _ensure_site(gripper, FIXED_PAD_SITE, FIXED_PAD_REFERENCE_LOCAL_M)
    _ensure_site(moving, MOVING_PAD_SITE, MOVING_PAD_REFERENCE_LOCAL_M)
    after = _collision_geometry_digest(
        root,
        exclude_names={FIXED_PAD_GEOM, MOVING_PAD_GEOM},
    )
    if before != after:
        raise ValueError("Gripper semantic naming changed collision geometry")
    ET.indent(tree, space="  ")
    tree.write(robot_xml_path, encoding="utf-8", xml_declaration=True)
    return {
        "semantic_model_version": SEMANTIC_MODEL_VERSION,
        "collision_geometry_digest_before": before,
        "collision_geometry_digest_after": after,
        "original_collision_geometry_preserved": True,
        "collision_geometry_change_scope": (
            "original_geoms_unchanged_plus_two_explicit_fingertip_pad_boxes"
        ),
        "named_pad_geoms": [FIXED_PAD_GEOM, MOVING_PAD_GEOM],
        "named_non_pad_geoms": [
            SHELL_GEOM,
            FIXED_JAW_COMPOSITE_GEOM,
            MOVING_JAW_COMPOSITE_GEOM,
        ],
        "added_pad_collision_geoms": [FIXED_PAD_GEOM, MOVING_PAD_GEOM],
        "pad_half_size_m": list(PAD_HALF_SIZE_M),
        "added_noncolliding_reference_sites": [FIXED_PAD_SITE, MOVING_PAD_SITE],
    }


def apply_explicit_pad_proxy_contact_model(robot_xml_path: Path) -> dict[str, Any]:
    """Retain composite jaw meshes but make only explicit pads contact-active."""

    change = apply_gripper_contact_identities(robot_xml_path)
    tree = ET.parse(robot_xml_path)
    root = tree.getroot()
    disabled = []
    for name in (FIXED_JAW_COMPOSITE_GEOM, MOVING_JAW_COMPOSITE_GEOM):
        geom = root.find(f".//geom[@name='{name}']")
        if geom is None:
            raise ValueError(f"Composite jaw geom is missing: {name}")
        geom.set("contype", "0")
        geom.set("conaffinity", "0")
        disabled.append(name)
    ET.indent(tree, space="  ")
    tree.write(robot_xml_path, encoding="utf-8", xml_declaration=True)
    return {
        **change,
        "semantic_model_version": "scenesmith.so101_explicit_pad_proxy_contact.v2",
        "contact_mask_disabled_composite_geoms": disabled,
        "contact_active_pad_geoms": [FIXED_PAD_GEOM, MOVING_PAD_GEOM],
        "geometry_removed": False,
    }


def build_gripper_geometry_audit() -> dict[str, Any]:
    """Compile the pinned grasp model and emit deterministic geometry evidence."""

    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise RuntimeError("mujoco is required for the gripper audit") from exc
    with tempfile.TemporaryDirectory(prefix="scenesmith-gripper-audit-") as directory:
        root = Path(directory)
        robot_xml = prepare_mujoco_so101_assets(root, _scene().robot.base_position_m)
        change = apply_gripper_contact_identities(robot_xml)
        scene_xml = root / "scene.xml"
        scene_xml.write_text(render_mujoco_xml(_scene()), encoding="utf-8")
        _bind_anchor_geometry(scene_xml)
        model = mujoco.MjModel.from_xml_path(str(scene_xml))
        data = mujoco.MjData(model)
        data.qpos[: model.nu] = np.asarray(SIMULATION_HOME, dtype=np.float64)
        data.ctrl[: model.nu] = np.asarray(SIMULATION_HOME, dtype=np.float64)
        mujoco.mj_forward(model, data)
        body_ids = _gripper_body_ids(mujoco, model)
        geom_rows = [_geom_row(mujoco, model, data, geom_id) for geom_id in range(model.ngeom)
                     if int(model.geom_bodyid[geom_id]) in body_ids]
        aperture = _aperture_curve(mujoco, model, data)
    synthetic = synthetic_contact_convention_proof()
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "compiled_mujoco_geometry_and_synthetic_contact_semantics",
            "semantic_model_change": change,
            "pinned_model": _file_ref(PINNED_MJCF),
            "pad_reference_source": _file_ref(MENAGERIE_MODEL),
            "contact_normal_convention": "object_coordinates_inward_toward_object",
            "gripper_bodies": [_body_row(mujoco, model, body_id) for body_id in sorted(body_ids)],
            "gripper_geoms": geom_rows,
            "fixed_fingertip_pad_geom_names": [FIXED_PAD_GEOM],
            "moving_fingertip_pad_geom_names": [MOVING_PAD_GEOM],
            "non_pad_contact_geom_names": [
                SHELL_GEOM,
                FIXED_JAW_COMPOSITE_GEOM,
                MOVING_JAW_COMPOSITE_GEOM,
            ],
            "moving_jaw_joint": _joint_row(mujoco, model, "gripper"),
            "aperture_reference": {
                "method": "distance_between_versioned_fingertip_reference_sites",
                "physical_calibration_claimed": False,
                "samples": aperture,
                "minimum_m": min(row["separation_m"] for row in aperture),
                "maximum_m": max(row["separation_m"] for row in aperture),
            },
            "nominal_object_dimensions_m": list(ANCHOR_DIMENSIONS_M),
            "object_relative_to_aperture": {
                "minimum_object_width_m": min(ANCHOR_DIMENSIONS_M),
                "maximum_object_width_m": max(ANCHOR_DIMENSIONS_M),
                "fits_maximum_simulated_reference_aperture": max(ANCHOR_DIMENSIONS_M)
                < max(row["separation_m"] for row in aperture),
            },
            "synthetic_contact_convention_proof": synthetic,
            "historical_contact_methods": {
                "body_contact_count": "diagnostic_only",
                "minimum_pairwise_span": "diagnostic_only",
            },
            "actual_mujoco_grasp_success": False,
            "simulation_training_ready": False,
            "physical_twin_qualified": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "local_capabilities": [
                "compiled_gripper_geometry_audit_valid",
                "object_oriented_contact_normal_adapter_valid",
                "pad_qualified_contact_aggregation_valid",
            ],
            "authority_not_granted": [
                "unassisted_mujoco_grasp_success",
                "simulation_training_ready",
                "physical_twin_qualified",
                "physical_actuation",
            ],
        }
    )


def verify_gripper_geometry_audit(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="gripper geometry audit")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Gripper geometry audit schema drifted")
    change = payload.get("semantic_model_change", {})
    if not change.get("original_collision_geometry_preserved"):
        raise ValueError("Gripper collision geometry was not preserved")
    names = {row.get("name") for row in payload.get("gripper_geoms", [])}
    required = {
        FIXED_PAD_GEOM,
        MOVING_PAD_GEOM,
        SHELL_GEOM,
        FIXED_JAW_COMPOSITE_GEOM,
        MOVING_JAW_COMPOSITE_GEOM,
    }
    if not required.issubset(names):
        raise ValueError("Gripper semantic geom identities are incomplete")
    rows = payload.get("gripper_geoms", [])
    pads = [
        row
        for row in rows
        if row.get("semantic_role")
        in {"fixed_fingertip_pad", "moving_fingertip_pad"}
    ]
    if (
        len(pads) != 2
        or any(row.get("type") != "mjGEOM_BOX" for row in pads)
        or any(row.get("contype") == 0 or row.get("conaffinity") == 0 for row in pads)
    ):
        raise ValueError("Explicit fingertip pads are not unique active box geoms")
    proof = payload.get("synthetic_contact_convention_proof", {})
    if not proof.get("geom_order_independent") or not proof.get("aggregate_valid"):
        raise ValueError("Synthetic contact convention proof failed")
    if payload.get("actual_mujoco_grasp_success") is not False:
        raise ValueError("Geometry audit overclaimed grasp success")


def extract_pad_contacts(
    mujoco: Any,
    model: Any,
    data: Any,
    *,
    object_body_id: int,
    pad_geom_roles: dict[int, str],
) -> list[dict[str, Any]]:
    """Return pad-only contacts with normals inward toward the object."""

    object_position = np.asarray(data.xpos[object_body_id], dtype=np.float64)
    object_rotation = np.asarray(data.xmat[object_body_id], dtype=np.float64).reshape(3, 3)
    rows: list[dict[str, Any]] = []
    force = np.zeros(6, dtype=np.float64)
    for contact_index in range(data.ncon):
        contact = data.contact[contact_index]
        geom1, geom2 = int(contact.geom1), int(contact.geom2)
        body1, body2 = int(model.geom_bodyid[geom1]), int(model.geom_bodyid[geom2])
        if object_body_id == body1 and geom2 in pad_geom_roles:
            object_side, pad_geom, canonical_world = "geom1", geom2, -np.asarray(contact.frame[:3])
        elif object_body_id == body2 and geom1 in pad_geom_roles:
            object_side, pad_geom, canonical_world = "geom2", geom1, np.asarray(contact.frame[:3])
        else:
            continue
        mujoco.mj_contactForce(model, data, contact_index, force)
        normal_force = float(force[0])
        if not math.isfinite(normal_force) or normal_force <= 0.0:
            continue
        world_position = np.asarray(contact.pos, dtype=np.float64)
        object_point = object_rotation.T @ (world_position - object_position)
        object_normal = object_rotation.T @ canonical_world
        rows.append(
            {
                "contact_index": contact_index,
                "geom1_id": geom1,
                "geom1_name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_GEOM, geom1),
                "geom2_id": geom2,
                "geom2_name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_GEOM, geom2),
                "body1_id": body1,
                "body1_name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_BODY, body1),
                "body2_id": body2,
                "body2_name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_BODY, body2),
                "object_side": object_side,
                "fingertip_side": "geom2" if object_side == "geom1" else "geom1",
                "pad_role": pad_geom_roles[pad_geom],
                "pad_geom_id": pad_geom,
                "raw_contact_frame": _rounded(contact.frame),
                "raw_position_world_m": _rounded(world_position),
                "raw_normal_world": _rounded(contact.frame[:3]),
                "normal_force_n": round(normal_force, 9),
                "tangential_force_contact_frame_n": _rounded(force[1:3]),
                "contact_point_object_m": _rounded(object_point),
                "contact_normal_object_inward": _rounded(object_normal),
            }
        )
    return rows


def compiled_pad_geom_roles(mujoco: Any, model: Any) -> dict[int, str]:
    """Resolve the two required pad geoms by explicit name and fail closed."""

    roles: dict[int, str] = {}
    for name, role in (
        (FIXED_PAD_GEOM, "fixed_fingertip_pad"),
        (MOVING_PAD_GEOM, "moving_fingertip_pad"),
    ):
        geom_id = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name))
        if geom_id < 0 or geom_id in roles:
            raise ValueError(f"Required unique fingertip pad geom is missing: {name}")
        if int(model.geom_contype[geom_id]) == 0 or int(model.geom_conaffinity[geom_id]) == 0:
            raise ValueError(f"Fingertip pad geom is not collision-active: {name}")
        roles[geom_id] = role
    return roles


def aggregate_pad_contacts(
    contacts: list[dict[str, Any]], closing_axis_object: list[float]
) -> dict[str, Any] | None:
    """Build representative pad contacts and a strict-v2 witness."""

    axis = _unit(np.asarray(closing_axis_object, dtype=np.float64), "closing axis")
    groups = {role: [row for row in contacts if row["pad_role"] == role]
              for role in ("fixed_fingertip_pad", "moving_fingertip_pad")}
    if any(not rows for rows in groups.values()):
        return None
    representatives = {role: _representative(rows) for role, rows in groups.items()}
    fixed = representatives["fixed_fingertip_pad"]
    moving = representatives["moving_fingertip_pad"]
    fixed_point = np.asarray(fixed["centroid_object_m"])
    moving_point = np.asarray(moving["centroid_object_m"])
    span_vector = moving_point - fixed_point
    span = float(np.linalg.norm(span_vector))
    if not math.isfinite(span) or span <= 0.0:
        return None
    span_axis = span_vector / span
    fixed_normal = np.asarray(fixed["normal_object_inward"])
    moving_normal = np.asarray(moving["normal_object_inward"])
    all_pairwise = [
        float(np.linalg.norm(np.asarray(left["contact_point_object_m"]) - np.asarray(right["contact_point_object_m"])))
        for left in groups["fixed_fingertip_pad"]
        for right in groups["moving_fingertip_pad"]
    ]
    force_fixed = fixed["total_normal_force_n"]
    force_moving = moving["total_normal_force_n"]
    return {
        "representative_contacts": representatives,
        "span_vector_object_m": _rounded(span_vector),
        "euclidean_span_m": round(span, 9),
        "closing_axis_projected_span_m": round(float(np.dot(span_vector, axis)), 9),
        "normal_dot": round(float(np.dot(fixed_normal, moving_normal)), 9),
        "fixed_normal_span_alignment": round(float(np.dot(fixed_normal, span_axis)), 9),
        "moving_normal_span_alignment": round(float(np.dot(moving_normal, -span_axis)), 9),
        "signed_contact_locations_on_closing_axis_m": {
            "fixed": round(float(np.dot(fixed_point, axis)), 9),
            "moving": round(float(np.dot(moving_point, axis)), 9),
        },
        "force_balance_min_over_max": round(min(force_fixed, force_moving) / max(force_fixed, force_moving), 9),
        "minimum_pairwise_span_m_diagnostic_only": round(min(all_pairwise), 9),
        "maximum_pairwise_span_m_diagnostic_only": round(max(all_pairwise), 9),
        "strict_v2_witness": {
            "jaw_ids": ["fixed_fingertip_pad", "moving_fingertip_pad"],
            "contact_points_m": [fixed["centroid_object_m"], moving["centroid_object_m"]],
            "contact_normals": [fixed["normal_object_inward"], moving["normal_object_inward"]],
            "source_mode": "mujoco_pad_qualified_force_weighted_representatives",
        },
    }


def synthetic_contact_convention_proof() -> dict[str, Any]:
    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise RuntimeError("mujoco is required for contact proof") from exc
    results = []
    for object_last in (False, True):
        object_xml = '<body name="object" pos="0 0 0"><freejoint/><geom name="object_geom" type="box" size=".02 .02 .02" mass="1"/></body>'
        pads_xml = '<body name="fixed_pad" pos="-.035 0 0"><geom name="fixed_pad_geom" type="box" size=".02 .02 .02"/></body><body name="moving_pad" pos=".035 0 0"><geom name="moving_pad_geom" type="box" size=".02 .02 .02"/></body>'
        bodies = pads_xml + object_xml if object_last else object_xml + pads_xml
        model = mujoco.MjModel.from_xml_string(f'<mujoco><option gravity="0 0 0"/><worldbody>{bodies}</worldbody></mujoco>')
        data = mujoco.MjData(model)
        mujoco.mj_step(model, data)
        object_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "object")
        roles = {
            mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "fixed_pad_geom"): "fixed_fingertip_pad",
            mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "moving_pad_geom"): "moving_fingertip_pad",
        }
        contacts = extract_pad_contacts(mujoco, model, data, object_body_id=object_id, pad_geom_roles=roles)
        aggregate = aggregate_pad_contacts(contacts, [1.0, 0.0, 0.0])
        if aggregate is None:
            raise ValueError("Synthetic pad aggregation unexpectedly failed")
        results.append({"object_declared_last": object_last, "contacts": contacts, "aggregate": aggregate})
    witnesses = [row["aggregate"]["strict_v2_witness"] for row in results]
    return {
        "fixture": "symmetric_box_between_fixed_and_moving_pads",
        "canonical_convention": "object_coordinates_inward_toward_object",
        "geom_order_independent": witnesses[0] == witnesses[1],
        "aggregate_valid": all(
            row["aggregate"]["normal_dot"] <= -0.999999
            and row["aggregate"]["fixed_normal_span_alignment"] >= 0.999999
            and row["aggregate"]["moving_normal_span_alignment"] >= 0.999999
            for row in results
        ),
        "order_cases": results,
    }


def _representative(rows: list[dict[str, Any]]) -> dict[str, Any]:
    weights = np.asarray([row["normal_force_n"] for row in rows], dtype=np.float64)
    points = np.asarray([row["contact_point_object_m"] for row in rows], dtype=np.float64)
    normals = np.asarray([row["contact_normal_object_inward"] for row in rows], dtype=np.float64)
    if not np.isfinite(weights).all() or np.any(weights <= 0.0):
        raise ValueError("Pad contact forces must be finite and positive")
    if not np.isfinite(points).all() or not np.isfinite(normals).all():
        raise ValueError("Pad contact geometry must be finite")
    total = float(np.sum(weights))
    centroid = np.sum(points * weights[:, None], axis=0) / total
    normal = _unit(np.sum(normals * weights[:, None], axis=0), "weighted pad normal")
    return {
        "contact_count": len(rows),
        "total_normal_force_n": round(total, 9),
        "centroid_object_m": _rounded(centroid),
        "normal_object_inward": _rounded(normal),
    }


def _active_mesh_geom(body: ET.Element, mesh: str) -> ET.Element:
    matches = [geom for geom in body.findall("geom") if geom.get("mesh") == mesh and geom.get("class") == "collision"]
    if len(matches) != 1:
        raise ValueError(f"Expected one active collision geom for mesh {mesh}, found {len(matches)}")
    return matches[0]


def _ensure_site(body: ET.Element, name: str, position: tuple[float, float, float]) -> None:
    if body.find(f"site[@name='{name}']") is None:
        ET.SubElement(body, "site", {"name": name, "pos": " ".join(str(v) for v in position), "size": "0.001", "group": "4"})


def _ensure_pad_geom(
    body: ET.Element,
    name: str,
    position: tuple[float, float, float],
) -> None:
    if body.find(f"geom[@name='{name}']") is None:
        ET.SubElement(
            body,
            "geom",
            {
                "name": name,
                "type": "box",
                "class": "collision",
                "size": " ".join(str(value) for value in PAD_HALF_SIZE_M),
                "pos": " ".join(str(value) for value in position),
            },
        )


def _collision_geometry_digest(
    root: ET.Element,
    *,
    exclude_names: set[str] | None = None,
) -> str:
    rows = []
    excluded = exclude_names or set()
    for body in root.iter("body"):
        for geom in body.findall("geom"):
            if geom.get("class") == "collision" and geom.get("name") not in excluded:
                rows.append({key: geom.get(key) for key in ("type", "mesh", "size", "pos", "quat", "class")})
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _gripper_body_ids(mujoco: Any, model: Any) -> set[int]:
    root = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "gripper")
    return {body_id for body_id in range(model.nbody) if body_id == root or _descends(model, body_id, root)}


def _descends(model: Any, body_id: int, root_id: int) -> bool:
    current = body_id
    while current > 0:
        current = int(model.body_parentid[current])
        if current == root_id:
            return True
    return False


def _geom_row(mujoco: Any, model: Any, data: Any, geom_id: int) -> dict[str, Any]:
    name = _name(mujoco, model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
    mesh_id = int(model.geom_dataid[geom_id]) if int(model.geom_type[geom_id]) == int(mujoco.mjtGeom.mjGEOM_MESH) else -1
    role = {
        FIXED_PAD_GEOM: "fixed_fingertip_pad",
        MOVING_PAD_GEOM: "moving_fingertip_pad",
        SHELL_GEOM: "shell_non_pad",
        FIXED_JAW_COMPOSITE_GEOM: "fixed_jaw_link_non_pad",
        MOVING_JAW_COMPOSITE_GEOM: "moving_jaw_link_non_pad",
    }.get(name, "visual_or_other_non_pad")
    return {
        "id": geom_id,
        "name": name,
        "body_id": int(model.geom_bodyid[geom_id]),
        "body_name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[geom_id])),
        "semantic_role": role,
        "type": mujoco.mjtGeom(int(model.geom_type[geom_id])).name,
        "mesh_name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_MESH, mesh_id) if mesh_id >= 0 else None,
        "dimensions": _rounded(model.geom_size[geom_id]),
        "local_position_m": _rounded(model.geom_pos[geom_id]),
        "local_quaternion_wxyz": _rounded(model.geom_quat[geom_id]),
        "world_position_m": _rounded(data.geom_xpos[geom_id]),
        "world_orientation_matrix": [_rounded(row) for row in np.asarray(data.geom_xmat[geom_id]).reshape(3, 3)],
        "contype": int(model.geom_contype[geom_id]),
        "conaffinity": int(model.geom_conaffinity[geom_id]),
    }


def _body_row(mujoco: Any, model: Any, body_id: int) -> dict[str, Any]:
    return {"id": body_id, "name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_BODY, body_id), "parent_id": int(model.body_parentid[body_id]), "parent_name": _name(mujoco, model, mujoco.mjtObj.mjOBJ_BODY, int(model.body_parentid[body_id]))}


def _joint_row(mujoco: Any, model: Any, name: str) -> dict[str, Any]:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    return {"id": joint_id, "name": name, "axis_local": _rounded(model.jnt_axis[joint_id]), "range_rad": _rounded(model.jnt_range[joint_id]), "qpos_address": int(model.jnt_qposadr[joint_id])}


def _aperture_curve(mujoco: Any, model: Any, data: Any) -> list[dict[str, Any]]:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "gripper")
    qpos_address = int(model.jnt_qposadr[joint_id])
    fixed_site = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, FIXED_PAD_SITE)
    moving_site = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, MOVING_PAD_SITE)
    rows = []
    for qpos in np.linspace(*model.jnt_range[joint_id], 9):
        data.qpos[qpos_address] = qpos
        mujoco.mj_forward(model, data)
        vector = data.site_xpos[moving_site] - data.site_xpos[fixed_site]
        rows.append({"gripper_qpos_rad": round(float(qpos), 9), "separation_m": round(float(np.linalg.norm(vector)), 9), "fixed_to_moving_vector_world_m": _rounded(vector)})
    return rows


def _file_ref(path: Path) -> dict[str, Any]:
    return {"path": str(path.relative_to(REPO_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size_bytes": path.stat().st_size}


def _name(mujoco: Any, model: Any, object_type: Any, object_id: int) -> str | None:
    if object_id < 0:
        return None
    return mujoco.mj_id2name(model, object_type, object_id)


def _unit(vector: np.ndarray, label: str) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError(f"{label} must be finite and nonzero")
    return vector / norm


def _rounded(values: Any) -> list[float]:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        raise ValueError("Non-finite MuJoCo geometry/contact value")
    return [round(float(value), 9) for value in array]

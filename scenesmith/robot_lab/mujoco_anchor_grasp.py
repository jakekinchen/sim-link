"""Deterministic nominal-anchor MuJoCo grasp attempt and strict compilation."""

from __future__ import annotations

import copy
import hashlib
import math
import tempfile
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.causal_sort_expert import (
    CausalSortExpert,
    CausalSortExpertConfig,
)
from scenesmith.robot_lab.grasp_evidence import (
    KEYFRAME_IMAGE_SIZE,
    finalize_rendered_keyframes,
    retain_rendered_keyframe,
    validate_rendered_keyframes,
)
from scenesmith.robot_lab.mujoco_export import (
    prepare_mujoco_so101_assets,
    render_mujoco_xml,
)
from scenesmith.robot_lab.spec import (
    RobotLabCube,
    RobotLabDesk,
    RobotLabPolicy,
    RobotLabRobot,
    RobotLabRoom,
    RobotLabScene,
    RobotLabTray,
)
from scenesmith.robot_lab.strict_grasp import (
    evaluate_strict_grasp,
    strict_grasp_spec,
)


SCHEMA_VERSION = "scenesmith.mujoco_anchor_grasp_attempt.v1"
OBJECT_ID = "analytic_turquoise_anchor_cousin_v1"
ANCHOR_DIMENSIONS_M = (0.05, 0.035, 0.03)
ANCHOR_MASS_KG = 0.025
SEED = 901
REPO_ROOT = Path(__file__).resolve().parents[2]
PINNED_MJCF = REPO_ROOT / "external/SO-ARM100/Simulation/SO101/so101_new_calib.xml"
STRICT_FIXTURE = REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator.fixture.json"


def build_mujoco_anchor_grasp_attempt() -> dict[str, Any]:
    """Run the exact simulation twice and return one signed evidence artifact."""

    first = _run_once()
    second = _run_once()
    if first != second:
        raise ValueError("Nominal anchor MuJoCo replay is not deterministic")
    spec = strict_grasp_spec()
    trace = _compile_strict_trace(first["raw_frames"], spec)
    evaluation = evaluate_strict_grasp(
        spec,
        trace,
        claimed_proof_mode="analytic_expert",
    )
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "deterministic_mujoco_contact_gated_assisted_attempt",
            "seed": SEED,
            "pinned_mjcf": _file_evidence(PINNED_MJCF),
            "strict_fixture": _file_evidence(STRICT_FIXTURE),
            "anchor_object_id": OBJECT_ID,
            "anchor_dimensions_m": list(ANCHOR_DIMENSIONS_M),
            "anchor_mass_kg": ANCHOR_MASS_KG,
            "physical_measurement_claimed": False,
            "controller_owner": "causal_sort_expert_contact_gated_weld",
            "controller_assistance_present": True,
            "two_pass_exact_determinism": True,
            "mujoco_report": first["report"],
            "raw_frame_count": len(first["raw_frames"]),
            "raw_frames": first["raw_frames"],
            "rendered_keyframes": first["rendered_keyframes"],
            "maximum_anchor_step_displacement_m": first[
                "maximum_anchor_step_displacement_m"
            ],
            "strict_trace": trace,
            "strict_evaluation": evaluation,
            "unassisted_mujoco_grasp_success": False,
            "pure_policy_success": False,
            "physical_twin_qualified": False,
            "simulation_training_ready": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "authority_not_granted": [
                "unassisted_mujoco_grasp_success",
                "strict_policy_grasp_success",
                "physical_anchor_profile_complete",
                "physical_twin_qualified",
                "simulation_training_ready",
                "physical_actuation",
            ],
        }
    )


def verify_mujoco_anchor_grasp_attempt(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="MuJoCo anchor grasp attempt")
    validate_rendered_keyframes(payload.get("rendered_keyframes"))
    if payload != build_mujoco_anchor_grasp_attempt():
        raise ValueError("MuJoCo anchor grasp attempt drifted")


def _run_once() -> dict[str, Any]:
    scene = _scene()
    raw_frames: list[dict[str, Any]] = []
    rendered_keyframes: dict[str, dict[str, Any]] = {}
    phase_aliases = (
        ("descend", "pregrasp"),
        ("close", "close"),
        ("grasp_settle", "grasp_hold"),
        ("lift", "unsupported_lift_hold"),
        ("return_home", "retreat"),
    )
    with tempfile.TemporaryDirectory(prefix="scenesmith-anchor-grasp-") as directory:
        root = Path(directory)
        prepare_mujoco_so101_assets(root, scene.robot.base_position_m)
        xml_path = root / "scene.xml"
        xml_path.write_text(render_mujoco_xml(scene), encoding="utf-8")
        _bind_anchor_geometry(xml_path)
        expert: CausalSortExpert | None = None

        def retain(frame: dict[str, Any], _images: dict[str, np.ndarray]) -> None:
            if expert is None:
                raise RuntimeError("MuJoCo expert was not initialized")
            raw_frames.append(_raw_frame(expert, frame))
            phase = next(
                (
                    target
                    for suffix, target in phase_aliases
                    if str(frame.get("phase", "")).endswith(suffix)
                ),
                None,
            )
            if phase is not None:
                aliased_frame = dict(frame)
                aliased_frame["phase"] = phase
                retain_rendered_keyframe(
                    rendered_keyframes,
                    aliased_frame,
                    _images,
                    image_size=KEYFRAME_IMAGE_SIZE,
                )

        expert = CausalSortExpert(
            scene,
            xml_path,
            seed=SEED,
            frame_sink=retain,
            config=CausalSortExpertConfig(
                image_size=KEYFRAME_IMAGE_SIZE,
                capture_images=True,
            ),
        )
        try:
            report = expert.run()
        finally:
            expert.close()
        report["task"] = scene.policy.task
    maximum_step = _add_anchor_speeds(raw_frames)
    return {
        "report": report,
        "raw_frames": raw_frames,
        "rendered_keyframes": finalize_rendered_keyframes(rendered_keyframes),
        "maximum_anchor_step_displacement_m": maximum_step,
    }


def _scene(
    *, initial_position_m: tuple[float, float, float] | None = None
) -> RobotLabScene:
    anchor_position = initial_position_m or (0.22, 0.0, 0.325)
    if len(anchor_position) != 3:
        raise ValueError("Anchor initial position must have three coordinates")
    if any(not math.isfinite(value) for value in anchor_position):
        raise ValueError("Anchor initial position must be finite")
    return RobotLabScene(
        schema_version="scenesmith.robot_lab.v1",
        scene_id="scenesmith_nominal_anchor_grasp_probe",
        description="Nominal nonphysical turquoise anchor-cousin grasp probe.",
        room=RobotLabRoom(),
        desk=RobotLabDesk(),
        robot=RobotLabRobot(),
        trays=(
            RobotLabTray(
                name="green_tray",
                color="green",
                center_m=(0.34, 0.0, 0.316),
            ),
        ),
        cubes=(
            RobotLabCube(
                name=OBJECT_ID,
                color="green",
                initial_position_m=anchor_position,
                side_length_m=ANCHOR_DIMENSIONS_M[2],
                mass_kg=ANCHOR_MASS_KG,
            ),
        ),
        policy=RobotLabPolicy(task="Grasp and replace the nominal anchor cousin."),
    )


def _bind_anchor_geometry(xml_path: Path) -> None:
    tree = ET.parse(xml_path)
    geom = tree.getroot().find(f".//body[@name='{OBJECT_ID}']/geom")
    if geom is None:
        raise ValueError("Nominal anchor geom is missing")
    geom.set("size", "0.025 0.0175 0.015")
    geom.set("mass", str(ANCHOR_MASS_KG))
    geom.set("rgba", "0.1 0.8 0.75 1")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)


def _raw_frame(expert: CausalSortExpert, frame: dict[str, Any]) -> dict[str, Any]:
    data = expert.data
    model = expert.model
    mujoco = expert.mujoco
    cube_id = expert.cube_body_ids[OBJECT_ID]
    contact_force = 0.0
    support_contacts: list[str] = []
    self_contacts: list[list[str]] = []
    force = np.zeros(6, dtype=np.float64)
    for index in range(data.ncon):
        contact = data.contact[index]
        body1 = int(model.geom_bodyid[contact.geom1])
        body2 = int(model.geom_bodyid[contact.geom2])
        if cube_id in {body1, body2}:
            other = body2 if body1 == cube_id else body1
            if other not in expert.robot_body_ids:
                other_geom = contact.geom2 if body1 == cube_id else contact.geom1
                support_contacts.append(
                    mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, other_geom)
                    or "unnamed"
                )
            else:
                mujoco.mj_contactForce(model, data, index, force)
                contact_force = max(contact_force, float(np.linalg.norm(force[:3])))
        if body1 in expert.robot_body_ids and body2 in expert.robot_body_ids:
            names = sorted([expert._body_name(body1), expert._body_name(body2)])
            if names[0] != names[1] and names not in self_contacts:
                self_contacts.append(names)
    retained = copy.deepcopy(frame)
    retained.update(
        {
            "gripper_position_m": _rounded(data.site_xpos[expert.gripper_site_id]),
            "anchor_support_contacts": sorted(set(support_contacts)),
            "robot_self_contacts": sorted(self_contacts),
            "robot_anchor_contact_force_n_max": round(contact_force, 9),
            "actuator_effort_nm_max": round(
                float(np.max(np.abs(data.qfrc_actuator[: model.nu]))),
                9,
            ),
        }
    )
    return retained


def _add_anchor_speeds(raw_frames: list[dict[str, Any]]) -> float:
    previous_position: list[float] | None = None
    previous_time: float | None = None
    maximum_step = 0.0
    for frame in raw_frames:
        position = frame["cube_positions_m"][OBJECT_ID]
        time_s = float(frame["time_s"])
        displacement = (
            0.0 if previous_position is None else _distance(position, previous_position)
        )
        elapsed = 0.0 if previous_time is None else time_s - previous_time
        frame["anchor_step_displacement_m"] = round(displacement, 9)
        frame["anchor_speed_m_s"] = round(
            displacement / elapsed if elapsed > 0.0 else 0.0,
            9,
        )
        maximum_step = max(maximum_step, displacement)
        previous_position = position
        previous_time = time_s
    return round(maximum_step, 9)


def _compile_strict_trace(
    raw_frames: list[dict[str, Any]], spec: dict[str, Any]
) -> list[dict[str, Any]]:
    prefix = OBJECT_ID
    lift_rows = _phase(raw_frames, f"{prefix}_lift")
    required_z = (
        spec["table_top_z_m"]
        + spec["object_half_height_m"]
        + spec["required_lift_clearance_m"]
    )
    clear_rows = [
        frame
        for frame in lift_rows
        if frame["cube_positions_m"][OBJECT_ID][2] >= required_z
        and not frame["anchor_support_contacts"]
    ]
    lift = clear_rows[0] if clear_rows else lift_rows[-1]
    hold_candidates = [frame for frame in lift_rows if frame["frame_index"] > lift["frame_index"]]
    holds = hold_candidates[-2:] if len(hold_candidates) >= 2 else lift_rows[-2:]
    reclose = _phase(raw_frames, f"{prefix}_reclose_1")
    selected = [
        ("approach", _phase(raw_frames, f"{prefix}_approach")[0]),
        ("pregrasp", _phase(raw_frames, f"{prefix}_descend")[-1]),
        ("close", (reclose or _phase(raw_frames, f"{prefix}_close"))[-1]),
        ("grasp_confirmed", lift_rows[0]),
        ("lift", lift),
        ("stable_hold", holds[0]),
        ("stable_hold", holds[1]),
        ("lower", _phase(raw_frames, f"{prefix}_place")[-1]),
        ("release", _phase(raw_frames, f"{prefix}_release")[-1]),
        ("retreat", _phase(raw_frames, f"{prefix}_return_home")[-1]),
    ]
    return [_strict_frame(phase, frame) for phase, frame in selected]


def _strict_frame(phase: str, source: dict[str, Any]) -> dict[str, Any]:
    assist_active = bool(source["grasp_assists_active"])
    if assist_active:
        mechanism = "contact_gated_weld_assist"
    elif phase in {"close", "grasp_confirmed"}:
        mechanism = "grasp_contact"
    elif phase == "release":
        mechanism = "release"
    else:
        mechanism = "free_motion"
    return {
        "timestamp_ns": round(float(source["time_s"]) * 1_000_000_000),
        "source_frame_index": source["frame_index"],
        "phase": phase,
        "object_id": OBJECT_ID,
        "controller_owner": "causal_sort_expert_contact_gated_weld",
        "control_mode": "analytic_expert",
        "object_position_m": source["cube_positions_m"][OBJECT_ID],
        "gripper_position_m": source["gripper_position_m"],
        "fingertip_contacts": len(source["robot_cube_contacts"]),
        "object_table_contact": bool(source["anchor_support_contacts"]),
        "object_speed_m_s": source["anchor_speed_m_s"],
        "impact_force_n": source["robot_anchor_contact_force_n_max"],
        "actuator_current_ma_max": None,
        "actuator_effort_nm_max": source["actuator_effort_nm_max"],
        "mechanism": mechanism,
        "gripper_aperture_m": None,
        "forbidden_collision": bool(source["robot_self_contacts"]),
        "scripted_object_motion": False,
        "teleport_detected": source["anchor_step_displacement_m"] > 0.05,
        "actor_observation_fields": [
            "observation.state",
        ],
        "contact_gated_assist_active": assist_active,
    }


def _phase(raw_frames: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    rows = [frame for frame in raw_frames if frame["phase"] == name]
    if not rows:
        raise ValueError(f"MuJoCo anchor grasp phase is missing: {name}")
    return rows


def _file_evidence(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }


def _rounded(values: np.ndarray) -> list[float]:
    return [round(float(value), 9) for value in values]


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))

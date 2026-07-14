"""Lazy registry for uniform robot-lab artifact writers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactWriterSpec:
    module: str
    builder: str
    verifier: str
    output: str
    pass_repo_root: bool = False


# Keep module names as strings: listing available writers must not import a
# MuJoCo builder or any other expensive runtime.
ARTIFACT_WRITERS: dict[str, ArtifactWriterSpec] = {
    "experience_record_contract": ArtifactWriterSpec(
        "scenesmith.robot_lab.experience_records",
        "build_experience_record_contract",
        "verify_experience_record_contract",
        "configurations/robot_lab/experience_record_contract.json",
        True,
    ),
    "grasp_pose_solver_fixture": ArtifactWriterSpec(
        "scenesmith.robot_lab.grasp_pose_solver",
        "build_grasp_pose_solver_fixture",
        "verify_grasp_pose_solver_fixture",
        "configurations/robot_lab/grasp_pose_solver.fixture.json",
    ),
    "gripper_geometry_audit": ArtifactWriterSpec(
        "scenesmith.robot_lab.gripper_contact_semantics",
        "build_gripper_geometry_audit",
        "verify_gripper_geometry_audit",
        "configurations/robot_lab/gripper_geometry_audit.json",
    ),
    "mujoco_anchor_grasp_attempt": ArtifactWriterSpec(
        "scenesmith.robot_lab.mujoco_anchor_grasp",
        "build_mujoco_anchor_grasp_attempt",
        "verify_mujoco_anchor_grasp_attempt",
        "configurations/robot_lab/mujoco_anchor_grasp_attempt.json",
    ),
    "mujoco_contact_property_sweep": ArtifactWriterSpec(
        "scenesmith.robot_lab.mujoco_contact_property_sweep",
        "build_mujoco_contact_property_sweep",
        "verify_mujoco_contact_property_sweep",
        "configurations/robot_lab/mujoco_contact_property_sweep.json",
    ),
    "normalization_bundle": ArtifactWriterSpec(
        "scenesmith.robot_lab.normalization_bundle",
        "build_normalization_bundle",
        "verify_normalization_bundle",
        "configurations/robot_lab/normalization_bundle.json",
        True,
    ),
    "robotics_dependency_lock": ArtifactWriterSpec(
        "scenesmith.robot_lab.robotics_dependency_lock",
        "build_robotics_dependency_lock",
        "verify_robotics_dependency_lock",
        "configurations/robot_lab/pi05_robotics_dependency_lock.json",
        True,
    ),
    "so101_processor_contract": ArtifactWriterSpec(
        "scenesmith.robot_lab.so101_processor",
        "build_so101_processor_contract",
        "verify_so101_processor_contract",
        "configurations/robot_lab/so101_canonical_processor_contract.json",
        True,
    ),
    "strict_grasp_fixture": ArtifactWriterSpec(
        "scenesmith.robot_lab.strict_grasp",
        "build_strict_grasp_fixture",
        "verify_strict_grasp_fixture",
        "configurations/robot_lab/strict_anchor_grasp_evaluator.fixture.json",
    ),
    "strict_grasp_v2_fixture": ArtifactWriterSpec(
        "scenesmith.robot_lab.strict_grasp",
        "build_strict_grasp_v2_fixture",
        "verify_strict_grasp_v2_fixture",
        "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json",
    ),
}

"""Production-schema measured-inertial compiler with fixture-safe evidence semantics."""

from __future__ import annotations

import hashlib
import json
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    require_finite_number,
    require_nonblank,
    sign_payload,
    validate_content_addressed_evidence,
    validate_inertia_tensor,
    validate_unique_ids,
    verify_artifact_ref,
    verify_signed_payload,
)
from scenesmith.robot_lab.robotics_dependency_lock import (
    verify_robotics_dependency_lock,
)
from scenesmith.robot_lab.structural_twin_diff import (
    DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    verify_structural_twin_diff,
)
from scenesmith.robot_lab.twin_contract import (
    DEFAULT_DEPENDENCY_LOCK_PATH,
    DEFAULT_TWIN_PROFILE_PATH,
    verify_twin_profile,
)


PRODUCTION_INTAKE_SCHEMA_VERSION = "scenesmith.measured_inertial_intake.v2"
ASSEMBLY_INERTIALS_SCHEMA_VERSION = "scenesmith.assembly_inertials.v2"
PRODUCTION_FIXTURE_STATUS = "production_fixture"
PRODUCTION_INPUT_STATUS = "production_input"
FIXTURE_EVIDENCE_CLASS = "fixture"
PHYSICAL_EVIDENCE_CLASS = "physical"
DEFAULT_PRODUCTION_FIXTURE_PATH = Path(
    "tests/fixtures/robot_lab/measured_mass/production_mixed_source.fixture.json"
)
DEFAULT_PRODUCTION_OUTPUT_FIXTURE_PATH = Path(
    "tests/fixtures/robot_lab/measured_mass/production_mixed_source.output.json"
)

SOURCE_MODES = (
    "cad_scaled",
    "direct_inertia_tensor",
    "primitive_geometry",
    "point_mass",
    "lumped_component",
    "measured_rigid_assembly",
)
CANONICAL_UNITS = {
    "mass": "kilogram",
    "length": "meter",
    "inertia": "kilogram_meter_squared",
}
UNIT_FACTORS = {
    "mass": {"kilogram": 1.0, "gram": 1e-3},
    "length": {"meter": 1.0, "millimeter": 1e-3},
    "inertia": {
        "kilogram_meter_squared": 1.0,
        "gram_millimeter_squared": 1e-9,
    },
}
DERIVATIONS = {
    "cad_scaled": {
        "mass": "measured_scale",
        "center_of_mass": "cad_reference",
        "inertia": "cad_reference_mass_scaled",
    },
    "direct_inertia_tensor": {
        "mass": "measured_scale",
        "center_of_mass": "direct_measurement",
        "inertia": "direct_tensor_measurement",
    },
    "primitive_geometry": {
        "mass": "measured_scale",
        "center_of_mass": "direct_measurement",
        "inertia": "primitive_geometry",
    },
    "point_mass": {
        "mass": "measured_scale",
        "center_of_mass": "direct_measurement",
        "inertia": "point_mass_zero_about_com",
    },
    "lumped_component": {
        "mass": "measured_scale",
        "center_of_mass": "lumped_estimate",
        "inertia": "lumped_tensor_estimate",
    },
    "measured_rigid_assembly": {
        "mass": "measured_scale",
        "center_of_mass": "rigid_assembly_measurement",
        "inertia": "rigid_assembly_tensor_measurement",
    },
}
FORBIDDEN_GLOBAL_FIELDS = {
    "authority",
    "physical_qualification_authority",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "training_or_promotion_authority",
}


def build_production_fixture(*, repo_root: Path) -> dict[str, Any]:
    dependency_ref, profile_ref, structural_ref = _current_contract_refs(repo_root)
    assembly_id = "production_fixture_arm"
    target_frame = "production_fixture_arm_base_frame"
    components = [
        _component("fixture_root", None, target_frame, False, None),
        _component("base_group", "fixture_root", "base_group_frame", False, _transform()),
        _component(
            "cad_link",
            "base_group",
            "cad_link_frame",
            True,
            _transform(translation=[0.1, 0.0, 0.0]),
        ),
        _component(
            "point_payload",
            "base_group",
            "point_payload_frame",
            True,
            _transform(translation=[-0.1, 0.0, 0.0]),
        ),
        _component(
            "arm_group",
            "fixture_root",
            "arm_group_frame",
            False,
            _transform(
                translation=[0.0, 0.2, 0.0],
                rotation=[[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
            ),
        ),
        _component(
            "primitive_link",
            "arm_group",
            "primitive_link_frame",
            True,
            _transform(translation=[0.2, 0.0, 0.0]),
        ),
        _component(
            "tensor_link",
            "arm_group",
            "tensor_link_frame",
            True,
            _transform(translation=[0.4, 0.0, 0.0]),
        ),
        _component(
            "wrist_group",
            "arm_group",
            "wrist_group_frame",
            False,
            _transform(translation=[0.6, 0.0, 0.0]),
        ),
        _component(
            "lumped_cable",
            "wrist_group",
            "lumped_cable_frame",
            True,
            _transform(translation=[0.0, 0.1, 0.0]),
        ),
        _component(
            "gripper_assembly",
            "wrist_group",
            "gripper_assembly_frame",
            False,
            _transform(translation=[0.2, 0.0, 0.0]),
        ),
        _component(
            "finger_left",
            "gripper_assembly",
            "finger_left_frame",
            True,
            _transform(translation=[0.0, 0.05, 0.0]),
        ),
        _component(
            "finger_right",
            "gripper_assembly",
            "finger_right_frame",
            True,
            _transform(translation=[0.0, -0.05, 0.0]),
        ),
    ]
    measurements = [
        _measurement(
            repo_root=repo_root,
            measurement_id="fixture_cad_scaled",
            component_id="cad_link",
            source_mode="cad_scaled",
            native_units={
                "mass": "gram",
                "length": "millimeter",
                "inertia": "gram_millimeter_squared",
            },
            raw_values={
                "mass": 1000.0,
                "cad_reference": {
                    "mass": 900.0,
                    "center_of_mass": [10.0, 0.0, 0.0],
                    "inertia_about_com": [
                        [9000.0, 0.0, 0.0],
                        [0.0, 10000.0, 0.0],
                        [0.0, 0.0, 11000.0],
                    ],
                },
            },
            evidence_name="production-cad-scale-001.json",
            method="bench_scale_plus_cad",
            device_id="fixture-scale-cad-001",
            calibration_id="fixture-scale-cal-cad-001",
            assumptions=[
                "CAD center of mass is inherited without geometric rescaling.",
                "CAD inertia is scaled linearly by measured-to-reference mass ratio.",
            ],
            approximation={"mass": 0.0, "length": 1.0, "inertia": 500.0},
        ),
        _measurement(
            repo_root=repo_root,
            measurement_id="fixture_point_mass",
            component_id="point_payload",
            source_mode="point_mass",
            native_units=dict(CANONICAL_UNITS),
            raw_values={"mass": 0.2, "center_of_mass": [0.0, 0.03, 0.0]},
            evidence_name="production-point-mass-001.json",
            method="bench_scale_and_location_fixture",
            device_id="fixture-scale-point-001",
            calibration_id="fixture-scale-cal-point-001",
            assumptions=["The component is represented as a point mass about its own COM."],
            approximation={"mass": 0.0, "length": 0.001, "inertia": 0.00001},
        ),
        _measurement(
            repo_root=repo_root,
            measurement_id="fixture_primitive_geometry",
            component_id="primitive_link",
            source_mode="primitive_geometry",
            native_units={
                "mass": "gram",
                "length": "millimeter",
                "inertia": "gram_millimeter_squared",
            },
            raw_values={
                "mass": 500.0,
                "center_of_mass": [0.0, 0.0, 0.0],
                "geometry": {"shape": "box", "dimensions": [100.0, 40.0, 20.0]},
            },
            evidence_name="production-primitive-001.json",
            method="bench_scale_and_caliper_fixture",
            device_id="fixture-caliper-scale-001",
            calibration_id="fixture-caliper-scale-cal-001",
            assumptions=["Uniform-density rectangular box approximation."],
            approximation={"mass": 0.0, "length": 0.5, "inertia": 200.0},
        ),
        _measurement(
            repo_root=repo_root,
            measurement_id="fixture_direct_tensor",
            component_id="tensor_link",
            source_mode="direct_inertia_tensor",
            native_units=dict(CANONICAL_UNITS),
            raw_values={
                "mass": 0.8,
                "center_of_mass": [0.02, 0.0, 0.0],
                "inertia_about_com": [
                    [0.002, 0.0, 0.0],
                    [0.0, 0.003, 0.0],
                    [0.0, 0.0, 0.004],
                ],
            },
            evidence_name="production-direct-tensor-001.json",
            method="direct_inertia_fixture",
            device_id="fixture-inertia-rig-001",
            calibration_id="fixture-inertia-cal-001",
            assumptions=["Tensor is expressed about the measured COM in the component frame."],
            approximation={"mass": 0.0, "length": 0.0005, "inertia": 0.00005},
        ),
        _measurement(
            repo_root=repo_root,
            measurement_id="fixture_lumped_component",
            component_id="lumped_cable",
            source_mode="lumped_component",
            native_units=dict(CANONICAL_UNITS),
            raw_values={
                "mass": 0.3,
                "center_of_mass": [-0.01, 0.02, 0.0],
                "inertia_about_com": [
                    [0.0002, 0.0, 0.0],
                    [0.0, 0.0003, 0.0],
                    [0.0, 0.0, 0.0004],
                ],
            },
            evidence_name="production-lumped-001.json",
            method="lumped_component_fixture",
            device_id="fixture-lumped-estimator-001",
            calibration_id="fixture-lumped-cal-001",
            assumptions=["Cable bundle is represented by one lumped rigid component."],
            approximation={"mass": 0.0, "length": 0.005, "inertia": 0.0001},
        ),
        _measurement(
            repo_root=repo_root,
            measurement_id="fixture_measured_rigid_assembly",
            component_id="gripper_assembly",
            source_mode="measured_rigid_assembly",
            native_units={
                "mass": "gram",
                "length": "millimeter",
                "inertia": "gram_millimeter_squared",
            },
            raw_values={
                "mass": 400.0,
                "center_of_mass": [0.0, 0.0, 0.0],
                "inertia_about_com": [
                    [500000.0, 0.0, 0.0],
                    [0.0, 600000.0, 0.0],
                    [0.0, 0.0, 700000.0],
                ],
            },
            evidence_name="production-rigid-assembly-001.json",
            method="rigid_assembly_fixture",
            device_id="fixture-rigid-assembly-rig-001",
            calibration_id="fixture-rigid-assembly-cal-001",
            assumptions=[
                "Both required finger leaves are rigidly installed during assembly measurement."
            ],
            approximation={"mass": 0.0, "length": 0.5, "inertia": 5000.0},
        ),
    ]
    return sign_payload(
        {
            "schema_version": PRODUCTION_INTAKE_SCHEMA_VERSION,
            "intake_name": "production_mixed_source_fixture",
            "status": PRODUCTION_FIXTURE_STATUS,
            "evidence_class": FIXTURE_EVIDENCE_CLASS,
            "assembly": {
                "assembly_id": assembly_id,
                "root_component_id": "fixture_root",
                "target_rigid_body_frame_id": target_frame,
                "canonical_units": dict(CANONICAL_UNITS),
            },
            "dependency_lock_ref": dependency_ref,
            "twin_profile_ref": profile_ref,
            "structural_diff_ref": structural_ref,
            "components": components,
            "measurements": measurements,
        }
    )


def verify_production_intake(payload: dict[str, Any], *, repo_root: Path) -> None:
    context = _validate_and_index(payload, repo_root=repo_root)
    for measurement in context["measurements"]:
        _compile_source(measurement)


def compile_production_inertials(
    payload: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    context = _validate_and_index(payload, repo_root=repo_root)
    selected_results: list[dict[str, Any]] = []
    total_mass = 0.0
    weighted_com = [0.0, 0.0, 0.0]
    consumed_evidence: set[str] = set()
    mode_counts = {mode: 0 for mode in SOURCE_MODES}

    for measurement in context["measurements"]:
        component_id = measurement["component_id"]
        mass, local_com, local_inertia, trace = _compile_source(measurement)
        rotation, translation, transform_path = context["world_transforms"][component_id]
        target_com = _vector_add(translation, _matrix_vector(rotation, local_com))
        target_inertia = _rotate_inertia(rotation, local_inertia)
        _require_finite_tree(
            {"mass": mass, "com": target_com, "inertia": target_inertia},
            label=f"{measurement['measurement_id']} transformed result",
        )
        covered_leaves = context["coverage_by_measurement"][measurement["measurement_id"]]
        evidence_identities = sorted(item["sha256"] for item in measurement["evidence"])
        consumed_evidence.update(evidence_identities)
        mode_counts[measurement["source_mode"]] += 1
        total_mass = _finite_add(total_mass, mass, label="aggregate mass")
        weighted_com = [
            _finite_add(
                weighted_com[index],
                _finite_multiply(mass, target_com[index], label="weighted COM"),
                label="weighted COM",
            )
            for index in range(3)
        ]
        selected_results.append(
            {
                "measurement_id": measurement["measurement_id"],
                "component_id": component_id,
                "source_mode": measurement["source_mode"],
                "covered_required_leaf_component_ids": covered_leaves,
                "transform_path_component_ids": transform_path,
                "mass_kg_internal": mass,
                "center_of_mass_target_frame_m_internal": target_com,
                "inertia_about_component_com_target_frame_kg_m2_internal": target_inertia,
                "source_trace": trace,
                "evidence_identities": evidence_identities,
            }
        )

    if total_mass <= 0.0:
        raise ValueError("Production inertial aggregate mass must be positive")
    aggregate_com = [value / total_mass for value in weighted_com]
    _require_finite_tree(aggregate_com, label="aggregate center of mass")
    aggregate_inertia = _zero_matrix()
    for result in selected_results:
        displacement = [
            result["center_of_mass_target_frame_m_internal"][index] - aggregate_com[index]
            for index in range(3)
        ]
        shifted = _matrix_add(
            result["inertia_about_component_com_target_frame_kg_m2_internal"],
            _parallel_axis(result["mass_kg_internal"], displacement),
            label="parallel-axis aggregation",
        )
        aggregate_inertia = _matrix_add(
            aggregate_inertia,
            shifted,
            label="aggregate inertia",
        )
    validate_inertia_tensor(aggregate_inertia, label="aggregate inertia")

    serialized_results = []
    for result in sorted(selected_results, key=lambda item: item["measurement_id"]):
        serialized_results.append(
            {
                "measurement_id": result["measurement_id"],
                "component_id": result["component_id"],
                "source_mode": result["source_mode"],
                "covered_required_leaf_component_ids": result[
                    "covered_required_leaf_component_ids"
                ],
                "transform_path_component_ids": result["transform_path_component_ids"],
                "mass_kg": _round_number(result["mass_kg_internal"]),
                "center_of_mass_target_frame_m": _round_vector(
                    result["center_of_mass_target_frame_m_internal"]
                ),
                "inertia_about_component_com_target_frame_kg_m2": _round_matrix(
                    result["inertia_about_component_com_target_frame_kg_m2_internal"]
                ),
                "source_trace": result["source_trace"],
                "evidence_identities": result["evidence_identities"],
            }
        )

    output = {
        "schema_version": ASSEMBLY_INERTIALS_SCHEMA_VERSION,
        "artifact_name": f"{payload['intake_name']}_output",
        "status": "ready",
        "qualification_scope": (
            "fixture_evidence"
            if payload["evidence_class"] == FIXTURE_EVIDENCE_CLASS
            else "physical_measurement_evidence"
        ),
        "evidence_class": payload["evidence_class"],
        "assembly": json.loads(json.dumps(payload["assembly"])),
        "dependency_lock_ref": json.loads(json.dumps(payload["dependency_lock_ref"])),
        "twin_profile_ref": json.loads(json.dumps(payload["twin_profile_ref"])),
        "structural_diff_ref": json.loads(json.dumps(payload["structural_diff_ref"])),
        "intake_ref": _semantic_intake_ref(payload),
        "bom": {
            "root_component_id": context["root_component_id"],
            "component_count": len(context["components"]),
            "required_leaf_component_ids": context["required_leaf_ids"],
            "selected_component_ids": sorted(
                measurement["component_id"] for measurement in context["measurements"]
            ),
            "exact_cover_valid": True,
            "acyclic": True,
            "unique_transform_paths": True,
        },
        "source_mode_counts": mode_counts,
        "aggregate_physical_properties": {
            "mass_kg": _round_number(total_mass),
            "center_of_mass_target_frame_m": _round_vector(aggregate_com),
            "inertia_about_com_target_frame_kg_m2": _round_matrix(aggregate_inertia),
        },
        "selected_component_results": serialized_results,
        "consumed_evidence_identities": sorted(consumed_evidence),
        "capabilities": {
            "artifact_schema_valid": True,
            "inertial_compilation_valid": True,
            "inertial_model_usable_for_simulation": True,
            "physical_measurement_evidence_verified": (
                payload["evidence_class"] == PHYSICAL_EVIDENCE_CLASS
            ),
        },
        "authority_limitations": (
            [
                "Fixture evidence proves the production compiler path only.",
                "No current-arm physical measurement or global authority is established.",
            ]
            if payload["evidence_class"] == FIXTURE_EVIDENCE_CLASS
            else [
                "Physical measurement evidence is a local inertial capability only.",
                "No global training, transfer, deployment, or promotion authority is established.",
            ]
        ),
    }
    _require_finite_tree(output, label="production inertial output")
    return sign_payload(output)


def verify_production_output(
    output: dict[str, Any],
    *,
    intake: dict[str, Any],
    repo_root: Path,
) -> None:
    verify_signed_payload(output, label="Production assembly inertials")
    _reject_global_authority_fields(output)
    expected = compile_production_inertials(intake, repo_root=repo_root)
    if output != expected:
        raise ValueError("Production assembly inertials drifted from deterministic compilation")


def write_production_fixture_artifacts(
    *,
    repo_root: Path,
    intake_path: Path = DEFAULT_PRODUCTION_FIXTURE_PATH,
    output_path: Path = DEFAULT_PRODUCTION_OUTPUT_FIXTURE_PATH,
) -> dict[str, Any]:
    intake = build_production_fixture(repo_root=repo_root)
    output = compile_production_inertials(intake, repo_root=repo_root)
    dump_canonical_json(_resolve(repo_root, intake_path), intake)
    dump_canonical_json(_resolve(repo_root, output_path), output)
    return {"intake": intake, "output": output}


def verify_production_fixture_artifacts(
    *,
    repo_root: Path,
    intake_path: Path = DEFAULT_PRODUCTION_FIXTURE_PATH,
    output_path: Path = DEFAULT_PRODUCTION_OUTPUT_FIXTURE_PATH,
) -> dict[str, Any]:
    intake = load_strict_json(_resolve(repo_root, intake_path))
    output = load_strict_json(_resolve(repo_root, output_path))
    verify_production_intake(intake, repo_root=repo_root)
    verify_production_output(output, intake=intake, repo_root=repo_root)
    if intake != build_production_fixture(repo_root=repo_root):
        raise ValueError("Tracked production fixture intake drifted from deterministic build")
    return {"intake": intake, "output": output}


def _validate_and_index(payload: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    if payload.get("schema_version") != PRODUCTION_INTAKE_SCHEMA_VERSION:
        raise ValueError("Unsupported production measured-inertial intake schema")
    verify_signed_payload(payload, label="Production measured-inertial intake")
    _reject_global_authority_fields(payload)
    expected_fields = {
        "schema_version",
        "intake_name",
        "status",
        "evidence_class",
        "assembly",
        "dependency_lock_ref",
        "twin_profile_ref",
        "structural_diff_ref",
        "components",
        "measurements",
        "identity_sha256",
    }
    if set(payload) != expected_fields:
        raise ValueError("Production measured-inertial intake fields are malformed")
    require_nonblank(payload.get("intake_name"), label="production intake_name")
    status = payload.get("status")
    evidence_class = payload.get("evidence_class")
    expected_class_by_status = {
        PRODUCTION_FIXTURE_STATUS: FIXTURE_EVIDENCE_CLASS,
        PRODUCTION_INPUT_STATUS: PHYSICAL_EVIDENCE_CLASS,
    }
    if status not in expected_class_by_status:
        raise ValueError("Production intake status is invalid")
    if evidence_class != expected_class_by_status[status]:
        raise ValueError("Production intake status and evidence class disagree")
    dependency_ref, profile_ref, structural_ref = _current_contract_refs(repo_root)
    verify_artifact_ref(payload.get("dependency_lock_ref"), dependency_ref, label="Dependency lock")
    verify_artifact_ref(payload.get("twin_profile_ref"), profile_ref, label="Twin profile")
    verify_artifact_ref(payload.get("structural_diff_ref"), structural_ref, label="Structural diff")

    assembly = payload.get("assembly")
    if not isinstance(assembly, dict) or set(assembly) != {
        "assembly_id",
        "root_component_id",
        "target_rigid_body_frame_id",
        "canonical_units",
    }:
        raise ValueError("Production assembly metadata is malformed")
    require_nonblank(assembly.get("assembly_id"), label="assembly_id")
    root_component_id = require_nonblank(
        assembly.get("root_component_id"), label="root_component_id"
    )
    target_frame = require_nonblank(
        assembly.get("target_rigid_body_frame_id"),
        label="target_rigid_body_frame_id",
    )
    if assembly.get("canonical_units") != CANONICAL_UNITS:
        raise ValueError("Production assembly canonical units must be explicit SI units")

    components = payload.get("components")
    if not isinstance(components, list) or len(components) < 2:
        raise ValueError("Production BOM components are required")
    validate_unique_ids(components, field="component_id", label="component")
    component_index: dict[str, dict[str, Any]] = {}
    frame_ids: set[str] = set()
    for component in components:
        if not isinstance(component, dict) or set(component) != {
            "component_id",
            "parent_component_id",
            "frame_id",
            "required_leaf",
            "transform_to_parent",
        }:
            raise ValueError("Production BOM component fields are malformed")
        component_id = require_nonblank(component.get("component_id"), label="component_id")
        frame_id = require_nonblank(component.get("frame_id"), label=f"{component_id} frame_id")
        if frame_id in frame_ids:
            raise ValueError(f"Duplicate production BOM frame_id: {frame_id}")
        frame_ids.add(frame_id)
        if not isinstance(component.get("required_leaf"), bool):
            raise ValueError(f"Production BOM required_leaf must be boolean: {component_id}")
        component_index[component_id] = component
    if root_component_id not in component_index:
        raise ValueError("Production BOM root component is missing")
    roots = [
        component["component_id"]
        for component in components
        if component.get("parent_component_id") is None
    ]
    if roots != [root_component_id]:
        raise ValueError("Production BOM must contain exactly one declared root")
    if component_index[root_component_id]["frame_id"] != target_frame:
        raise ValueError("Production BOM root frame must equal the target rigid-body frame")
    if component_index[root_component_id].get("transform_to_parent") is not None:
        raise ValueError("Production BOM root must not carry a parent transform")

    children: dict[str, list[str]] = {component_id: [] for component_id in component_index}
    for component_id, component in component_index.items():
        if component_id == root_component_id:
            continue
        parent_id = require_nonblank(
            component.get("parent_component_id"),
            label=f"{component_id} parent_component_id",
        )
        if parent_id not in component_index:
            raise ValueError(f"Production BOM parent is unknown: {component_id}")
        if parent_id == component_id:
            raise ValueError(f"Production BOM self-cycle: {component_id}")
        children[parent_id].append(component_id)
        _validate_transform(
            component.get("transform_to_parent"),
            label=f"{component_id} transform_to_parent",
        )
    for child_ids in children.values():
        child_ids.sort()

    world_transforms: dict[str, tuple[list[list[float]], list[float], list[str]]] = {
        root_component_id: (_identity_matrix(), [0.0, 0.0, 0.0], [root_component_id])
    }
    visiting: set[str] = set()

    def resolve(component_id: str) -> tuple[list[list[float]], list[float], list[str]]:
        if component_id in world_transforms:
            return world_transforms[component_id]
        if component_id in visiting:
            raise ValueError(f"Production BOM cycle detected at: {component_id}")
        visiting.add(component_id)
        component = component_index[component_id]
        parent_id = str(component["parent_component_id"])
        parent_rotation, parent_translation, parent_path = resolve(parent_id)
        local = component["transform_to_parent"]
        local_rotation = _validate_rotation(
            local["rotation_matrix"], label=f"{component_id} rotation"
        )
        local_translation = _finite_vector(
            local["translation"], label=f"{component_id} translation"
        )
        rotation = _matrix_multiply(parent_rotation, local_rotation, label="transform rotation")
        translation = _vector_add(
            parent_translation,
            _matrix_vector(parent_rotation, local_translation),
        )
        result = (rotation, translation, [*parent_path, component_id])
        visiting.remove(component_id)
        world_transforms[component_id] = result
        return result

    for component_id in sorted(component_index):
        resolve(component_id)
    if set(world_transforms) != set(component_index):
        raise ValueError("Production BOM contains a disconnected component")

    required_leaf_ids = sorted(
        component_id
        for component_id, component in component_index.items()
        if component["required_leaf"]
    )
    if not required_leaf_ids:
        raise ValueError("Production BOM requires at least one required leaf")
    for component_id in required_leaf_ids:
        if children[component_id]:
            raise ValueError(f"Required production BOM component is not a leaf: {component_id}")

    def required_descendants(component_id: str) -> list[str]:
        found = [component_id] if component_id in required_leaf_ids else []
        for child_id in children[component_id]:
            found.extend(required_descendants(child_id))
        return sorted(found)

    measurements = payload.get("measurements")
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("Production measured-inertial measurements are required")
    validate_unique_ids(measurements, field="measurement_id", label="measurement")
    sorted_measurements = sorted(measurements, key=lambda item: str(item["measurement_id"]))
    selected_component_ids: set[str] = set()
    evidence_seen: set[tuple[str, str, str]] = set()
    evidence_digests_seen: set[str] = set()
    source_modes: set[str] = set()
    coverage_seen: set[str] = set()
    coverage_by_measurement: dict[str, list[str]] = {}
    for measurement in sorted_measurements:
        _validate_measurement_fields(
            measurement,
            expected_evidence_class=evidence_class,
        )
        measurement_id = measurement["measurement_id"]
        component_id = measurement["component_id"]
        if component_id not in component_index:
            raise ValueError(f"Production measurement component is unknown: {measurement_id}")
        if component_id in selected_component_ids:
            raise ValueError(f"Production component has multiple measurements: {component_id}")
        component_ancestors = set(world_transforms[component_id][2][:-1])
        for selected_component_id in selected_component_ids:
            selected_ancestors = set(world_transforms[selected_component_id][2][:-1])
            if (
                selected_component_id in component_ancestors
                or component_id in selected_ancestors
            ):
                raise ValueError(
                    "Production measurements select ancestor and descendant: "
                    f"{selected_component_id}, {component_id}"
                )
        selected_component_ids.add(component_id)
        source_mode = measurement["source_mode"]
        source_modes.add(source_mode)
        if source_mode == "measured_rigid_assembly":
            if not children[component_id]:
                raise ValueError("measured_rigid_assembly must select a non-leaf component")
        elif component_id not in required_leaf_ids:
            raise ValueError(f"Production leaf source mode selected a non-leaf: {component_id}")
        covered = required_descendants(component_id)
        if not covered:
            raise ValueError(f"Production measurement covers no required leaves: {measurement_id}")
        overlap = sorted(set(covered) & coverage_seen)
        if overlap:
            raise ValueError(
                "Production measurements overlap required leaf coverage: " + ", ".join(overlap)
            )
        coverage_seen.update(covered)
        coverage_by_measurement[measurement_id] = covered
        evidence_keys = validate_content_addressed_evidence(
            measurement["evidence"], label=measurement_id
        )
        reused = evidence_keys & evidence_seen
        if reused:
            raise ValueError(f"Production measurement evidence was reused: {measurement_id}")
        evidence_seen.update(evidence_keys)
        for evidence in measurement["evidence"]:
            if evidence["sha256"] in evidence_digests_seen:
                raise ValueError(f"Production measurement evidence was reused: {measurement_id}")
            evidence_digests_seen.add(evidence["sha256"])
            evidence_path = repo_root / evidence["ref"]
            if not evidence_path.is_file():
                raise ValueError(f"Production evidence file is missing: {evidence['ref']}")
            digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            if digest != evidence["sha256"]:
                raise ValueError(f"Production evidence hash drifted: {evidence['ref']}")
            evidence_payload = load_strict_json(evidence_path)
            if evidence_payload.get("evidence_class") != evidence_class:
                raise ValueError(f"Production evidence class mismatch: {evidence['ref']}")
            if evidence_payload.get("device_id") != measurement["provenance"]["device_id"]:
                raise ValueError(f"Production evidence device mismatch: {evidence['ref']}")
            if (
                evidence_payload.get("calibration_id")
                != measurement["provenance"]["calibration_id"]
            ):
                raise ValueError(f"Production evidence calibration mismatch: {evidence['ref']}")

    if coverage_seen != set(required_leaf_ids):
        missing = sorted(set(required_leaf_ids) - coverage_seen)
        extra = sorted(coverage_seen - set(required_leaf_ids))
        raise ValueError(
            "Production measurements do not form an exact required-leaf cover; "
            f"missing={missing}, extra={extra}"
        )
    if payload["status"] == PRODUCTION_FIXTURE_STATUS and source_modes != set(SOURCE_MODES):
        raise ValueError("Production fixture must exercise every supported source mode exactly")

    return {
        "root_component_id": root_component_id,
        "components": component_index,
        "children": children,
        "required_leaf_ids": required_leaf_ids,
        "measurements": sorted_measurements,
        "coverage_by_measurement": coverage_by_measurement,
        "world_transforms": world_transforms,
    }


def _validate_measurement_fields(
    measurement: dict[str, Any],
    *,
    expected_evidence_class: str,
) -> None:
    fields = {
        "measurement_id",
        "component_id",
        "source_mode",
        "evidence_class",
        "native_units",
        "canonical_units",
        "provenance",
        "derivation",
        "raw_values",
        "metrology",
        "evidence",
    }
    if not isinstance(measurement, dict) or set(measurement) != fields:
        raise ValueError("Production measurement fields are malformed")
    measurement_id = require_nonblank(
        measurement.get("measurement_id"), label="measurement_id"
    )
    require_nonblank(measurement.get("component_id"), label=f"{measurement_id} component_id")
    source_mode = measurement.get("source_mode")
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"Production measurement source mode is invalid: {measurement_id}")
    if measurement.get("evidence_class") != expected_evidence_class:
        raise ValueError("Production measurement evidence class drifted")
    _unit_factors(measurement.get("native_units"), measurement.get("canonical_units"))
    provenance = measurement.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {
        "method",
        "device_id",
        "calibration_id",
    }:
        raise ValueError(f"Production measurement provenance is malformed: {measurement_id}")
    for field in ("method", "device_id", "calibration_id"):
        require_nonblank(provenance.get(field), label=f"{measurement_id} {field}")
    if measurement.get("derivation") != DERIVATIONS[source_mode]:
        raise ValueError(f"Production measurement derivation drifted: {measurement_id}")
    if not isinstance(measurement.get("raw_values"), dict):
        raise ValueError(f"Production measurement raw_values are required: {measurement_id}")
    metrology = measurement.get("metrology")
    if not isinstance(metrology, dict) or set(metrology) != {
        "repeatability",
        "resolution",
        "uncertainty",
        "approximation_uncertainty",
        "inherited_assumptions",
    }:
        raise ValueError(f"Production measurement metrology is malformed: {measurement_id}")
    for category in (
        "repeatability",
        "resolution",
        "uncertainty",
        "approximation_uncertainty",
    ):
        values = metrology[category]
        if not isinstance(values, dict) or set(values) != {"mass", "length", "inertia"}:
            raise ValueError(f"Production {category} fields are malformed: {measurement_id}")
        for quantity, value in values.items():
            number = require_finite_number(value, label=f"{measurement_id} {category} {quantity}")
            if number < 0.0:
                raise ValueError(f"Production metrology must be nonnegative: {measurement_id}")
    assumptions = metrology["inherited_assumptions"]
    if not isinstance(assumptions, list) or not assumptions:
        raise ValueError(f"Production inherited assumptions are required: {measurement_id}")
    for assumption in assumptions:
        require_nonblank(assumption, label=f"{measurement_id} inherited assumption")
    validate_content_addressed_evidence(measurement.get("evidence"), label=measurement_id)


def _compile_source(
    measurement: dict[str, Any],
) -> tuple[float, list[float], list[list[float]], dict[str, Any]]:
    measurement_id = measurement["measurement_id"]
    source_mode = measurement["source_mode"]
    factors = _unit_factors(
        measurement["native_units"], measurement["canonical_units"]
    )
    raw = measurement["raw_values"]
    mass_native = require_finite_number(
        raw.get("mass"), label=f"{measurement_id} raw mass", positive=True
    )
    mass = _finite_multiply(mass_native, factors["mass"], label=f"{measurement_id} SI mass")
    extra_si: dict[str, Any] = {}

    if source_mode == "cad_scaled":
        if set(raw) != {"mass", "cad_reference"}:
            raise ValueError(f"cad_scaled raw fields are malformed: {measurement_id}")
        reference = raw["cad_reference"]
        if not isinstance(reference, dict) or set(reference) != {
            "mass",
            "center_of_mass",
            "inertia_about_com",
        }:
            raise ValueError(f"cad_scaled reference fields are malformed: {measurement_id}")
        reference_mass_native = require_finite_number(
            reference["mass"],
            label=f"{measurement_id} CAD reference mass",
            positive=True,
        )
        reference_mass = _finite_multiply(
            reference_mass_native,
            factors["mass"],
            label=f"{measurement_id} CAD reference SI mass",
        )
        local_com = _convert_vector(
            reference["center_of_mass"], factors["length"], label=f"{measurement_id} CAD COM"
        )
        reference_inertia = _convert_inertia(
            reference["inertia_about_com"],
            factors["inertia"],
            label=f"{measurement_id} CAD inertia",
        )
        ratio = mass / reference_mass
        local_inertia = _matrix_scale(
            reference_inertia,
            ratio,
            label=f"{measurement_id} mass-scaled CAD inertia",
        )
        extra_si = {"cad_reference_mass_kg": reference_mass, "mass_scale_ratio": ratio}
    elif source_mode in {
        "direct_inertia_tensor",
        "lumped_component",
        "measured_rigid_assembly",
    }:
        if set(raw) != {"mass", "center_of_mass", "inertia_about_com"}:
            raise ValueError(f"{source_mode} raw fields are malformed: {measurement_id}")
        local_com = _convert_vector(
            raw["center_of_mass"], factors["length"], label=f"{measurement_id} COM"
        )
        local_inertia = _convert_inertia(
            raw["inertia_about_com"],
            factors["inertia"],
            label=f"{measurement_id} inertia",
        )
    elif source_mode == "primitive_geometry":
        if set(raw) != {"mass", "center_of_mass", "geometry"}:
            raise ValueError(f"primitive_geometry raw fields are malformed: {measurement_id}")
        local_com = _convert_vector(
            raw["center_of_mass"], factors["length"], label=f"{measurement_id} COM"
        )
        local_inertia, extra_si = _primitive_inertia(
            mass,
            raw["geometry"],
            length_factor=factors["length"],
            label=measurement_id,
        )
    elif source_mode == "point_mass":
        if set(raw) != {"mass", "center_of_mass"}:
            raise ValueError(f"point_mass raw fields are malformed: {measurement_id}")
        local_com = _convert_vector(
            raw["center_of_mass"], factors["length"], label=f"{measurement_id} COM"
        )
        local_inertia = _zero_matrix()
    else:
        raise ValueError(f"Unsupported production source mode: {source_mode}")

    validate_inertia_tensor(local_inertia, label=f"{measurement_id} compiled inertia")
    metrology_si = _convert_metrology(measurement["metrology"], factors)
    trace = {
        "evidence_class": measurement["evidence_class"],
        "native_units": json.loads(json.dumps(measurement["native_units"])),
        "canonical_units": json.loads(json.dumps(measurement["canonical_units"])),
        "raw_values_native": json.loads(json.dumps(raw)),
        "si_values": {
            "mass_kg": _round_number(mass),
            "center_of_mass_component_frame_m": _round_vector(local_com),
            "inertia_about_com_component_frame_kg_m2": _round_matrix(local_inertia),
            **_round_tree(extra_si),
        },
        "derivation": json.loads(json.dumps(measurement["derivation"])),
        "provenance": json.loads(json.dumps(measurement["provenance"])),
        "metrology_native": json.loads(json.dumps(measurement["metrology"])),
        "metrology_si": metrology_si,
        "evidence": sorted(
            json.loads(json.dumps(measurement["evidence"])),
            key=lambda item: (item["kind"], item["ref"], item["sha256"]),
        ),
    }
    return mass, local_com, local_inertia, trace


def _primitive_inertia(
    mass: float,
    geometry: Any,
    *,
    length_factor: float,
    label: str,
) -> tuple[list[list[float]], dict[str, Any]]:
    if not isinstance(geometry, dict) or set(geometry) != {"shape", "dimensions"}:
        raise ValueError(f"Primitive geometry fields are malformed: {label}")
    shape = geometry["shape"]
    dimensions = _convert_vector(
        geometry["dimensions"], length_factor, label=f"{label} primitive dimensions"
    )
    if shape == "box":
        if len(dimensions) != 3 or any(value <= 0.0 for value in dimensions):
            raise ValueError(f"Box dimensions must be three positive values: {label}")
        x, y, z = dimensions
        inertia = [
            [mass * (y * y + z * z) / 12.0, 0.0, 0.0],
            [0.0, mass * (x * x + z * z) / 12.0, 0.0],
            [0.0, 0.0, mass * (x * x + y * y) / 12.0],
        ]
    elif shape == "solid_sphere":
        if len(dimensions) != 1 or dimensions[0] <= 0.0:
            raise ValueError(f"Sphere radius must be positive: {label}")
        moment = 0.4 * mass * dimensions[0] * dimensions[0]
        inertia = [[moment, 0.0, 0.0], [0.0, moment, 0.0], [0.0, 0.0, moment]]
    elif shape == "solid_cylinder_z":
        if len(dimensions) != 2 or any(value <= 0.0 for value in dimensions):
            raise ValueError(f"Cylinder radius and length must be positive: {label}")
        radius, length = dimensions
        transverse = mass * (3.0 * radius * radius + length * length) / 12.0
        axial = 0.5 * mass * radius * radius
        inertia = [
            [transverse, 0.0, 0.0],
            [0.0, transverse, 0.0],
            [0.0, 0.0, axial],
        ]
    else:
        raise ValueError(f"Unsupported primitive shape: {shape}")
    _require_finite_tree(inertia, label=f"{label} primitive inertia")
    return inertia, {
        "primitive_shape": shape,
        "primitive_dimensions_m": _round_vector(dimensions),
    }


def _unit_factors(native: Any, canonical: Any) -> dict[str, float]:
    if not isinstance(native, dict) or set(native) != set(CANONICAL_UNITS):
        raise ValueError("Production native units must explicitly name mass, length, and inertia")
    if canonical != CANONICAL_UNITS:
        raise ValueError("Production canonical units must be exact SI units")
    factors: dict[str, float] = {}
    for quantity in CANONICAL_UNITS:
        unit = native[quantity]
        if unit not in UNIT_FACTORS[quantity]:
            raise ValueError(f"Unsupported production {quantity} unit: {unit}")
        factors[quantity] = UNIT_FACTORS[quantity][unit]
    return factors


def _convert_metrology(
    metrology: dict[str, Any], factors: dict[str, float]
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for category in (
        "repeatability",
        "resolution",
        "uncertainty",
        "approximation_uncertainty",
    ):
        output[category] = {
            quantity: _round_number(
                _finite_multiply(
                    float(metrology[category][quantity]),
                    factors[quantity],
                    label=f"{category} {quantity} SI conversion",
                )
            )
            for quantity in CANONICAL_UNITS
        }
    output["inherited_assumptions"] = list(metrology["inherited_assumptions"])
    return output


def _current_contract_refs(
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    dependency_payload = load_strict_json(repo_root / DEFAULT_DEPENDENCY_LOCK_PATH)
    verify_robotics_dependency_lock(dependency_payload, repo_root=repo_root)
    dependency_ref = artifact_ref(
        path=DEFAULT_DEPENDENCY_LOCK_PATH,
        payload=dependency_payload,
        repo_root=repo_root,
    )
    profile_payload = load_strict_json(repo_root / DEFAULT_TWIN_PROFILE_PATH)
    verify_twin_profile(profile_payload, repo_root=repo_root)
    profile_ref = artifact_ref(
        path=DEFAULT_TWIN_PROFILE_PATH,
        payload=profile_payload,
        repo_root=repo_root,
    )
    structural_payload = load_strict_json(repo_root / DEFAULT_STRUCTURAL_TWIN_DIFF_PATH)
    verify_structural_twin_diff(structural_payload, repo_root=repo_root)
    structural_ref = artifact_ref(
        path=DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
        payload=structural_payload,
        repo_root=repo_root,
    )
    return dependency_ref, profile_ref, structural_ref


def _measurement(
    *,
    repo_root: Path,
    measurement_id: str,
    component_id: str,
    source_mode: str,
    native_units: dict[str, str],
    raw_values: dict[str, Any],
    evidence_name: str,
    method: str,
    device_id: str,
    calibration_id: str,
    assumptions: list[str],
    approximation: dict[str, float],
) -> dict[str, Any]:
    evidence_path = Path("tests/fixtures/robot_lab/measured_mass/evidence") / evidence_name
    digest = hashlib.sha256((repo_root / evidence_path).read_bytes()).hexdigest()
    return {
        "measurement_id": measurement_id,
        "component_id": component_id,
        "source_mode": source_mode,
        "evidence_class": FIXTURE_EVIDENCE_CLASS,
        "native_units": native_units,
        "canonical_units": dict(CANONICAL_UNITS),
        "provenance": {
            "method": method,
            "device_id": device_id,
            "calibration_id": calibration_id,
        },
        "derivation": dict(DERIVATIONS[source_mode]),
        "raw_values": raw_values,
        "metrology": {
            "repeatability": {"mass": 0.1, "length": 0.1, "inertia": 1.0},
            "resolution": {"mass": 0.1, "length": 0.1, "inertia": 1.0},
            "uncertainty": {"mass": 0.2, "length": 0.2, "inertia": 2.0},
            "approximation_uncertainty": approximation,
            "inherited_assumptions": assumptions,
        },
        "evidence": [
            {
                "kind": "production_fixture_measurement",
                "ref": str(evidence_path),
                "sha256": digest,
            }
        ],
    }


def _component(
    component_id: str,
    parent_component_id: str | None,
    frame_id: str,
    required_leaf: bool,
    transform_to_parent: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "parent_component_id": parent_component_id,
        "frame_id": frame_id,
        "required_leaf": required_leaf,
        "transform_to_parent": transform_to_parent,
    }


def _transform(
    *,
    translation: list[float] | None = None,
    rotation: list[list[float]] | None = None,
) -> dict[str, Any]:
    return {
        "translation": translation or [0.0, 0.0, 0.0],
        "rotation_matrix": rotation or _identity_matrix(),
    }


def _validate_transform(value: Any, *, label: str) -> None:
    if not isinstance(value, dict) or set(value) != {"translation", "rotation_matrix"}:
        raise ValueError(f"{label} is malformed")
    _finite_vector(value["translation"], label=f"{label} translation")
    _validate_rotation(value["rotation_matrix"], label=f"{label} rotation")


def _validate_rotation(value: Any, *, label: str) -> list[list[float]]:
    matrix = _finite_matrix(value, label=label)
    product = _matrix_multiply(_transpose(matrix), matrix, label=f"{label} orthogonality")
    scale = max(1.0, max(abs(item) for row in product for item in row))
    tolerance = 1e-12 * scale
    for row in range(3):
        for column in range(3):
            expected = 1.0 if row == column else 0.0
            if abs(product[row][column] - expected) > tolerance:
                raise ValueError(f"{label} must be orthonormal")
    determinant = (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )
    if abs(determinant - 1.0) > 1e-12:
        raise ValueError(f"{label} must be a proper rotation")
    return matrix


def _semantic_intake_ref(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        key: value
        for key, value in payload.items()
        if key not in {"identity_sha256", "components", "measurements"}
    }
    normalized["components"] = sorted(
        payload["components"], key=lambda item: item["component_id"]
    )
    normalized["measurements"] = []
    for measurement in sorted(payload["measurements"], key=lambda item: item["measurement_id"]):
        copied = json.loads(json.dumps(measurement))
        copied["evidence"] = sorted(
            copied["evidence"], key=lambda item: (item["kind"], item["ref"], item["sha256"])
        )
        normalized["measurements"].append(copied)
    identity = hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()
    return {
        "path": f"fixture_evidence://{payload['intake_name']}",
        "schema_version": payload["schema_version"],
        "identity_sha256": identity,
    }


def _reject_global_authority_fields(payload: Any) -> None:
    found: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in FORBIDDEN_GLOBAL_FIELDS:
                    found.add(key)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    if found:
        raise ValueError(
            "Production inertial payload carries forbidden global-authority fields: "
            + ", ".join(sorted(found))
        )


def _convert_vector(values: Any, factor: float, *, label: str) -> list[float]:
    return [
        _finite_multiply(value, factor, label=f"{label} SI conversion")
        for value in _finite_vector(values, label=label)
    ]


def _convert_inertia(values: Any, factor: float, *, label: str) -> list[list[float]]:
    matrix = _finite_matrix(values, label=label)
    converted = _matrix_scale(matrix, factor, label=f"{label} SI conversion")
    validate_inertia_tensor(converted, label=label)
    return converted


def _finite_vector(values: Any, *, label: str) -> list[float]:
    if not isinstance(values, list):
        raise ValueError(f"{label} must be a finite vector")
    return [require_finite_number(value, label=label) for value in values]


def _finite_matrix(values: Any, *, label: str) -> list[list[float]]:
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{label} must be a 3x3 finite matrix")
    matrix = [_finite_vector(row, label=label) for row in values]
    if any(len(row) != 3 for row in matrix):
        raise ValueError(f"{label} must be a 3x3 finite matrix")
    return matrix


def _matrix_multiply(
    left: list[list[float]],
    right: list[list[float]],
    *,
    label: str,
) -> list[list[float]]:
    result = [
        [
            sum(left[row][index] * right[index][column] for index in range(3))
            for column in range(3)
        ]
        for row in range(3)
    ]
    _require_finite_tree(result, label=label)
    return result


def _matrix_vector(matrix: list[list[float]], vector: list[float]) -> list[float]:
    result = [sum(matrix[row][column] * vector[column] for column in range(3)) for row in range(3)]
    _require_finite_tree(result, label="matrix-vector product")
    return result


def _matrix_scale(
    matrix: list[list[float]], scalar: float, *, label: str
) -> list[list[float]]:
    result = [
        [_finite_multiply(value, scalar, label=label) for value in row] for row in matrix
    ]
    _require_finite_tree(result, label=label)
    return result


def _matrix_add(
    left: list[list[float]],
    right: list[list[float]],
    *,
    label: str,
) -> list[list[float]]:
    result = [
        [
            _finite_add(left[row][column], right[row][column], label=label)
            for column in range(3)
        ]
        for row in range(3)
    ]
    return result


def _rotate_inertia(
    rotation: list[list[float]], inertia: list[list[float]]
) -> list[list[float]]:
    return _matrix_multiply(
        _matrix_multiply(rotation, inertia, label="inertia rotation"),
        _transpose(rotation),
        label="inertia rotation",
    )


def _parallel_axis(mass: float, displacement: list[float]) -> list[list[float]]:
    dx, dy, dz = displacement
    norm_sq = dx * dx + dy * dy + dz * dz
    _require_finite_tree(norm_sq, label="parallel-axis displacement")
    outer = [
        [dx * dx, dx * dy, dx * dz],
        [dy * dx, dy * dy, dy * dz],
        [dz * dx, dz * dy, dz * dz],
    ]
    result = [
        [
            _finite_multiply(
                mass,
                (norm_sq if row == column else 0.0) - outer[row][column],
                label="parallel-axis term",
            )
            for column in range(3)
        ]
        for row in range(3)
    ]
    return result


def _vector_add(left: list[float], right: list[float]) -> list[float]:
    return [_finite_add(left[index], right[index], label="vector addition") for index in range(3)]


def _finite_add(left: float, right: float, *, label: str) -> float:
    result = left + right
    if not math.isfinite(result):
        raise ValueError(f"{label} produced a non-finite result")
    return result


def _finite_multiply(left: Any, right: Any, *, label: str) -> float:
    result = float(left) * float(right)
    if not math.isfinite(result):
        raise ValueError(f"{label} produced a non-finite result")
    return result


def _require_finite_tree(value: Any, *, label: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{label} contains a non-finite value")
    if isinstance(value, dict):
        for child in value.values():
            _require_finite_tree(child, label=label)
    elif isinstance(value, list):
        for child in value:
            _require_finite_tree(child, label=label)


def _identity_matrix() -> list[list[float]]:
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [[matrix[row][column] for row in range(3)] for column in range(3)]


def _zero_matrix() -> list[list[float]]:
    return [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]


def _round_number(value: float) -> float:
    rounded = round(value, 12)
    return 0.0 if rounded == 0.0 else rounded


def _round_vector(values: list[float]) -> list[float]:
    return [_round_number(value) for value in values]


def _round_matrix(values: list[list[float]]) -> list[list[float]]:
    return [_round_vector(row) for row in values]


def _round_tree(value: Any) -> Any:
    if isinstance(value, float):
        return _round_number(value)
    if isinstance(value, dict):
        return {key: _round_tree(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_round_tree(child) for child in value]
    return value


def _resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path

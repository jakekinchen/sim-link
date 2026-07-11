"""Truthful measured-mass intake and blocked assembly inertial artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.robotics_dependency_lock import verify_robotics_dependency_lock
from scenesmith.robot_lab.structural_twin_diff import (
    DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    verify_structural_twin_diff,
)
from scenesmith.robot_lab.twin_contract import (
    DEFAULT_DEPENDENCY_LOCK_PATH,
    DEFAULT_TWIN_PROFILE_PATH,
    verify_twin_profile,
)


MEASURED_MASS_INTAKE_SCHEMA_VERSION = "scenesmith.measured_mass_intake.v1"
ASSEMBLY_INERTIALS_SCHEMA_VERSION = "scenesmith.assembly_inertials.v1"
DEFAULT_MEASURED_MASS_INTAKE_PATH = Path(
    "configurations/robot_lab/pi05_measured_mass_intake.awaiting_measurements.json"
)
DEFAULT_ASSEMBLY_INERTIALS_PATH = Path(
    "configurations/robot_lab/pi05_assembly_inertials.blocked_missing_measurements.json"
)
CURRENT_ASSEMBLY_ID = "pi05_current_arm"
CURRENT_ASSEMBLY_FRAME_ID = "pi05_current_arm_base_frame"
BODY_FRAME_SUFFIX = "_frame"
MEASURED_INTAKE_STATUS = "awaiting_measurements"
BLOCKED_ASSEMBLY_STATUS = "blocked_missing_measurements"
READY_ASSEMBLY_STATUS = "ready"
SYNTHETIC_TEST_ONLY_STATUS = "synthetic_test_only"
KNOWN_MISSING_CATEGORY_SPECS = (
    (
        "servo_actuators",
        "per-axis servos/actuators",
        "The repository does not prove the installed servo BOM or the measured servo masses.",
    ),
    (
        "horns_and_bearings",
        "horns/bearings",
        "The repository does not prove the installed horn and bearing part counts or masses.",
    ),
    (
        "fasteners",
        "fasteners",
        "The repository does not prove the installed fastener inventory or masses.",
    ),
    (
        "wrist_camera_and_mount",
        "wrist camera and mount",
        "The repository does not carry measured wrist-camera or mount masses for the current arm.",
    ),
    (
        "wiring_and_cable_bundles",
        "wiring/cable bundles",
        "The repository does not prove the installed wire/cable routing or masses.",
    ),
    (
        "gripper_fingertips_and_pads",
        "gripper fingertips/pads",
        "The repository does not prove the installed fingertip or pad masses.",
    ),
    (
        "attachments_and_payloads",
        "attachments/payloads",
        "The repository does not prove any installed attachment or payload mass inventory.",
    ),
)


def build_measured_mass_intake(
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    structural_diff_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
) -> dict[str, Any]:
    dependency_lock = _dependency_lock_ref(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    twin_profile = _twin_profile_ref(
        repo_root=repo_root,
        twin_profile_path=twin_profile_path,
        dependency_lock_path=dependency_lock_path,
    )
    structural_diff = _structural_diff_ref(
        repo_root=repo_root,
        structural_diff_path=structural_diff_path,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
    )
    runtime_source = dependency_lock["payload"]["runtime_contract"]["source_mjcf"]
    geometry_priors = _extract_geometry_priors(
        repo_root=repo_root,
        runtime_source=runtime_source,
    )
    components, coverage_atoms = _build_component_inventory(geometry_priors)
    unresolved_inventory = [
        {
            "inventory_id": f"missing_{category_id}",
            "category_id": category_id,
            "category_label": label,
            "required_for_ready": True,
            "reason": reason,
        }
        for category_id, label, reason in KNOWN_MISSING_CATEGORY_SPECS
    ]
    return _sign(
        {
            "schema_version": MEASURED_MASS_INTAKE_SCHEMA_VERSION,
            "intake_name": "pi05_measured_mass_intake_current_arm",
            "status": MEASURED_INTAKE_STATUS,
            "assembly": {
                "assembly_id": CURRENT_ASSEMBLY_ID,
                "assembly_frame_id": CURRENT_ASSEMBLY_FRAME_ID,
                "frame_units": "meter",
            },
            "dependency_lock_ref": dependency_lock["ref"],
            "twin_profile_ref": twin_profile["ref"],
            "structural_diff_ref": structural_diff["ref"],
            "measurements": [],
            "components": components,
            "coverage_atoms": coverage_atoms,
            "missing_inventory_categories": [item["category_id"] for item in unresolved_inventory],
            "unresolved_inventory": unresolved_inventory,
            "cad_priors": geometry_priors,
            "coverage_rules": {
                "measured_origin_required_for_ready": True,
                "pairwise_disjoint_required": True,
                "required_atom_exact_cover": True,
                "cad_priors_do_not_satisfy_measured_coverage": True,
            },
        }
    )


def build_assembly_inertials(
    *,
    repo_root: Path,
    intake_path: Path = DEFAULT_MEASURED_MASS_INTAKE_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    structural_diff_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
) -> dict[str, Any]:
    intake = _measured_mass_intake_ref(
        repo_root=repo_root,
        intake_path=intake_path,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
        structural_diff_path=structural_diff_path,
    )
    if intake["payload"].get("status") == SYNTHETIC_TEST_ONLY_STATUS:
        return _build_synthetic_ready_assembly_inertials(intake=intake)
    return _build_blocked_assembly_inertials(intake=intake)


def _build_blocked_assembly_inertials(*, intake: dict[str, Any]) -> dict[str, Any]:
    required_atom_ids = [
        atom["atom_id"] for atom in intake["payload"]["coverage_atoms"] if atom["required_for_ready"]
    ]
    cad_prior_total_mass_kg = round(
        sum(float(entry["source_mass_kg"]) for entry in intake["payload"]["cad_priors"]),
        9,
    )
    return _sign(
        {
            "schema_version": ASSEMBLY_INERTIALS_SCHEMA_VERSION,
            "artifact_name": "pi05_assembly_inertials_current_arm",
            "status": BLOCKED_ASSEMBLY_STATUS,
            "assembly": dict(intake["payload"]["assembly"]),
            "dependency_lock_ref": intake["payload"]["dependency_lock_ref"],
            "twin_profile_ref": intake["payload"]["twin_profile_ref"],
            "structural_diff_ref": intake["payload"]["structural_diff_ref"],
            "intake_ref": intake["ref"],
            "coverage": {
                "required_atom_ids": required_atom_ids,
                "selected_measurement_ids": [],
                "selected_atom_ids": [],
                "missing_atom_ids": required_atom_ids,
                "unresolved_inventory_ids": [
                    entry["inventory_id"] for entry in intake["payload"]["unresolved_inventory"]
                ],
                "missing_inventory_categories": list(
                    intake["payload"]["missing_inventory_categories"]
                ),
            },
            "aggregate_physical_properties": {
                "mass_kg": None,
                "center_of_mass_assembly_frame_m": None,
                "inertia_about_com_assembly_frame_kg_m2": None,
            },
            "rejected_measurements": [],
            "rejected_evidence": [],
            "unresolved_evidence": list(intake["payload"]["unresolved_inventory"]),
            "blocking_reasons": [
                "No measured-mass evidence is checked into repo state for the current arm.",
                "CAD/MJCF priors remain separate from measured coverage and cannot authorize readiness.",
            ],
            "cad_prior_summary": {
                "prior_count": len(intake["payload"]["cad_priors"]),
                "source_mass_total_kg": cad_prior_total_mass_kg,
                "origin": "CAD",
            },
            "physical_qualification_authority": False,
            "training_or_promotion_authority": False,
        }
    )


def _build_synthetic_ready_assembly_inertials(*, intake: dict[str, Any]) -> dict[str, Any]:
    payload = intake["payload"]
    assembly = payload["assembly"]
    components_by_id = {
        str(component["component_id"]): component for component in payload["components"]
    }
    atoms_by_id = {
        str(atom["atom_id"]): atom for atom in payload["coverage_atoms"]
    }
    priors_by_id = {
        str(prior["prior_id"]): prior for prior in payload["cad_priors"]
    }
    required_atom_ids = sorted(
        atom_id for atom_id, atom in atoms_by_id.items() if bool(atom.get("required_for_ready"))
    )
    selected_measurements = sorted(
        payload["measurements"],
        key=lambda measurement: str(measurement["measurement_id"]),
    )
    selected_atom_ids: list[str] = []
    selected_measurement_ids: list[str] = []
    seen_atoms: set[str] = set()
    seen_evidence: set[tuple[str, str]] = set()
    component_results: list[dict[str, Any]] = []
    total_mass = 0.0
    weighted_com = [0.0, 0.0, 0.0]
    for measurement in selected_measurements:
        measurement_id = str(measurement["measurement_id"])
        component_id = str(measurement["component_id"])
        if component_id not in components_by_id:
            raise ValueError(f"Synthetic measurement references unknown component: {measurement_id}")
        prior_id = str(measurement["source_prior_id"])
        if prior_id not in priors_by_id:
            raise ValueError(f"Synthetic measurement references unknown prior: {measurement_id}")
        if measurement.get("origin") != "measured":
            raise ValueError(f"Synthetic measurement origin must be measured: {measurement_id}")
        covered_atom_ids = sorted(str(atom_id) for atom_id in measurement.get("covered_atom_ids", []))
        if len(covered_atom_ids) != 1:
            raise ValueError(f"Synthetic measurement must cover exactly one atom: {measurement_id}")
        atom_id = covered_atom_ids[0]
        if atom_id in seen_atoms:
            raise ValueError(f"Synthetic coverage atom was selected more than once: {atom_id}")
        atom = atoms_by_id.get(atom_id)
        if atom is None:
            raise ValueError(f"Synthetic measurement references unknown atom: {measurement_id}")
        if atom.get("component_id") != component_id:
            raise ValueError(f"Synthetic measurement component/atom mismatch: {measurement_id}")
        if atom.get("assembly_id") != assembly["assembly_id"]:
            raise ValueError(f"Synthetic measurement assembly drifted: {measurement_id}")
        if atom.get("assembly_frame_id") != assembly["assembly_frame_id"]:
            raise ValueError(f"Synthetic measurement frame drifted: {measurement_id}")
        evidence_items = measurement.get("evidence")
        if not isinstance(evidence_items, list) or not evidence_items:
            raise ValueError(f"Synthetic measurement evidence is required: {measurement_id}")
        for evidence in evidence_items:
            evidence_key = (str(evidence.get("kind")), str(evidence.get("ref")))
            if evidence_key in seen_evidence:
                raise ValueError(f"Synthetic measurement evidence was reused: {measurement_id}")
            seen_evidence.add(evidence_key)

        prior = priors_by_id[prior_id]
        source_mass = float(prior["source_mass_kg"])
        measured_mass = float(measurement["measured_mass_kg"])
        if source_mass <= 0.0 or measured_mass <= 0.0:
            raise ValueError(f"Synthetic measurement masses must be positive: {measurement_id}")
        rotation = _validate_rotation_matrix(
            prior["body_frame_to_assembly"]["rotation_matrix"],
            label=f"{prior_id} rotation",
        )
        translation = _validate_vector(
            prior["body_frame_to_assembly"]["translation_m"],
            expected=3,
            label=f"{prior_id} translation",
        )
        com_body = _validate_vector(
            prior["source_center_of_mass_body_frame_m"],
            expected=3,
            label=f"{prior_id} source COM",
        )
        inertia_body = _validate_inertia_matrix(
            prior["source_inertia_about_com_body_frame_kg_m2"],
            label=f"{prior_id} source inertia",
        )
        scaled_inertia = _matrix_scale(inertia_body, measured_mass / source_mass)
        component_com = _vector_add(translation, _matrix_vector_multiply(rotation, com_body))
        component_inertia = _rotate_inertia(rotation, scaled_inertia)

        selected_atom_ids.append(atom_id)
        selected_measurement_ids.append(measurement_id)
        seen_atoms.add(atom_id)
        total_mass += measured_mass
        weighted_com = [
            weighted_com[index] + measured_mass * component_com[index] for index in range(3)
        ]
        component_results.append(
            {
                "measurement_id": measurement_id,
                "component_id": component_id,
                "atom_id": atom_id,
                "mass_kg": measured_mass,
                "center_of_mass_assembly_frame_m": _round_vector(component_com),
                "inertia_about_component_com_assembly_frame_kg_m2": _round_matrix(component_inertia),
            }
        )
    if selected_atom_ids != required_atom_ids:
        raise ValueError("Synthetic measurements did not form an exact cover of required atoms")
    aggregate_com = [weighted_com[index] / total_mass for index in range(3)]
    aggregate_inertia = _zero_matrix()
    for component_result in component_results:
        component_mass = float(component_result["mass_kg"])
        component_com = component_result["center_of_mass_assembly_frame_m"]
        displacement = [
            component_com[index] - aggregate_com[index] for index in range(3)
        ]
        aggregate_inertia = _matrix_add(
            aggregate_inertia,
            _matrix_add(
                component_result["inertia_about_component_com_assembly_frame_kg_m2"],
                _parallel_axis_term(component_mass, displacement),
            ),
        )
    component_results.sort(key=lambda item: item["measurement_id"])
    return _sign(
        {
            "schema_version": ASSEMBLY_INERTIALS_SCHEMA_VERSION,
            "artifact_name": "synthetic_measured_inertials_ready",
            "status": READY_ASSEMBLY_STATUS,
            "qualification_scope": SYNTHETIC_TEST_ONLY_STATUS,
            "assembly": dict(assembly),
            "dependency_lock_ref": payload["dependency_lock_ref"],
            "twin_profile_ref": payload["twin_profile_ref"],
            "structural_diff_ref": payload["structural_diff_ref"],
            "intake_ref": _synthetic_intake_semantic_ref(payload),
            "coverage": {
                "required_atom_ids": required_atom_ids,
                "selected_measurement_ids": selected_measurement_ids,
                "selected_atom_ids": selected_atom_ids,
                "missing_atom_ids": [],
                "unresolved_inventory_ids": [],
                "missing_inventory_categories": [],
            },
            "aggregate_physical_properties": {
                "mass_kg": round(total_mass, 9),
                "center_of_mass_assembly_frame_m": _round_vector(aggregate_com),
                "inertia_about_com_assembly_frame_kg_m2": _round_matrix(aggregate_inertia),
            },
            "selected_component_results": component_results,
            "rejected_measurements": [],
            "rejected_evidence": [],
            "unresolved_evidence": [],
            "blocking_reasons": [],
            "cad_prior_summary": {
                "prior_count": len(payload["cad_priors"]),
                "source_mass_total_kg": round(
                    sum(float(entry["source_mass_kg"]) for entry in payload["cad_priors"]),
                    9,
                ),
                "origin": "CAD",
            },
            "physical_qualification_authority": False,
            "training_or_promotion_authority": False,
        }
    )


def verify_measured_mass_intake(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    structural_diff_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
) -> None:
    if payload.get("schema_version") != MEASURED_MASS_INTAKE_SCHEMA_VERSION:
        raise ValueError("Unsupported measured mass intake schema")
    _verify_identity(payload, label="Measured mass intake")
    if payload.get("status") == SYNTHETIC_TEST_ONLY_STATUS:
        _verify_synthetic_measured_mass_intake(
            payload,
            repo_root=repo_root,
            dependency_lock_path=dependency_lock_path,
            twin_profile_path=twin_profile_path,
            structural_diff_path=structural_diff_path,
        )
        return
    if payload.get("status") != MEASURED_INTAKE_STATUS:
        raise ValueError("Measured mass intake status must remain awaiting_measurements")
    if payload.get("measurements") != []:
        raise ValueError("Awaiting-measurements intake must not carry measurements")
    assembly = payload.get("assembly")
    if not isinstance(assembly, dict):
        raise ValueError("Measured mass intake assembly metadata is missing")
    if assembly.get("assembly_id") != CURRENT_ASSEMBLY_ID:
        raise ValueError("Measured mass intake assembly_id drifted")
    if assembly.get("assembly_frame_id") != CURRENT_ASSEMBLY_FRAME_ID:
        raise ValueError("Measured mass intake assembly frame drifted")

    dependency_lock = _dependency_lock_ref(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    twin_profile = _twin_profile_ref(
        repo_root=repo_root,
        twin_profile_path=twin_profile_path,
        dependency_lock_path=dependency_lock_path,
    )
    structural_diff = _structural_diff_ref(
        repo_root=repo_root,
        structural_diff_path=structural_diff_path,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
    )
    _verify_ref(payload.get("dependency_lock_ref"), dependency_lock["ref"], label="Dependency lock")
    _verify_ref(payload.get("twin_profile_ref"), twin_profile["ref"], label="Twin profile")
    _verify_ref(payload.get("structural_diff_ref"), structural_diff["ref"], label="Structural diff")

    components = payload.get("components")
    coverage_atoms = payload.get("coverage_atoms")
    cad_priors = payload.get("cad_priors")
    unresolved_inventory = payload.get("unresolved_inventory")
    if not isinstance(components, list) or not components:
        raise ValueError("Measured mass intake components are required")
    if not isinstance(coverage_atoms, list) or not coverage_atoms:
        raise ValueError("Measured mass intake coverage atoms are required")
    if not isinstance(cad_priors, list) or not cad_priors:
        raise ValueError("Measured mass intake CAD priors are required")
    if not isinstance(unresolved_inventory, list) or not unresolved_inventory:
        raise ValueError("Measured mass intake unresolved inventory is required")

    component_ids = {component["component_id"] for component in components}
    if len(component_ids) != len(components):
        raise ValueError("Duplicate measured mass intake component_id")
    coverage_atom_ids: set[str] = set()
    for atom in coverage_atoms:
        atom_id = str(atom.get("atom_id") or "")
        if not atom_id:
            raise ValueError("Measured mass intake atom_id is required")
        if atom_id in coverage_atom_ids:
            raise ValueError(f"Duplicate measured mass intake atom_id: {atom_id}")
        coverage_atom_ids.add(atom_id)
        if atom.get("assembly_id") != CURRENT_ASSEMBLY_ID:
            raise ValueError(f"Measured mass intake atom assembly drifted: {atom_id}")
        if atom.get("assembly_frame_id") != CURRENT_ASSEMBLY_FRAME_ID:
            raise ValueError(f"Measured mass intake atom frame drifted: {atom_id}")
        if atom.get("component_id") not in component_ids:
            raise ValueError(f"Measured mass intake atom references unknown component: {atom_id}")
        if atom.get("origin_namespace") != "unmeasured_required_coverage":
            raise ValueError(f"Measured mass intake atom origin namespace drifted: {atom_id}")

    for component in components:
        component_id = str(component.get("component_id") or "")
        if not component_id:
            raise ValueError("Measured mass intake component_id is required")
        atom_ids = component.get("coverage_atom_ids")
        if not isinstance(atom_ids, list) or not atom_ids:
            raise ValueError(f"Measured mass intake component coverage is missing: {component_id}")
        for atom_id in atom_ids:
            if atom_id not in coverage_atom_ids:
                raise ValueError(f"Measured mass intake component references unknown atom: {component_id}")

    cad_prior_ids: set[str] = set()
    for prior in cad_priors:
        prior_id = str(prior.get("prior_id") or "")
        if not prior_id:
            raise ValueError("Measured mass intake CAD prior_id is required")
        if prior_id in cad_prior_ids:
            raise ValueError(f"Duplicate measured mass intake CAD prior_id: {prior_id}")
        cad_prior_ids.add(prior_id)
        if prior.get("origin") != "CAD":
            raise ValueError(f"Measured mass intake CAD prior origin drifted: {prior_id}")
        if prior.get("component_id") not in component_ids:
            raise ValueError(f"Measured mass intake CAD prior references unknown component: {prior_id}")
        if prior.get("atom_id") not in coverage_atom_ids:
            raise ValueError(f"Measured mass intake CAD prior references unknown atom: {prior_id}")
        if float(prior.get("source_mass_kg", 0.0)) <= 0.0:
            raise ValueError(f"Measured mass intake CAD prior mass must be positive: {prior_id}")

    missing_inventory_categories = payload.get("missing_inventory_categories")
    if not isinstance(missing_inventory_categories, list) or not missing_inventory_categories:
        raise ValueError("Measured mass intake missing inventory categories are required")
    if {entry["category_id"] for entry in unresolved_inventory} != set(missing_inventory_categories):
        raise ValueError("Measured mass intake unresolved inventory categories drifted")

    expected = build_measured_mass_intake(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
        structural_diff_path=structural_diff_path,
    )
    if payload != expected:
        raise ValueError("Measured mass intake drifted from deterministic repo rebuild")


def verify_assembly_inertials(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    intake_path: Path = DEFAULT_MEASURED_MASS_INTAKE_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    structural_diff_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
) -> None:
    if payload.get("schema_version") != ASSEMBLY_INERTIALS_SCHEMA_VERSION:
        raise ValueError("Unsupported assembly inertials schema")
    _verify_identity(payload, label="Assembly inertials")
    intake = _measured_mass_intake_ref(
        repo_root=repo_root,
        intake_path=intake_path,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
        structural_diff_path=structural_diff_path,
    )
    _verify_ref(payload.get("dependency_lock_ref"), intake["payload"]["dependency_lock_ref"], label="Dependency lock")
    _verify_ref(payload.get("twin_profile_ref"), intake["payload"]["twin_profile_ref"], label="Twin profile")
    _verify_ref(payload.get("structural_diff_ref"), intake["payload"]["structural_diff_ref"], label="Structural diff")
    if intake["payload"].get("status") == SYNTHETIC_TEST_ONLY_STATUS:
        _verify_ref(
            payload.get("intake_ref"),
            _synthetic_intake_semantic_ref(intake["payload"]),
            label="Measured mass intake",
        )
    else:
        _verify_ref(payload.get("intake_ref"), intake["ref"], label="Measured mass intake")
    if intake["payload"].get("status") != SYNTHETIC_TEST_ONLY_STATUS:
        if payload.get("status") != BLOCKED_ASSEMBLY_STATUS:
            raise ValueError("Assembly inertials status must remain blocked_missing_measurements")
        if payload.get("physical_qualification_authority") is not False:
            raise ValueError("Blocked assembly inertials must not grant physical qualification authority")
        if payload.get("training_or_promotion_authority") is not False:
            raise ValueError("Blocked assembly inertials must not grant training or promotion authority")
        aggregate = payload.get("aggregate_physical_properties") or {}
        if aggregate.get("mass_kg") is not None:
            raise ValueError("Blocked assembly inertials mass_kg must remain null")
        if aggregate.get("center_of_mass_assembly_frame_m") is not None:
            raise ValueError("Blocked assembly inertials center of mass must remain null")
        if aggregate.get("inertia_about_com_assembly_frame_kg_m2") is not None:
            raise ValueError("Blocked assembly inertials inertia must remain null")

    expected = build_assembly_inertials(
        repo_root=repo_root,
        intake_path=intake_path,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
        structural_diff_path=structural_diff_path,
    )
    if payload != expected:
        raise ValueError("Assembly inertials artifact drifted from repo state")


def write_measured_mass_intake(
    *,
    repo_root: Path,
    output_path: Path = DEFAULT_MEASURED_MASS_INTAKE_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    structural_diff_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
) -> dict[str, Any]:
    payload = build_measured_mass_intake(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
        structural_diff_path=structural_diff_path,
    )
    _write_json(_resolve(repo_root=repo_root, path=output_path), payload)
    return payload


def write_assembly_inertials(
    *,
    repo_root: Path,
    intake_path: Path = DEFAULT_MEASURED_MASS_INTAKE_PATH,
    output_path: Path = DEFAULT_ASSEMBLY_INERTIALS_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    structural_diff_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
) -> dict[str, Any]:
    payload = build_assembly_inertials(
        repo_root=repo_root,
        intake_path=intake_path,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
        structural_diff_path=structural_diff_path,
    )
    intake_payload = _read_json(_resolve(repo_root=repo_root, path=intake_path))
    if intake_payload.get("status") == SYNTHETIC_TEST_ONLY_STATUS:
        _refuse_real_artifact_destination(repo_root=repo_root, output_path=output_path)
    _write_json(_resolve(repo_root=repo_root, path=output_path), payload)
    return payload


def require_ready_or_raise(payload: dict[str, Any]) -> None:
    if payload.get("status") != "ready":
        raise ValueError(
            "Measured inertial compilation is not ready; current status is "
            f"{payload.get('status')!r}"
        )


def _build_component_inventory(
    geometry_priors: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    components: list[dict[str, Any]] = []
    coverage_atoms: list[dict[str, Any]] = []
    for prior in geometry_priors:
        component_id = prior["component_id"]
        atom_id = prior["atom_id"]
        body_name = prior["body_name"]
        components.append(
            {
                "component_id": component_id,
                "assembly_id": CURRENT_ASSEMBLY_ID,
                "canonical_body_id": body_name,
                "canonical_frame_id": f"{body_name}{BODY_FRAME_SUFFIX}",
                "category_id": "printed_link_structures",
                "installed_state": "present_in_runtime_model_unmeasured",
                "required_for_ready": True,
                "coverage_atom_ids": [atom_id],
                "evidence": [
                    _evidence("runtime_mjcf_body", body_name),
                    _evidence("cad_prior_id", prior["prior_id"]),
                ],
            }
        )
        coverage_atoms.append(
            {
                "atom_id": atom_id,
                "component_id": component_id,
                "assembly_id": CURRENT_ASSEMBLY_ID,
                "assembly_frame_id": CURRENT_ASSEMBLY_FRAME_ID,
                "canonical_body_id": body_name,
                "canonical_frame_id": f"{body_name}{BODY_FRAME_SUFFIX}",
                "category_id": "printed_link_structures",
                "required_for_ready": True,
                "installed_state": "present_in_runtime_model_unmeasured",
                "origin_namespace": "unmeasured_required_coverage",
                "evidence": [
                    _evidence("runtime_mjcf_body", body_name),
                ],
            }
        )

    for category_id, label, _ in KNOWN_MISSING_CATEGORY_SPECS:
        component_id = f"{category_id}_bundle"
        atom_id = f"{category_id}_bundle_mass"
        components.append(
            {
                "component_id": component_id,
                "assembly_id": CURRENT_ASSEMBLY_ID,
                "canonical_body_id": None,
                "canonical_frame_id": CURRENT_ASSEMBLY_FRAME_ID,
                "category_id": category_id,
                "installed_state": "present_or_possible_but_unresolved",
                "required_for_ready": True,
                "coverage_atom_ids": [atom_id],
                "evidence": [
                    _evidence("inventory_gap", label),
                ],
            }
        )
        coverage_atoms.append(
            {
                "atom_id": atom_id,
                "component_id": component_id,
                "assembly_id": CURRENT_ASSEMBLY_ID,
                "assembly_frame_id": CURRENT_ASSEMBLY_FRAME_ID,
                "canonical_body_id": None,
                "canonical_frame_id": CURRENT_ASSEMBLY_FRAME_ID,
                "category_id": category_id,
                "required_for_ready": True,
                "installed_state": "present_or_possible_but_unresolved",
                "origin_namespace": "unmeasured_required_coverage",
                "evidence": [
                    _evidence("inventory_gap", label),
                ],
            }
        )
    return components, coverage_atoms


def _extract_geometry_priors(*, repo_root: Path, runtime_source: dict[str, Any]) -> list[dict[str, Any]]:
    source_path = repo_root / runtime_source["path"]
    root = ET.parse(source_path).getroot()
    worldbody = root.find("worldbody")
    if worldbody is None:
        raise ValueError("Runtime MJCF is missing worldbody")
    body_states = _collect_body_states(worldbody)
    priors: list[dict[str, Any]] = []
    for body_name in sorted(body_states):
        body_element, world_rotation, world_translation = body_states[body_name]
        inertial = body_element.find("inertial")
        if inertial is None:
            continue
        com_local = _parse_vector(inertial.attrib.get("pos"), expected=3, default=(0.0, 0.0, 0.0))
        inertia_local = _parse_fullinertia(inertial.attrib.get("fullinertia"))
        priors.append(
            {
                "prior_id": f"runtime_mjcf_{body_name}_cad_prior",
                "component_id": f"{body_name}_structure",
                "atom_id": f"{body_name}_structure_mass",
                "body_name": body_name,
                "source_path": runtime_source["path"],
                "source_path_sha256": runtime_source["sha256"],
                "source_path_size_bytes": runtime_source["size_bytes"],
                "source_mass_kg": _parse_scalar(inertial.attrib["mass"]),
                "source_center_of_mass_body_frame_m": com_local,
                "source_inertia_about_com_body_frame_kg_m2": inertia_local,
                "body_frame_to_assembly": {
                    "translation_m": world_translation,
                    "rotation_matrix": world_rotation,
                },
                "units": {
                    "mass": "kilogram",
                    "length": "meter",
                    "inertia": "kilogram_meter_squared",
                },
                "origin": "CAD",
                "assumptions": [
                    "Derived from the active runtime MJCF inertial element.",
                    "This prior is not a physical measurement and cannot satisfy measured coverage.",
                ],
            }
        )
    if not priors:
        raise ValueError("Runtime MJCF did not expose any inertial priors")
    return priors


def _collect_body_states(
    parent: ET.Element,
    *,
    parent_rotation: list[list[float]] | None = None,
    parent_translation: list[float] | None = None,
) -> dict[str, tuple[ET.Element, list[list[float]], list[float]]]:
    parent_rotation = parent_rotation or _identity_matrix()
    parent_translation = parent_translation or [0.0, 0.0, 0.0]
    states: dict[str, tuple[ET.Element, list[list[float]], list[float]]] = {}
    for body in parent.findall("body"):
        body_name = body.attrib.get("name")
        if not body_name:
            raise ValueError("Runtime MJCF body name is required")
        local_translation = _parse_vector(body.attrib.get("pos"), expected=3, default=(0.0, 0.0, 0.0))
        local_quaternion = _parse_vector(body.attrib.get("quat"), expected=4, default=(1.0, 0.0, 0.0, 0.0))
        local_rotation = _quaternion_to_matrix(local_quaternion)
        world_rotation = _matrix_multiply(parent_rotation, local_rotation)
        world_translation = _vector_add(
            parent_translation,
            _matrix_vector_multiply(parent_rotation, local_translation),
        )
        states[body_name] = (body, world_rotation, world_translation)
        states.update(
            _collect_body_states(
                body,
                parent_rotation=world_rotation,
                parent_translation=world_translation,
            )
        )
    return states


def _quaternion_to_matrix(quaternion: list[float]) -> list[list[float]]:
    w, x, y, z = quaternion
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if norm <= 0.0:
        raise ValueError("Quaternion norm must be positive")
    w /= norm
    x /= norm
    y /= norm
    z /= norm
    return [
        [
            round(1.0 - 2.0 * (y * y + z * z), 9),
            round(2.0 * (x * y - z * w), 9),
            round(2.0 * (x * z + y * w), 9),
        ],
        [
            round(2.0 * (x * y + z * w), 9),
            round(1.0 - 2.0 * (x * x + z * z), 9),
            round(2.0 * (y * z - x * w), 9),
        ],
        [
            round(2.0 * (x * z - y * w), 9),
            round(2.0 * (y * z + x * w), 9),
            round(1.0 - 2.0 * (x * x + y * y), 9),
        ],
    ]


def _identity_matrix() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def _matrix_multiply(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    result: list[list[float]] = []
    for row in a:
        result_row: list[float] = []
        for column_index in range(len(b[0])):
            value = sum(row[item_index] * b[item_index][column_index] for item_index in range(len(b)))
            result_row.append(round(value, 9))
        result.append(result_row)
    return result


def _matrix_vector_multiply(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [
        round(sum(row[index] * vector[index] for index in range(len(vector))), 9)
        for row in matrix
    ]


def _vector_add(left: list[float], right: list[float]) -> list[float]:
    return [round(left[index] + right[index], 9) for index in range(len(left))]


def _parse_fullinertia(value: str | None) -> list[list[float]]:
    parts = _parse_vector(value, expected=6)
    return [
        [parts[0], parts[3], parts[4]],
        [parts[3], parts[1], parts[5]],
        [parts[4], parts[5], parts[2]],
    ]


def _parse_vector(
    value: str | None,
    *,
    expected: int,
    default: tuple[float, ...] | None = None,
) -> list[float]:
    if value is None:
        if default is None:
            raise ValueError("Vector value is required")
        return [round(float(item), 9) for item in default]
    parts = [round(float(item), 9) for item in value.split()]
    if len(parts) != expected:
        raise ValueError(f"Expected {expected} values but found {len(parts)}")
    return parts


def _parse_scalar(value: str) -> float:
    return round(float(value), 9)


def _verify_synthetic_measured_mass_intake(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    dependency_lock_path: Path,
    twin_profile_path: Path,
    structural_diff_path: Path,
) -> None:
    dependency_lock = _dependency_lock_ref(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    twin_profile = _twin_profile_ref(
        repo_root=repo_root,
        twin_profile_path=twin_profile_path,
        dependency_lock_path=dependency_lock_path,
    )
    structural_diff = _structural_diff_ref(
        repo_root=repo_root,
        structural_diff_path=structural_diff_path,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
    )
    _verify_ref(payload.get("dependency_lock_ref"), dependency_lock["ref"], label="Dependency lock")
    _verify_ref(payload.get("twin_profile_ref"), twin_profile["ref"], label="Twin profile")
    _verify_ref(payload.get("structural_diff_ref"), structural_diff["ref"], label="Structural diff")
    if payload.get("status") != SYNTHETIC_TEST_ONLY_STATUS:
        raise ValueError("Synthetic intake status drifted")
    if payload.get("intake_name") != "synthetic_complete":
        raise ValueError("Synthetic intake name drifted")
    assembly = payload.get("assembly")
    if not isinstance(assembly, dict):
        raise ValueError("Synthetic intake assembly metadata is missing")
    components = payload.get("components")
    coverage_atoms = payload.get("coverage_atoms")
    cad_priors = payload.get("cad_priors")
    measurements = payload.get("measurements")
    if not isinstance(components, list) or len(components) < 2:
        raise ValueError("Synthetic intake components are required")
    if not isinstance(coverage_atoms, list) or len(coverage_atoms) < 2:
        raise ValueError("Synthetic intake coverage atoms are required")
    if not isinstance(cad_priors, list) or len(cad_priors) < 2:
        raise ValueError("Synthetic intake CAD priors are required")
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("Synthetic intake measurements are required")
    component_ids = {str(component["component_id"]) for component in components}
    atom_ids = {str(atom["atom_id"]) for atom in coverage_atoms}
    prior_ids = {str(prior["prior_id"]) for prior in cad_priors}
    if len(component_ids) != len(components):
        raise ValueError("Synthetic intake component IDs must be unique")
    if len(atom_ids) != len(coverage_atoms):
        raise ValueError("Synthetic intake atom IDs must be unique")
    if len(prior_ids) != len(cad_priors):
        raise ValueError("Synthetic intake prior IDs must be unique")
    has_nonzero_translation = False
    has_non_identity_rotation = False
    for prior in cad_priors:
        if prior.get("origin") != "CAD":
            raise ValueError("Synthetic intake priors must remain CAD-origin")
        if str(prior["component_id"]) not in component_ids or str(prior["atom_id"]) not in atom_ids:
            raise ValueError("Synthetic prior linkage drifted")
        translation = _validate_vector(
            prior["body_frame_to_assembly"]["translation_m"],
            expected=3,
            label=f"{prior['prior_id']} translation",
        )
        rotation = _validate_rotation_matrix(
            prior["body_frame_to_assembly"]["rotation_matrix"],
            label=f"{prior['prior_id']} rotation",
        )
        _validate_vector(
            prior["source_center_of_mass_body_frame_m"],
            expected=3,
            label=f"{prior['prior_id']} source COM",
        )
        _validate_inertia_matrix(
            prior["source_inertia_about_com_body_frame_kg_m2"],
            label=f"{prior['prior_id']} source inertia",
        )
        if float(prior["source_mass_kg"]) <= 0.0:
            raise ValueError("Synthetic prior source mass must be positive")
        has_nonzero_translation = has_nonzero_translation or any(abs(value) > 0.0 for value in translation)
        has_non_identity_rotation = has_non_identity_rotation or rotation != _identity_matrix()
    if not has_nonzero_translation:
        raise ValueError("Synthetic intake must include a nonzero translation")
    if not has_non_identity_rotation:
        raise ValueError("Synthetic intake must include a non-identity rotation")
    for measurement in measurements:
        if measurement.get("origin") != "measured":
            raise ValueError("Synthetic measurements must remain measured-origin")
        if str(measurement["component_id"]) not in component_ids:
            raise ValueError("Synthetic measurement component linkage drifted")
        if str(measurement["source_prior_id"]) not in prior_ids:
            raise ValueError("Synthetic measurement prior linkage drifted")
        if float(measurement["measured_mass_kg"]) <= 0.0:
            raise ValueError("Synthetic measurement mass must be positive")
        covered_atom_ids = measurement.get("covered_atom_ids")
        if not isinstance(covered_atom_ids, list) or len(covered_atom_ids) != 1:
            raise ValueError("Synthetic measurements must cover exactly one atom")
        if str(covered_atom_ids[0]) not in atom_ids:
            raise ValueError("Synthetic measurement atom linkage drifted")
        uncertainty = measurement.get("uncertainty")
        if not isinstance(uncertainty, dict) or float(uncertainty.get("mass_kg", -1.0)) < 0.0:
            raise ValueError("Synthetic measurement uncertainty is required")
        provenance = measurement.get("provenance")
        if not isinstance(provenance, dict):
            raise ValueError("Synthetic measurement provenance is required")
        for field in ("method", "device_id", "calibration_id"):
            if not str(provenance.get(field) or ""):
                raise ValueError(f"Synthetic measurement provenance field is required: {field}")
        evidence = measurement.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("Synthetic measurement evidence is required")


def _refuse_real_artifact_destination(*, repo_root: Path, output_path: Path) -> None:
    resolved_output = _resolve(repo_root=repo_root, path=output_path)
    forbidden = {
        _resolve(repo_root=repo_root, path=DEFAULT_MEASURED_MASS_INTAKE_PATH).resolve(),
        _resolve(repo_root=repo_root, path=DEFAULT_ASSEMBLY_INERTIALS_PATH).resolve(),
    }
    if resolved_output.resolve() in forbidden:
        raise ValueError("Synthetic test-only compilation cannot write to checked-in real artifact destinations")


def _synthetic_intake_semantic_ref(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": f"synthetic_test_only://{payload['intake_name']}",
        "schema_version": str(payload["schema_version"]),
        "identity_sha256": _synthetic_intake_semantic_identity(payload),
    }


def _synthetic_intake_semantic_identity(payload: dict[str, Any]) -> str:
    normalized = {
        "schema_version": payload["schema_version"],
        "status": payload["status"],
        "intake_name": payload["intake_name"],
        "fixture_scope": payload.get("fixture_scope"),
        "assembly": payload["assembly"],
        "dependency_lock_ref": payload["dependency_lock_ref"],
        "twin_profile_ref": payload["twin_profile_ref"],
        "structural_diff_ref": payload["structural_diff_ref"],
        "components": sorted(payload["components"], key=lambda item: str(item["component_id"])),
        "coverage_atoms": sorted(payload["coverage_atoms"], key=lambda item: str(item["atom_id"])),
        "cad_priors": sorted(payload["cad_priors"], key=lambda item: str(item["prior_id"])),
        "measurements": sorted(payload["measurements"], key=lambda item: str(item["measurement_id"])),
    }
    return hashlib.sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _validate_vector(values: Any, *, expected: int, label: str) -> list[float]:
    if not isinstance(values, list) or len(values) != expected:
        raise ValueError(f"{label} must contain {expected} finite values")
    output = [float(value) for value in values]
    if not all(math.isfinite(value) for value in output):
        raise ValueError(f"{label} must be finite")
    return output


def _validate_rotation_matrix(values: Any, *, label: str) -> list[list[float]]:
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{label} must be a 3x3 matrix")
    matrix = [_validate_vector(row, expected=3, label=label) for row in values]
    transpose = _transpose(matrix)
    product = _matrix_multiply(transpose, matrix)
    if _round_matrix(product) != _identity_matrix():
        raise ValueError(f"{label} must be orthonormal")
    determinant = (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )
    if round(determinant, 9) != 1.0:
        raise ValueError(f"{label} must be a proper rotation")
    return _round_matrix(matrix)


def _validate_inertia_matrix(values: Any, *, label: str) -> list[list[float]]:
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{label} must be a 3x3 matrix")
    matrix = [_validate_vector(row, expected=3, label=label) for row in values]
    rounded = _round_matrix(matrix)
    if rounded != _round_matrix(_transpose(rounded)):
        raise ValueError(f"{label} must be symmetric")
    diagonal = [rounded[index][index] for index in range(3)]
    if any(value < 0.0 for value in diagonal):
        raise ValueError(f"{label} diagonal must be nonnegative")
    if diagonal[0] > diagonal[1] + diagonal[2] or diagonal[1] > diagonal[0] + diagonal[2] or diagonal[2] > diagonal[0] + diagonal[1]:
        raise ValueError(f"{label} violates triangle inequalities")
    return rounded


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [[matrix[row][column] for row in range(len(matrix))] for column in range(len(matrix[0]))]


def _matrix_scale(matrix: list[list[float]], scalar: float) -> list[list[float]]:
    return [[round(value * scalar, 9) for value in row] for row in matrix]


def _matrix_add(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [round(left[row][column] + right[row][column], 9) for column in range(len(left[row]))]
        for row in range(len(left))
    ]


def _rotate_inertia(rotation: list[list[float]], inertia: list[list[float]]) -> list[list[float]]:
    return _round_matrix(_matrix_multiply(_matrix_multiply(rotation, inertia), _transpose(rotation)))


def _parallel_axis_term(mass: float, displacement: list[float]) -> list[list[float]]:
    dx, dy, dz = displacement
    norm_sq = dx * dx + dy * dy + dz * dz
    outer = [
        [dx * dx, dx * dy, dx * dz],
        [dy * dx, dy * dy, dy * dz],
        [dz * dx, dz * dy, dz * dz],
    ]
    return _round_matrix(
        [
            [mass * ((norm_sq if row == column else 0.0) - outer[row][column]) for column in range(3)]
            for row in range(3)
        ]
    )


def _zero_matrix() -> list[list[float]]:
    return [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]


def _round_vector(values: list[float]) -> list[float]:
    return [round(value, 9) for value in values]


def _round_matrix(values: list[list[float]]) -> list[list[float]]:
    return [[round(value, 9) for value in row] for row in values]


def _dependency_lock_ref(*, repo_root: Path, dependency_lock_path: Path) -> dict[str, Any]:
    payload = _read_json(_resolve(repo_root=repo_root, path=dependency_lock_path))
    verify_robotics_dependency_lock(payload, repo_root=repo_root)
    return {"payload": payload, "ref": _artifact_ref(path=dependency_lock_path, payload=payload, repo_root=repo_root)}


def _twin_profile_ref(
    *,
    repo_root: Path,
    twin_profile_path: Path,
    dependency_lock_path: Path,
) -> dict[str, Any]:
    payload = _read_json(_resolve(repo_root=repo_root, path=twin_profile_path))
    verify_twin_profile(payload, repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    return {"payload": payload, "ref": _artifact_ref(path=twin_profile_path, payload=payload, repo_root=repo_root)}


def _structural_diff_ref(
    *,
    repo_root: Path,
    structural_diff_path: Path,
    dependency_lock_path: Path,
    twin_profile_path: Path,
) -> dict[str, Any]:
    payload = _read_json(_resolve(repo_root=repo_root, path=structural_diff_path))
    verify_structural_twin_diff(
        payload,
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
    )
    return {
        "payload": payload,
        "ref": _artifact_ref(path=structural_diff_path, payload=payload, repo_root=repo_root),
    }


def _measured_mass_intake_ref(
    *,
    repo_root: Path,
    intake_path: Path,
    dependency_lock_path: Path,
    twin_profile_path: Path,
    structural_diff_path: Path,
) -> dict[str, Any]:
    payload = _read_json(_resolve(repo_root=repo_root, path=intake_path))
    verify_measured_mass_intake(
        payload,
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
        structural_diff_path=structural_diff_path,
    )
    return {"payload": payload, "ref": _artifact_ref(path=intake_path, payload=payload, repo_root=repo_root)}


def _artifact_ref(*, path: Path, payload: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    identity = str(payload.get("identity_sha256") or "")
    if not identity:
        raise ValueError(f"Artifact is missing identity_sha256: {path}")
    return {
        "path": str(path),
        "schema_version": str(payload["schema_version"]),
        "identity_sha256": identity,
        "file_sha256": _sha256(_resolve(repo_root=repo_root, path=path)),
    }


def _verify_ref(payload: dict[str, Any] | None, expected: dict[str, Any], *, label: str) -> None:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} linkage is missing")
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            raise ValueError(f"{label} linkage drifted for {key}")


def _sign(payload: dict[str, Any]) -> dict[str, Any]:
    signed = dict(payload)
    unsigned = {key: value for key, value in signed.items() if key != "identity_sha256"}
    signed["identity_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return signed


def _verify_identity(payload: dict[str, Any], *, label: str) -> None:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    actual = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if payload.get("identity_sha256") != actual:
        raise ValueError(f"{label} identity hash is invalid")


def _evidence(kind: str, ref: str) -> dict[str, str]:
    return {"kind": kind, "ref": ref}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _resolve(*, repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

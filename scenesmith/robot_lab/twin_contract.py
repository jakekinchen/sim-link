"""Twin contract schemas for the SceneSmith PI0.5 hardware twin workflow."""

from __future__ import annotations

import hashlib
import json

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.so101_coordinates import coordinate_contract


TWIN_PROFILE_SCHEMA_VERSION = "scenesmith.twin_profile.v1"
TWIN_QUALIFICATION_SPEC_SCHEMA_VERSION = "scenesmith.twin_qualification_spec.v1"
TWIN_QUALIFICATION_REPORT_SCHEMA_VERSION = "scenesmith.twin_qualification_report.v1"
DEFAULT_DEPENDENCY_LOCK_PATH = Path("configurations/robot_lab/pi05_robotics_dependency_lock.json")
DEFAULT_TWIN_PROFILE_PATH = Path("configurations/robot_lab/pi05_twin_profile.simulation_only.json")
DEFAULT_TWIN_QUALIFICATION_SPEC_PATH = Path(
    "configurations/robot_lab/pi05_twin_qualification_spec.simulation_only.json"
)
DEFAULT_TWIN_QUALIFICATION_REPORT_PATH = Path(
    "configurations/robot_lab/pi05_twin_qualification_report.simulation_only.json"
)

PROOF_STATES = {
    "structural_baseline_only",
    "simulation_only",
    "physical_qualified",
}
PARAMETER_ORIGINS = {"read", "measured", "CAD", "fitted"}
PARAMETER_UNITS = {
    "boolean",
    "celsius",
    "fraction",
    "hertz",
    "identifier",
    "kilogram",
    "meter",
    "millisecond",
    "newton",
    "radian",
    "ratio",
    "second",
    "unitless",
    "volt",
}
METRIC_STATUSES = {"pass", "fail", "not_run"}
METRIC_EVIDENCE_MODES = {"simulation_trace", "physical_run", "documentation_only", "not_run"}
SECTION_NAMES = (
    "structural_model_identity",
    "coordinate_gripper_contract",
    "kinematics",
    "inertials",
    "actuators",
    "backlash_friction_compliance",
    "cameras_timing",
    "gripper_contact",
    "environment_object_profiles",
)
QUALIFICATION_STATE_BY_PROOF_STATE = {
    "structural_baseline_only": "unqualified",
    "simulation_only": "simulation_only_unqualified",
    "physical_qualified": "physical_qualified",
}


def build_twin_profile(
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> dict[str, Any]:
    dependency_lock = _dependency_lock_ref(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    runtime_contract = dependency_lock["payload"]["runtime_contract"]
    coordinates = coordinate_contract()
    coordinate_identity = hashlib.sha256(
        json.dumps(coordinates, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return _sign(
        {
            "schema_version": TWIN_PROFILE_SCHEMA_VERSION,
            "profile_name": "pi05_so101_simulation_only",
            "proof_state": "simulation_only",
            "qualification_state": "simulation_only_unqualified",
            "dependency_lock_ref": dependency_lock["ref"],
            "structural_lineage": {
                "runtime_robot_model": runtime_contract["robot_model"],
                "runtime_joint_names": runtime_contract["joint_names"],
                "source_mjcf_sha256": runtime_contract["source_mjcf"]["sha256"],
                "source_urdf_sha256": runtime_contract["source_urdf"]["sha256"],
            },
            "sections": {
                "structural_model_identity": {
                    "parameters": [
                        _parameter(
                            parameter_id="runtime_robot_model",
                            value=runtime_contract["robot_model"],
                            units="identifier",
                            origin="read",
                            evidence=[
                                _evidence("dependency_lock", dependency_lock["ref"]["path"]),
                            ],
                        ),
                        _parameter(
                            parameter_id="runtime_joint_count",
                            value=len(runtime_contract["joint_names"]),
                            units="unitless",
                            origin="read",
                            evidence=[
                                _evidence("dependency_lock", dependency_lock["ref"]["path"]),
                            ],
                        ),
                    ],
                },
                "coordinate_gripper_contract": {
                    "parameters": [
                        _parameter(
                            parameter_id="coordinate_contract_schema_version",
                            value=coordinates["schema_version"],
                            units="identifier",
                            origin="read",
                            evidence=[
                                _evidence("source", "scenesmith/robot_lab/so101_coordinates.py"),
                                _evidence("contract_identity_sha256", coordinate_identity),
                            ],
                        ),
                        _parameter(
                            parameter_id="policy_action_representation",
                            value="absolute_joint_degrees_plus_gripper_percent",
                            units="identifier",
                            origin="read",
                            evidence=[
                                _evidence("source", "scenesmith/robot_lab/pi05_dataset_contract.py"),
                            ],
                        ),
                        _parameter(
                            parameter_id="simulator_control_representation",
                            value="absolute_joint_radians_plus_gripper_radians",
                            units="identifier",
                            origin="read",
                            evidence=[
                                _evidence("source", "scenesmith/robot_lab/so101_coordinates.py"),
                            ],
                        ),
                        _parameter(
                            parameter_id="gripper_joint_name",
                            value="gripper",
                            units="identifier",
                            origin="read",
                            evidence=[_evidence("spec", "scenesmith/robot_lab/spec.py")],
                        ),
                    ],
                },
                "kinematics": {
                    "parameters": [
                        _parameter(
                            parameter_id="joint_home_pose_nominal",
                            value=[0.0, -0.55, 1.05, -0.48, 0.0, 0.35],
                            units="radian",
                            origin="read",
                            uncertainty={"lower": 0.0, "upper": 0.0},
                            evidence=[_evidence("spec", "scenesmith/robot_lab/spec.py")],
                        ),
                    ],
                },
                "inertials": {
                    "parameters": [
                        _parameter(
                            parameter_id="full_arm_mass_kg",
                            value=None,
                            units="kilogram",
                            origin="CAD",
                            uncertainty={"state": "unknown"},
                            evidence=[_evidence("planned_slice", "T16.4 measured inertial intake pending")],
                        ),
                    ],
                },
                "actuators": {
                    "parameters": [
                        _parameter(
                            parameter_id="nominal_bus_voltage",
                            value=None,
                            units="volt",
                            origin="read",
                            uncertainty={"state": "unknown"},
                            evidence=[_evidence("planned_measurement", "T19.1 read-only servo census")],
                        ),
                    ],
                },
                "backlash_friction_compliance": {
                    "parameters": [
                        _parameter(
                            parameter_id="wrist_friction_model",
                            value=None,
                            units="ratio",
                            origin="fitted",
                            uncertainty={"state": "unknown"},
                            evidence=[_evidence("planned_slice", "T16.5 identification harness pending")],
                        ),
                    ],
                },
                "cameras_timing": {
                    "parameters": [
                        _parameter(
                            parameter_id="policy_camera_latency_ms",
                            value=None,
                            units="millisecond",
                            origin="measured",
                            uncertainty={"state": "unknown"},
                            evidence=[_evidence("planned_slice", "M19 held-out timing census pending")],
                        ),
                    ],
                },
                "gripper_contact": {
                    "parameters": [
                        _parameter(
                            parameter_id="cube_contact_patch_model",
                            value="simulation_default_contact_only",
                            units="identifier",
                            origin="CAD",
                            evidence=[_evidence("runtime_model", runtime_contract["source_mjcf"]["path"])],
                        ),
                    ],
                },
                "environment_object_profiles": {
                    "parameters": [
                        _parameter(
                            parameter_id="desk_sort_cube_mass_kg",
                            value=0.035,
                            units="kilogram",
                            origin="read",
                            evidence=[_evidence("spec", "scenesmith/robot_lab/spec.py")],
                        ),
                    ],
                },
            },
            "requalification_triggers": [
                "dependency_lock_identity_changed",
                "structural_diff_detected",
                "measured_mass_inputs_changed",
                "camera_or_timing_measurements_changed",
            ],
        }
    )


def build_twin_qualification_spec(
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = twin_profile or build_twin_profile(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
    )
    return _sign(
        {
            "schema_version": TWIN_QUALIFICATION_SPEC_SCHEMA_VERSION,
            "spec_name": "pi05_twin_qualification_spec_simulation_only",
            "authority_level": "simulation_only",
            "dependency_lock_ref": profile["dependency_lock_ref"],
            "profile_identity_sha256": profile["identity_sha256"],
            "held_out_metrics": [
                {
                    "metric_id": "sim_joint_limit_projection_error",
                    "description": "Held-out simulator replay stays within joint-space error budget.",
                    "tolerance": {"max_value": 0.05, "units": "radian"},
                    "required_evidence_modes": ["simulation_trace"],
                    "required_for_proof_state": ["simulation_only", "physical_qualified"],
                },
                {
                    "metric_id": "physical_gripper_contact_latency",
                    "description": "Held-out physical contact latency remains inside the simulated envelope.",
                    "tolerance": {"max_value": 35.0, "units": "millisecond"},
                    "required_evidence_modes": ["physical_run"],
                    "required_for_proof_state": ["physical_qualified"],
                },
            ],
            "required_evidence": [
                "dependency_lock_ref",
                "profile_identity_sha256",
                "held_out_metric_evidence",
            ],
        }
    )


def build_twin_qualification_report(
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile: dict[str, Any] | None = None,
    twin_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = twin_profile or build_twin_profile(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
    )
    spec = twin_spec or build_twin_qualification_spec(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile=profile,
    )
    return _sign(
        {
            "schema_version": TWIN_QUALIFICATION_REPORT_SCHEMA_VERSION,
            "report_name": "pi05_twin_qualification_report_simulation_only",
            "proof_state": "simulation_only",
            "qualification_state": "simulation_only_unqualified",
            "dependency_lock_ref": profile["dependency_lock_ref"],
            "profile_identity_sha256": profile["identity_sha256"],
            "spec_identity_sha256": spec["identity_sha256"],
            "metrics": [
                {
                    "metric_id": "sim_joint_limit_projection_error",
                    "status": "not_run",
                    "measured_value": None,
                    "units": "radian",
                    "evidence_mode": "not_run",
                    "evidence_refs": [],
                },
                {
                    "metric_id": "physical_gripper_contact_latency",
                    "status": "not_run",
                    "measured_value": None,
                    "units": "millisecond",
                    "evidence_mode": "not_run",
                    "evidence_refs": [],
                },
            ],
            "summary": (
                "Simulation-only structural twin artifact. Physical qualification has not run and "
                "must not be inferred from this report."
            ),
        }
    )


def build_twin_contract_examples(
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> dict[str, dict[str, Any]]:
    profile = build_twin_profile(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    spec = build_twin_qualification_spec(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile=profile,
    )
    report = build_twin_qualification_report(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile=profile,
        twin_spec=spec,
    )
    return {
        "profile": profile,
        "spec": spec,
        "report": report,
    }


def verify_twin_profile(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> None:
    if payload.get("schema_version") != TWIN_PROFILE_SCHEMA_VERSION:
        raise ValueError("Unsupported twin profile schema")
    _verify_identity_hash(payload, label="Twin profile")
    proof_state = str(payload["proof_state"])
    _verify_proof_state(proof_state)
    if payload.get("qualification_state") != QUALIFICATION_STATE_BY_PROOF_STATE[proof_state]:
        raise ValueError("Twin profile qualification state is inconsistent with its proof state")
    dependency_lock = _dependency_lock_ref(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    _verify_dependency_lock_ref(payload.get("dependency_lock_ref"), dependency_lock["ref"])
    sections = payload.get("sections") or {}
    for section_name in SECTION_NAMES:
        if section_name not in sections:
            raise ValueError(f"Missing twin profile section: {section_name}")
        section = sections[section_name]
        parameters = section.get("parameters")
        if not isinstance(parameters, list) or not parameters:
            raise ValueError(f"Twin profile section has no parameters: {section_name}")
        for parameter in parameters:
            _verify_parameter(parameter)
    triggers = payload.get("requalification_triggers")
    if not isinstance(triggers, list) or not triggers:
        raise ValueError("Twin profile must declare requalification triggers")


def verify_twin_qualification_spec(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile: dict[str, Any] | None = None,
) -> None:
    if payload.get("schema_version") != TWIN_QUALIFICATION_SPEC_SCHEMA_VERSION:
        raise ValueError("Unsupported twin qualification spec schema")
    _verify_identity_hash(payload, label="Twin qualification spec")
    authority_level = str(payload.get("authority_level") or "")
    if authority_level not in {"simulation_only", "physical_qualified"}:
        raise ValueError("Twin qualification spec authority level is invalid")
    dependency_lock = _dependency_lock_ref(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    _verify_dependency_lock_ref(payload.get("dependency_lock_ref"), dependency_lock["ref"])
    profile = twin_profile or build_twin_profile(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
    )
    if payload.get("profile_identity_sha256") != profile["identity_sha256"]:
        raise ValueError("Twin qualification spec profile identity does not match the twin profile")
    metrics = payload.get("held_out_metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("Twin qualification spec requires held-out metrics")
    seen_metric_ids: set[str] = set()
    for metric in metrics:
        metric_id = str(metric.get("metric_id") or "")
        if not metric_id:
            raise ValueError("Twin qualification spec metric_id is required")
        if metric_id in seen_metric_ids:
            raise ValueError(f"Duplicate twin qualification spec metric_id: {metric_id}")
        seen_metric_ids.add(metric_id)
        tolerance = metric.get("tolerance") or {}
        if "max_value" not in tolerance:
            raise ValueError(f"Metric tolerance max_value is required: {metric_id}")
        if tolerance.get("units") not in PARAMETER_UNITS:
            raise ValueError(f"Metric tolerance units are invalid: {metric_id}")
        required_modes = metric.get("required_evidence_modes")
        if not isinstance(required_modes, list) or not required_modes:
            raise ValueError(f"Metric required evidence modes are missing: {metric_id}")
        for mode in required_modes:
            if mode not in METRIC_EVIDENCE_MODES - {"not_run"}:
                raise ValueError(f"Metric required evidence mode is invalid: {metric_id}")
        required_states = metric.get("required_for_proof_state")
        if not isinstance(required_states, list) or not required_states:
            raise ValueError(f"Metric required proof states are missing: {metric_id}")
        for state in required_states:
            _verify_proof_state(state)


def verify_twin_qualification_report(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile: dict[str, Any] | None = None,
    twin_spec: dict[str, Any] | None = None,
) -> None:
    if payload.get("schema_version") != TWIN_QUALIFICATION_REPORT_SCHEMA_VERSION:
        raise ValueError("Unsupported twin qualification report schema")
    _verify_identity_hash(payload, label="Twin qualification report")
    proof_state = str(payload.get("proof_state") or "")
    _verify_proof_state(proof_state)
    if payload.get("qualification_state") != QUALIFICATION_STATE_BY_PROOF_STATE[proof_state]:
        raise ValueError("Twin qualification report state is inconsistent with its proof state")
    dependency_lock = _dependency_lock_ref(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    _verify_dependency_lock_ref(payload.get("dependency_lock_ref"), dependency_lock["ref"])
    profile = twin_profile or build_twin_profile(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
    )
    spec = twin_spec or build_twin_qualification_spec(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile=profile,
    )
    if proof_state == "physical_qualified":
        if profile.get("proof_state") != "physical_qualified":
            raise ValueError("Physical-qualified report requires a physical-qualified twin profile")
        if spec.get("authority_level") != "physical_qualified":
            raise ValueError("Physical-qualified report requires a physical qualification spec")
    if payload.get("profile_identity_sha256") != profile["identity_sha256"]:
        raise ValueError("Twin qualification report profile identity does not match the twin profile")
    if payload.get("spec_identity_sha256") != spec["identity_sha256"]:
        raise ValueError("Twin qualification report spec identity does not match the twin qualification spec")
    metric_index = {metric["metric_id"]: metric for metric in spec["held_out_metrics"]}
    report_metrics = payload.get("metrics")
    if not isinstance(report_metrics, list) or not report_metrics:
        raise ValueError("Twin qualification report requires metric results")
    seen_metric_ids: set[str] = set()
    for metric in report_metrics:
        metric_id = str(metric.get("metric_id") or "")
        if metric_id not in metric_index:
            raise ValueError(f"Twin qualification report metric is unknown: {metric_id}")
        if metric_id in seen_metric_ids:
            raise ValueError(f"Duplicate twin qualification report metric: {metric_id}")
        seen_metric_ids.add(metric_id)
        status = metric.get("status")
        if status not in METRIC_STATUSES:
            raise ValueError(f"Twin qualification report metric status is invalid: {metric_id}")
        if metric.get("units") not in PARAMETER_UNITS:
            raise ValueError(f"Twin qualification report metric units are invalid: {metric_id}")
        evidence_mode = metric.get("evidence_mode")
        if evidence_mode not in METRIC_EVIDENCE_MODES:
            raise ValueError(f"Twin qualification report metric evidence mode is invalid: {metric_id}")
        evidence_refs = metric.get("evidence_refs")
        if not isinstance(evidence_refs, list):
            raise ValueError(f"Twin qualification report evidence refs must be a list: {metric_id}")
        if status == "not_run":
            if evidence_mode != "not_run":
                raise ValueError(f"Not-run metric must use not_run evidence mode: {metric_id}")
            if evidence_refs:
                raise ValueError(f"Not-run metric must not carry evidence refs: {metric_id}")
            if metric.get("measured_value") is not None:
                raise ValueError(f"Not-run metric must not carry a measured value: {metric_id}")
        else:
            if not evidence_refs:
                raise ValueError(f"Executed metric must carry evidence refs: {metric_id}")
            if evidence_mode == "not_run":
                raise ValueError(f"Executed metric cannot use not_run evidence mode: {metric_id}")
            if not isinstance(metric.get("measured_value"), (int, float)):
                raise ValueError(f"Executed metric requires a numeric measured value: {metric_id}")
    if set(metric_index) != seen_metric_ids:
        missing = sorted(set(metric_index) - seen_metric_ids)
        raise ValueError(f"Twin qualification report is missing metric results: {missing}")
    if proof_state == "structural_baseline_only":
        for metric in report_metrics:
            if metric["status"] != "not_run":
                raise ValueError("Structural-baseline reports cannot claim executed metric results")
    if proof_state == "physical_qualified":
        for metric in spec["held_out_metrics"]:
            result = next(item for item in report_metrics if item["metric_id"] == metric["metric_id"])
            if result["status"] != "pass":
                raise ValueError("Physical-qualified reports require every metric to pass")
            if "physical_qualified" not in metric["required_for_proof_state"]:
                continue
            if result["evidence_mode"] not in metric["required_evidence_modes"]:
                raise ValueError("Physical-qualified reports require the spec-declared evidence mode")
            if "physical_run" in metric["required_evidence_modes"] and result["evidence_mode"] != "physical_run":
                raise ValueError("Physical-qualified reports require physical metric evidence")
            if not result["evidence_refs"]:
                raise ValueError("Physical-qualified reports require metric evidence refs")


def verify_twin_contract_examples(
    *,
    repo_root: Path,
    profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    spec_path: Path = DEFAULT_TWIN_QUALIFICATION_SPEC_PATH,
    report_path: Path = DEFAULT_TWIN_QUALIFICATION_REPORT_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> dict[str, dict[str, Any]]:
    profile = _read_json(repo_root / profile_path)
    spec = _read_json(repo_root / spec_path)
    report = _read_json(repo_root / report_path)
    verify_twin_profile(profile, repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    verify_twin_qualification_spec(
        spec,
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile=profile,
    )
    verify_twin_qualification_report(
        report,
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile=profile,
        twin_spec=spec,
    )
    return {
        "profile": profile,
        "spec": spec,
        "report": report,
    }


def write_twin_contract_examples(
    *,
    repo_root: Path,
    profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    spec_path: Path = DEFAULT_TWIN_QUALIFICATION_SPEC_PATH,
    report_path: Path = DEFAULT_TWIN_QUALIFICATION_REPORT_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> dict[str, dict[str, Any]]:
    examples = build_twin_contract_examples(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
    )
    _write_json(repo_root / profile_path, examples["profile"])
    _write_json(repo_root / spec_path, examples["spec"])
    _write_json(repo_root / report_path, examples["report"])
    return examples


def _dependency_lock_ref(*, repo_root: Path, dependency_lock_path: Path) -> dict[str, Any]:
    payload = _read_json(repo_root / dependency_lock_path)
    identity = str(payload.get("identity_sha256") or "")
    if not identity:
        raise ValueError("Dependency lock is missing identity_sha256")
    ref = {
        "path": str(dependency_lock_path),
        "schema_version": str(payload["schema_version"]),
        "identity_sha256": identity,
        "file_sha256": _sha256(repo_root / dependency_lock_path),
    }
    return {"payload": payload, "ref": ref}


def _parameter(
    *,
    parameter_id: str,
    value: Any,
    units: str,
    origin: str,
    uncertainty: dict[str, Any] | None = None,
    validity_conditions: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "value": value,
        "units": units,
        "origin": origin,
        "uncertainty": uncertainty or {"lower": 0.0, "upper": 0.0},
        "validity_conditions": validity_conditions or [],
        "evidence": evidence or [],
    }


def _validity_condition(
    *,
    field: str,
    min_value: float | None = None,
    max_value: float | None = None,
    units: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"field": field, "units": units}
    if min_value is not None:
        payload["min_value"] = min_value
    if max_value is not None:
        payload["max_value"] = max_value
    return payload


def _evidence(kind: str, ref: str) -> dict[str, str]:
    return {"kind": kind, "ref": ref}


def _verify_parameter(parameter: dict[str, Any]) -> None:
    parameter_id = str(parameter.get("parameter_id") or "")
    if not parameter_id:
        raise ValueError("Twin profile parameter_id is required")
    if parameter.get("units") not in PARAMETER_UNITS:
        raise ValueError(f"Twin profile parameter units are invalid: {parameter_id}")
    if parameter.get("origin") not in PARAMETER_ORIGINS:
        raise ValueError(f"Twin profile parameter origin is invalid: {parameter_id}")
    uncertainty = parameter.get("uncertainty")
    if not isinstance(uncertainty, dict):
        raise ValueError(f"Twin profile parameter uncertainty is invalid: {parameter_id}")
    if "state" in uncertainty:
        if uncertainty["state"] != "unknown":
            raise ValueError(f"Twin profile parameter uncertainty state is invalid: {parameter_id}")
        if parameter.get("value") is not None:
            raise ValueError(f"Unknown twin profile parameter must not carry a value: {parameter_id}")
    else:
        if "lower" not in uncertainty or "upper" not in uncertainty:
            raise ValueError(f"Twin profile parameter uncertainty bounds are required: {parameter_id}")
        if float(uncertainty["lower"]) > float(uncertainty["upper"]):
            raise ValueError(f"Twin profile parameter uncertainty bounds are reversed: {parameter_id}")
    validity_conditions = parameter.get("validity_conditions")
    if not isinstance(validity_conditions, list):
        raise ValueError(f"Twin profile parameter validity conditions are invalid: {parameter_id}")
    for item in validity_conditions:
        if item.get("units") not in PARAMETER_UNITS:
            raise ValueError(f"Twin profile validity condition units are invalid: {parameter_id}")
    evidence = parameter.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError(f"Twin profile parameter evidence is required: {parameter_id}")
    for item in evidence:
        if not item.get("kind") or not item.get("ref"):
            raise ValueError(f"Twin profile parameter evidence is malformed: {parameter_id}")


def _verify_dependency_lock_ref(payload: dict[str, Any] | None, expected: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Twin artifact dependency lock linkage is missing")
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            raise ValueError(f"Twin artifact dependency lock linkage drifted for {key}")


def _verify_identity_hash(payload: dict[str, Any], *, label: str) -> None:
    expected = str(payload.get("identity_sha256") or "")
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    actual = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if actual != expected:
        raise ValueError(f"{label} identity hash is invalid")


def _verify_proof_state(state: str) -> None:
    if state not in PROOF_STATES:
        raise ValueError(f"Twin proof state is invalid: {state}")


def _sign(payload: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signed = dict(payload)
    signed["identity_sha256"] = hashlib.sha256(encoded).hexdigest()
    return signed


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)

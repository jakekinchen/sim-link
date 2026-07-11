"""Mechanically computed twin qualification with fail-closed authority claims."""

from __future__ import annotations

import hashlib
import json
import math

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    dump_canonical_json,
    load_strict_json,
    require_finite_number,
    require_nonblank,
    sign_payload,
    verify_artifact_ref,
    verify_signed_payload,
)
from scenesmith.robot_lab.authority_composer import (
    DEFAULT_AUTHORITY_SCOPE_ID,
    DEFAULT_AUTHORITY_SUBJECT_ID,
    build_authority_contract,
    build_capability_claim,
    build_composition_request,
    build_evidence_ref,
    compose_authority,
)
from scenesmith.robot_lab.twin_contract import (
    DEFAULT_TWIN_PROFILE_PATH,
    verify_twin_profile,
)


COMPUTED_QUALIFICATION_SPEC_SCHEMA_VERSION = "scenesmith.twin_qualification_spec.v2"
METRIC_EVIDENCE_SCHEMA_VERSION = "scenesmith.twin_metric_evidence.v1"
QUALIFICATION_INPUT_SCHEMA_VERSION = "scenesmith.twin_qualification_input.v1"
COMPUTED_QUALIFICATION_REPORT_SCHEMA_VERSION = "scenesmith.twin_qualification_report.v2"

DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH = Path(
    "configurations/robot_lab/pi05_twin_qualification_spec.computed_v2.json"
)
DEFAULT_FIXTURE_ROOT = Path("tests/fixtures/robot_lab/twin_qualification")
DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS = {
    "sim_joint_limit_projection_error": (
        DEFAULT_FIXTURE_ROOT / "sim_joint_limit_projection_error.fixture.json"
    ),
    "physical_gripper_contact_latency": (
        DEFAULT_FIXTURE_ROOT / "physical_gripper_contact_latency.fixture.json"
    ),
}
DEFAULT_COMPUTED_QUALIFICATION_INPUT_PATH = (
    DEFAULT_FIXTURE_ROOT / "pi05_qualification_input.fixture.json"
)
DEFAULT_COMPUTED_QUALIFICATION_REPORT_PATH = (
    DEFAULT_FIXTURE_ROOT / "pi05_qualification_report.fixture.json"
)

DEFAULT_EVALUATION_TIME = "2026-07-11T02:14:07-05:00"
DEFAULT_VALIDITY = {
    "observed_at": "2026-07-11T02:10:00-05:00",
    "valid_from": "2026-07-11T02:10:00-05:00",
    "valid_until": "2026-07-12T02:10:00-05:00",
    "max_age_seconds": 86400,
}

_PROOF_STATES = {"simulation_only", "physical_qualified"}
_COMPOSITION_MODES = {"fixture", "production"}
_QUALIFICATION_SCOPE_TO_PROVENANCE = {
    "fixture_evidence": "fixture",
    "simulation_evidence": "simulation",
    "physical_evidence": "physical",
    "synthetic_test_only": "synthetic",
    "replay_evidence": "replay",
}
_QUALIFICATION_SCOPE_TO_MODE = {
    "fixture_evidence": "fixture_trace",
    "simulation_evidence": "simulation_trace",
    "physical_evidence": "physical_run",
    "synthetic_test_only": "synthetic_trace",
    "replay_evidence": "replay_trace",
}
_EVIDENCE_AUTHORITY_IDS = {
    "fixture": "scenesmith.fixture_qualification_evidence.v1",
    "simulation": "scenesmith.simulation_qualification_evidence.v1",
    "physical": "scenesmith.physical_qualification_evidence.v1",
    "synthetic": "scenesmith.synthetic_qualification_evidence.v1",
    "replay": "scenesmith.replay_qualification_evidence.v1",
}
_INPUT_AUTHORITY_IDS = {
    "fixture": "scenesmith.fixture_qualification_compiler.v1",
    "production": "scenesmith.production_qualification_compiler.v1",
}
_SPEC_AUTHORITY_ID = "scenesmith.twin_qualification_spec_authority.v2"
_REPORT_AUTHORITY_ID = "scenesmith.twin_qualification_report_compiler.v2"
_MAXIMUM_EVIDENCE_AGE_SECONDS = 86400

_FORBIDDEN_CALLER_FIELDS = {
    "authority",
    "pass",
    "physical_qualification_authority",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "qualification_state",
    "simulation_training_ready",
    "status",
    "training_or_promotion_authority",
}


def qualification_evidence_issuer(provenance_class: str) -> dict[str, str]:
    authority_id = _EVIDENCE_AUTHORITY_IDS.get(provenance_class)
    if authority_id is None:
        raise ValueError(f"Unknown qualification evidence provenance: {provenance_class}")
    return _issuer(authority_id)


def build_computed_qualification_spec(
    *,
    repo_root: Path,
    profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
) -> dict[str, Any]:
    profile = load_strict_json(_resolve(repo_root, profile_path))
    verify_twin_profile(profile, repo_root=repo_root)
    payload = {
        "schema_version": COMPUTED_QUALIFICATION_SPEC_SCHEMA_VERSION,
        "spec_name": "pi05_so101_mechanically_computed_qualification",
        "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
        "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
        "profile_ref": artifact_ref(
            path=_relative_path(repo_root, profile_path),
            payload=profile,
            repo_root=repo_root,
        ),
        "dependency_lock_ref": json.loads(json.dumps(profile["dependency_lock_ref"])),
        "supported_proof_states": sorted(_PROOF_STATES),
        "unit_conversion_policy": "exact_match_only",
        "maximum_evidence_age_seconds": _MAXIMUM_EVIDENCE_AGE_SECONDS,
        "metric_rules": _metric_rules(),
        "issuer": _issuer(_SPEC_AUTHORITY_ID),
    }
    return sign_payload(payload)


def verify_computed_qualification_spec(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    profile: dict[str, Any] | None = None,
) -> None:
    allowed_fields = {
        "schema_version",
        "spec_name",
        "subject_id",
        "scope_id",
        "profile_ref",
        "dependency_lock_ref",
        "supported_proof_states",
        "unit_conversion_policy",
        "maximum_evidence_age_seconds",
        "metric_rules",
        "issuer",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Computed qualification spec fields are malformed")
    if payload.get("schema_version") != COMPUTED_QUALIFICATION_SPEC_SCHEMA_VERSION:
        raise ValueError("Unsupported computed qualification spec schema")
    verify_signed_payload(payload, label="Computed qualification spec")
    if payload.get("spec_name") != "pi05_so101_mechanically_computed_qualification":
        raise ValueError("Computed qualification spec name is invalid")
    if payload.get("issuer") != _issuer(_SPEC_AUTHORITY_ID):
        raise ValueError("Computed qualification spec issuer is unauthorized")
    if payload.get("subject_id") != DEFAULT_AUTHORITY_SUBJECT_ID:
        raise ValueError("Computed qualification spec subject is invalid")
    if payload.get("scope_id") != DEFAULT_AUTHORITY_SCOPE_ID:
        raise ValueError("Computed qualification spec scope is invalid")
    profile_reference = payload.get("profile_ref")
    if not isinstance(profile_reference, dict):
        raise ValueError("Computed qualification spec profile linkage is missing")
    _validated_ref_path(
        profile_reference.get("path"),
        repo_root=repo_root,
        label="qualification profile",
    )
    selected_profile = profile or _load_artifact_ref(
        profile_reference,
        repo_root=repo_root,
        label="qualification profile",
    )
    verify_twin_profile(selected_profile, repo_root=repo_root)
    expected_profile_ref = artifact_ref(
        path=Path(payload["profile_ref"]["path"]),
        payload=selected_profile,
        repo_root=repo_root,
    )
    verify_artifact_ref(payload.get("profile_ref"), expected_profile_ref, label="qualification profile")
    if payload.get("dependency_lock_ref") != selected_profile.get("dependency_lock_ref"):
        raise ValueError("Computed qualification spec dependency linkage drifted")
    if payload.get("supported_proof_states") != sorted(_PROOF_STATES):
        raise ValueError("Computed qualification spec proof states drifted")
    if payload.get("unit_conversion_policy") != "exact_match_only":
        raise ValueError("Computed qualification spec unit conversion policy drifted")
    if payload.get("maximum_evidence_age_seconds") != _MAXIMUM_EVIDENCE_AGE_SECONDS:
        raise ValueError("Computed qualification spec maximum evidence age drifted")
    rules = payload.get("metric_rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("Computed qualification spec metric rules are required")
    seen: set[str] = set()
    for rule in rules:
        _verify_metric_rule(rule)
        metric_id = rule["metric_id"]
        if metric_id in seen:
            raise ValueError(f"Duplicate qualification metric rule: {metric_id}")
        seen.add(metric_id)
    if rules != sorted(rules, key=lambda item: item["metric_id"]):
        raise ValueError("Computed qualification spec metric rules are not canonical")
    if rules != _metric_rules():
        raise ValueError("Computed qualification spec rules drifted from the code-pinned contract")


def build_fixture_metric_evidence(
    metric_id: str,
    *,
    reverse_inputs: bool = False,
) -> dict[str, Any]:
    if metric_id == "sim_joint_limit_projection_error":
        units = "radian"
        sample_values = (
            ("sim-sample-001", "heldout-sim-trajectory-001", 0.010, "2026-07-11T02:11:00-05:00"),
            ("sim-sample-002", "heldout-sim-trajectory-001", 0.015, "2026-07-11T02:11:10-05:00"),
            ("sim-sample-003", "heldout-sim-trajectory-002", 0.012, "2026-07-11T02:11:20-05:00"),
        )
        conditions = (
            {"condition_id": "simulation_timestep", "units": "second", "value": 0.01},
        )
        uncertainty_value = 0.002
    elif metric_id == "physical_gripper_contact_latency":
        units = "millisecond"
        sample_values = (
            ("contact-sample-001", "heldout-contact-trajectory-001", 18.0, "2026-07-11T02:11:00-05:00"),
            ("contact-sample-002", "heldout-contact-trajectory-001", 21.0, "2026-07-11T02:11:10-05:00"),
            ("contact-sample-003", "heldout-contact-trajectory-002", 20.0, "2026-07-11T02:11:20-05:00"),
        )
        conditions = (
            {"condition_id": "ambient_temperature", "units": "celsius", "value": 24.0},
            {"condition_id": "supply_voltage", "units": "volt", "value": 12.0},
        )
        uncertainty_value = 2.0
    else:
        raise ValueError(f"Unknown fixture qualification metric: {metric_id}")
    samples = [
        {
            "sample_id": sample_id,
            "trajectory_id": trajectory_id,
            "value": value,
            "observed_at": observed_at,
        }
        for sample_id, trajectory_id, value, observed_at in sample_values
    ]
    condition_items = [dict(item) for item in conditions]
    if reverse_inputs:
        samples.reverse()
        condition_items.reverse()
    samples.sort(key=lambda item: item["sample_id"])
    condition_items.sort(key=lambda item: item["condition_id"])
    payload = {
        "schema_version": METRIC_EVIDENCE_SCHEMA_VERSION,
        "metric_id": metric_id,
        "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
        "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
        "qualification_scope": "fixture_evidence",
        "provenance_class": "fixture",
        "evidence_mode": "fixture_trace",
        "issuer": qualification_evidence_issuer("fixture"),
        "units": units,
        "declared_sample_count": len(samples),
        "held_out_trajectory_ids": sorted({item["trajectory_id"] for item in samples}),
        "samples": samples,
        "conditions": condition_items,
        "uncertainty": {
            "kind": "absolute_upper_bound",
            "value": uncertainty_value,
            "units": units,
            "confidence_level": 0.95,
        },
        "validity": dict(DEFAULT_VALIDITY),
    }
    return sign_payload(payload)


def verify_metric_evidence(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    evaluation_time: str,
    composition_mode: str,
    artifact_path: Path | None = None,
) -> None:
    allowed_fields = {
        "schema_version",
        "metric_id",
        "subject_id",
        "scope_id",
        "qualification_scope",
        "provenance_class",
        "evidence_mode",
        "issuer",
        "units",
        "declared_sample_count",
        "held_out_trajectory_ids",
        "samples",
        "conditions",
        "uncertainty",
        "validity",
        "identity_sha256",
    }
    forbidden = _find_forbidden_fields(payload)
    if forbidden or not isinstance(payload, dict) or set(payload) != allowed_fields:
        suffix = f": {sorted(forbidden)}" if forbidden else ""
        raise ValueError(f"Metric evidence fields are malformed or carry caller status{suffix}")
    if payload.get("schema_version") != METRIC_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Unsupported metric evidence schema")
    verify_signed_payload(payload, label="Metric evidence")
    mode = _composition_mode(composition_mode)
    if payload.get("subject_id") != spec.get("subject_id"):
        raise ValueError("Metric evidence subject does not match qualification spec")
    if payload.get("scope_id") != spec.get("scope_id"):
        raise ValueError("Metric evidence scope does not match qualification spec")
    qualification_scope = payload.get("qualification_scope")
    expected_provenance = _QUALIFICATION_SCOPE_TO_PROVENANCE.get(str(qualification_scope))
    expected_mode = _QUALIFICATION_SCOPE_TO_MODE.get(str(qualification_scope))
    if expected_provenance is None:
        raise ValueError("Metric evidence qualification scope is invalid")
    if payload.get("provenance_class") != expected_provenance:
        raise ValueError("Metric evidence provenance contradicts its qualification scope")
    if payload.get("evidence_mode") != expected_mode:
        raise ValueError("Metric evidence mode contradicts its qualification scope")
    if payload.get("issuer") != qualification_evidence_issuer(expected_provenance):
        raise ValueError("Metric evidence issuer is unauthorized for its provenance")
    if mode == "fixture" and expected_provenance != "fixture":
        raise ValueError("Non-fixture evidence is forbidden in a fixture composition")
    if mode == "production" and expected_provenance == "fixture":
        raise ValueError("Fixture evidence is forbidden in a production composition")
    if artifact_path is not None:
        path_parts = artifact_path.parts
        is_fixture_path = len(path_parts) >= 2 and path_parts[:2] == ("tests", "fixtures")
        if expected_provenance != "fixture" and is_fixture_path:
            raise ValueError("Fixture-path evidence cannot impersonate production evidence")
        if expected_provenance == "fixture" and not is_fixture_path:
            raise ValueError("Fixture evidence must remain under the fixture evidence root")
    rule = _metric_rule_index(spec).get(payload.get("metric_id"))
    if rule is None:
        raise ValueError(f"Metric evidence references an unknown metric: {payload.get('metric_id')}")
    if payload.get("units") != rule["units"]:
        raise ValueError(f"Metric evidence units do not match the spec: {rule['metric_id']}")
    evaluation = _parse_timestamp(evaluation_time, label="qualification evaluation_time")
    validity = _validate_validity(
        payload.get("validity"),
        evaluation_time=evaluation,
        label="metric evidence",
        maximum_age_seconds=spec["maximum_evidence_age_seconds"],
    )
    samples = payload.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError(f"Metric evidence samples are required: {rule['metric_id']}")
    if payload.get("declared_sample_count") != len(samples):
        raise ValueError(f"Metric evidence sample count drifted: {rule['metric_id']}")
    if len(samples) < rule["minimum_sample_count"]:
        raise ValueError(f"Metric evidence sample count is below the spec: {rule['metric_id']}")
    sample_ids: set[str] = set()
    trajectory_ids: set[str] = set()
    for sample in samples:
        if not isinstance(sample, dict) or set(sample) != {
            "sample_id",
            "trajectory_id",
            "value",
            "observed_at",
        }:
            raise ValueError(f"Metric evidence sample fields are malformed: {rule['metric_id']}")
        sample_id = require_nonblank(sample.get("sample_id"), label="qualification sample_id")
        if sample_id in sample_ids:
            raise ValueError(f"Duplicate qualification sample_id: {sample_id}")
        sample_ids.add(sample_id)
        trajectory_id = require_nonblank(
            sample.get("trajectory_id"),
            label="held-out trajectory_id",
        )
        trajectory_ids.add(trajectory_id)
        sample_value = require_finite_number(
            sample.get("value"),
            label=f"{rule['metric_id']} sample value",
        )
        if sample_value < rule["sample_minimum"]:
            raise ValueError(f"Metric evidence sample is below the spec minimum: {rule['metric_id']}")
        observed = _parse_timestamp(sample.get("observed_at"), label="sample observed_at")
        if (
            observed < validity["observed_at"]
            or observed < validity["valid_from"]
            or observed > validity["valid_until"]
        ):
            raise ValueError("Metric evidence sample timestamp falls outside validity")
        if observed > evaluation:
            raise ValueError("Metric evidence sample timestamp is after evaluation")
    if samples != sorted(samples, key=lambda item: item["sample_id"]):
        raise ValueError("Metric evidence samples are not canonical")
    declared_trajectories = payload.get("held_out_trajectory_ids")
    if declared_trajectories != sorted(trajectory_ids):
        raise ValueError(f"Metric evidence held-out trajectory IDs drifted: {rule['metric_id']}")
    if len(trajectory_ids) < rule["minimum_trajectory_count"]:
        raise ValueError(f"Metric evidence trajectory count is below the spec: {rule['metric_id']}")
    _verify_conditions(payload.get("conditions"), rule=rule)
    _verify_uncertainty(payload.get("uncertainty"), rule=rule)


def build_qualification_input(
    *,
    repo_root: Path,
    spec_path: Path = DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH,
    profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
    metric_evidence_paths: Iterable[Path] = tuple(DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS.values()),
    composition_mode: str = "fixture",
    requested_proof_state: str = "simulation_only",
    evaluation_time: str = DEFAULT_EVALUATION_TIME,
    validity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mode = _composition_mode(composition_mode)
    if _relative_path(repo_root, profile_path) != DEFAULT_TWIN_PROFILE_PATH:
        raise ValueError("Qualification input builder requires the code-pinned profile path")
    if _relative_path(repo_root, spec_path) != DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH:
        raise ValueError("Qualification input builder requires the code-pinned spec path")
    if requested_proof_state not in _PROOF_STATES:
        raise ValueError(f"Unsupported requested proof state: {requested_proof_state}")
    evaluation = _canonical_timestamp(evaluation_time, label="qualification evaluation_time")
    selected_validity = json.loads(json.dumps(validity or DEFAULT_VALIDITY))
    _validate_validity(
        selected_validity,
        evaluation_time=_parse_timestamp(evaluation, label="qualification evaluation_time"),
        label="qualification input",
        maximum_age_seconds=_MAXIMUM_EVIDENCE_AGE_SECONDS,
    )
    profile = load_strict_json(_resolve(repo_root, profile_path))
    verify_twin_profile(profile, repo_root=repo_root)
    spec = load_strict_json(_resolve(repo_root, spec_path))
    verify_computed_qualification_spec(spec, repo_root=repo_root, profile=profile)
    expected_profile_ref = artifact_ref(
        path=_relative_path(repo_root, profile_path),
        payload=profile,
        repo_root=repo_root,
    )
    verify_artifact_ref(spec.get("profile_ref"), expected_profile_ref, label="qualification profile")
    refs: list[dict[str, Any]] = []
    seen_metrics: set[str] = set()
    seen_identities: set[str] = set()
    for path in metric_evidence_paths:
        relative_path = _relative_path(repo_root, path)
        evidence = load_strict_json(_resolve(repo_root, relative_path))
        verify_metric_evidence(
            evidence,
            spec=spec,
            evaluation_time=evaluation,
            composition_mode=mode,
            artifact_path=relative_path,
        )
        metric_id = evidence["metric_id"]
        if metric_id in seen_metrics:
            raise ValueError(f"Duplicate metric evidence input: {metric_id}")
        seen_metrics.add(metric_id)
        if evidence["identity_sha256"] in seen_identities:
            raise ValueError("Qualification input reuses a metric evidence identity")
        seen_identities.add(evidence["identity_sha256"])
        refs.append(
            {
                "metric_id": metric_id,
                "artifact_ref": artifact_ref(
                    path=relative_path,
                    payload=evidence,
                    repo_root=repo_root,
                ),
            }
        )
    if not refs:
        raise ValueError("Qualification input requires at least one metric evidence artifact")
    refs.sort(key=lambda item: (item["metric_id"], item["artifact_ref"]["identity_sha256"]))
    payload = {
        "schema_version": QUALIFICATION_INPUT_SCHEMA_VERSION,
        "input_name": "pi05_so101_qualification_input",
        "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
        "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
        "requested_proof_state": requested_proof_state,
        "composition_mode": mode,
        "evaluation_time": evaluation,
        "validity": selected_validity,
        "issuer": _issuer(_INPUT_AUTHORITY_IDS[mode]),
        "profile_ref": expected_profile_ref,
        "spec_ref": artifact_ref(
            path=_relative_path(repo_root, spec_path),
            payload=spec,
            repo_root=repo_root,
        ),
        "metric_evidence_refs": refs,
    }
    return sign_payload(payload)


def verify_qualification_input(
    payload: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    allowed_fields = {
        "schema_version",
        "input_name",
        "subject_id",
        "scope_id",
        "requested_proof_state",
        "composition_mode",
        "evaluation_time",
        "validity",
        "issuer",
        "profile_ref",
        "spec_ref",
        "metric_evidence_refs",
        "identity_sha256",
    }
    forbidden = _find_forbidden_fields(payload)
    if forbidden or not isinstance(payload, dict) or set(payload) != allowed_fields:
        suffix = f": {sorted(forbidden)}" if forbidden else ""
        raise ValueError(f"Qualification input fields are malformed or carry caller status{suffix}")
    if payload.get("schema_version") != QUALIFICATION_INPUT_SCHEMA_VERSION:
        raise ValueError("Unsupported qualification input schema")
    verify_signed_payload(payload, label="Qualification input")
    if payload.get("input_name") != "pi05_so101_qualification_input":
        raise ValueError("Qualification input name is invalid")
    mode = _composition_mode(payload.get("composition_mode"))
    if payload.get("issuer") != _issuer(_INPUT_AUTHORITY_IDS[mode]):
        raise ValueError("Qualification input issuer is unauthorized")
    if payload.get("subject_id") != DEFAULT_AUTHORITY_SUBJECT_ID:
        raise ValueError("Qualification input subject is invalid")
    if payload.get("scope_id") != DEFAULT_AUTHORITY_SCOPE_ID:
        raise ValueError("Qualification input scope is invalid")
    if payload.get("requested_proof_state") not in _PROOF_STATES:
        raise ValueError("Qualification input requested proof state is invalid")
    evaluation_text = _canonical_timestamp(
        payload.get("evaluation_time"),
        label="qualification evaluation_time",
    )
    evaluation = _parse_timestamp(evaluation_text, label="qualification evaluation_time")
    input_validity = _validate_validity(
        payload.get("validity"),
        evaluation_time=evaluation,
        label="qualification input",
        maximum_age_seconds=_MAXIMUM_EVIDENCE_AGE_SECONDS,
    )
    profile = _load_artifact_ref(
        payload.get("profile_ref"),
        repo_root=repo_root,
        label="qualification profile",
    )
    if payload["profile_ref"]["path"] != str(DEFAULT_TWIN_PROFILE_PATH):
        raise ValueError("Qualification input profile path is not the code-pinned profile")
    verify_twin_profile(profile, repo_root=repo_root)
    if (
        payload.get("requested_proof_state") == "physical_qualified"
        and profile.get("proof_state") != "physical_qualified"
    ):
        raise ValueError(
            "Physical qualification input requires a physical-qualified profile; the profile "
            "does not pre-authorize that state"
        )
    spec = _load_artifact_ref(
        payload.get("spec_ref"),
        repo_root=repo_root,
        label="qualification spec",
    )
    if payload["spec_ref"]["path"] != str(DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH):
        raise ValueError("Qualification input spec path is not the code-pinned spec")
    verify_computed_qualification_spec(spec, repo_root=repo_root, profile=profile)
    verify_artifact_ref(spec.get("profile_ref"), payload["profile_ref"], label="qualification profile")
    refs = payload.get("metric_evidence_refs")
    if not isinstance(refs, list) or not refs:
        raise ValueError("Qualification input metric evidence refs are required")
    if refs != sorted(
        refs,
        key=lambda item: (
            str(item.get("metric_id", "")),
            str((item.get("artifact_ref") or {}).get("identity_sha256", "")),
        ),
    ):
        raise ValueError("Qualification input metric evidence refs are not canonical")
    evidence: dict[str, dict[str, Any]] = {}
    identities: set[str] = set()
    paths: set[str] = set()
    for item in refs:
        if not isinstance(item, dict) or set(item) != {"metric_id", "artifact_ref"}:
            raise ValueError("Qualification input metric evidence ref is malformed")
        metric_id = require_nonblank(item.get("metric_id"), label="qualification metric_id")
        if metric_id in evidence:
            raise ValueError(f"Duplicate qualification metric evidence: {metric_id}")
        loaded = _load_artifact_ref(
            item.get("artifact_ref"),
            repo_root=repo_root,
            label=f"qualification evidence {metric_id}",
        )
        if loaded.get("metric_id") != metric_id:
            raise ValueError("Qualification evidence substitution changed metric identity")
        identity = loaded.get("identity_sha256")
        path = (item.get("artifact_ref") or {}).get("path")
        if identity in identities or path in paths:
            raise ValueError("Qualification input reuses metric evidence")
        identities.add(identity)
        paths.add(path)
        verify_metric_evidence(
            loaded,
            spec=spec,
            evaluation_time=evaluation_text,
            composition_mode=mode,
            artifact_path=Path(path),
        )
        evidence[metric_id] = loaded
    evidence_validities = [
        _validate_validity(
            item["validity"],
            evaluation_time=evaluation,
            label=f"metric evidence {item['metric_id']}",
            maximum_age_seconds=spec["maximum_evidence_age_seconds"],
        )
        for item in evidence.values()
    ]
    if input_validity["observed_at"] != max(
        item["observed_at"] for item in evidence_validities
    ):
        raise ValueError("Qualification input freshness does not match its metric evidence")
    if input_validity["valid_from"] < max(
        item["valid_from"] for item in evidence_validities
    ):
        raise ValueError("Qualification input validity starts before its metric evidence")
    if input_validity["valid_until"] > min(
        item["valid_until"] for item in evidence_validities
    ):
        raise ValueError("Qualification input validity exceeds its metric evidence")
    if input_validity["max_age_seconds"] > min(
        item["max_age_seconds"] for item in evidence_validities
    ):
        raise ValueError("Qualification input freshness exceeds its metric evidence")
    return {"profile": profile, "spec": spec, "evidence": evidence}


def generate_computed_qualification_report(
    qualification_input: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    context = verify_qualification_input(qualification_input, repo_root=repo_root)
    spec = context["spec"]
    evidence = context["evidence"]
    metrics = [
        _generate_metric_result(rule, evidence.get(rule["metric_id"]), qualification_input)
        for rule in spec["metric_rules"]
    ]
    summary = _generate_summary(
        metrics,
        spec=spec,
        requested_proof_state=qualification_input["requested_proof_state"],
    )
    capabilities = _generate_capabilities(metrics, spec=spec, profile=context["profile"])
    if qualification_input["composition_mode"] == "fixture":
        capabilities["required_simulation_properties_available"] = False
        capabilities["held_out_twin_metrics_passed"] = False
    payload = {
        "schema_version": COMPUTED_QUALIFICATION_REPORT_SCHEMA_VERSION,
        "report_name": "pi05_so101_mechanically_computed_qualification",
        "subject_id": qualification_input["subject_id"],
        "scope_id": qualification_input["scope_id"],
        "requested_proof_state": qualification_input["requested_proof_state"],
        "composition_mode": qualification_input["composition_mode"],
        "evaluation_time": qualification_input["evaluation_time"],
        "input_identity_sha256": qualification_input["identity_sha256"],
        "profile_ref": json.loads(json.dumps(qualification_input["profile_ref"])),
        "spec_ref": json.loads(json.dumps(qualification_input["spec_ref"])),
        "metrics": metrics,
        "summary": summary,
        "capabilities": capabilities,
        "issuer": _issuer(_REPORT_AUTHORITY_ID),
    }
    return sign_payload(payload)


def verify_computed_qualification_report(
    payload: dict[str, Any],
    *,
    qualification_input: dict[str, Any],
    repo_root: Path,
) -> None:
    allowed_fields = {
        "schema_version",
        "report_name",
        "subject_id",
        "scope_id",
        "requested_proof_state",
        "composition_mode",
        "evaluation_time",
        "input_identity_sha256",
        "profile_ref",
        "spec_ref",
        "metrics",
        "summary",
        "capabilities",
        "issuer",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Computed qualification report fields are malformed")
    if payload.get("schema_version") != COMPUTED_QUALIFICATION_REPORT_SCHEMA_VERSION:
        raise ValueError("Unsupported computed qualification report schema")
    verify_signed_payload(payload, label="Computed qualification report")
    if payload.get("report_name") != "pi05_so101_mechanically_computed_qualification":
        raise ValueError("Computed qualification report name is invalid")
    if payload.get("issuer") != _issuer(_REPORT_AUTHORITY_ID):
        raise ValueError("Computed qualification report issuer is unauthorized")
    context = verify_qualification_input(qualification_input, repo_root=repo_root)
    for key in (
        "subject_id",
        "scope_id",
        "requested_proof_state",
        "composition_mode",
        "evaluation_time",
        "profile_ref",
        "spec_ref",
    ):
        if payload.get(key) != qualification_input.get(key):
            raise ValueError(f"Computed qualification report input linkage drifted: {key}")
    if payload.get("input_identity_sha256") != qualification_input.get("identity_sha256"):
        raise ValueError("Computed qualification report input identity drifted")
    report_metrics = payload.get("metrics")
    if not isinstance(report_metrics, list):
        raise ValueError("Computed qualification report metrics are malformed")
    if len(report_metrics) != len(context["spec"]["metric_rules"]):
        raise ValueError("Computed qualification report metric set drifted")
    expected_metric_order = [item["metric_id"] for item in context["spec"]["metric_rules"]]
    if [item.get("metric_id") for item in report_metrics if isinstance(item, dict)] != expected_metric_order:
        raise ValueError("Computed qualification report metric order drifted")
    observed_index: dict[str, dict[str, Any]] = {}
    for metric in report_metrics:
        if not isinstance(metric, dict):
            raise ValueError("Computed qualification report metric is malformed")
        metric_id = metric.get("metric_id")
        if metric_id in observed_index:
            raise ValueError(f"Duplicate computed qualification report metric: {metric_id}")
        observed_index[metric_id] = metric
    for rule in context["spec"]["metric_rules"]:
        metric_id = rule["metric_id"]
        expected = _independently_recompute_metric(
            rule,
            context["evidence"].get(metric_id),
        )
        if observed_index.get(metric_id) != expected:
            raise ValueError(
                f"Computed qualification report metric drifted from independent recomputation: {metric_id}"
            )
    canonical_metrics = [observed_index[rule["metric_id"]] for rule in context["spec"]["metric_rules"]]
    expected_summary = _independently_recompute_summary(
        canonical_metrics,
        spec=context["spec"],
        requested_proof_state=qualification_input["requested_proof_state"],
    )
    if payload.get("summary") != expected_summary:
        raise ValueError("Computed qualification report summary drifted from independent recomputation")
    expected_capabilities = _independently_recompute_capabilities(
        canonical_metrics,
        spec=context["spec"],
        profile=context["profile"],
    )
    if qualification_input["composition_mode"] == "fixture":
        expected_capabilities["required_simulation_properties_available"] = False
        expected_capabilities["held_out_twin_metrics_passed"] = False
    if payload.get("capabilities") != expected_capabilities:
        raise ValueError("Computed qualification report capabilities drifted from independent recomputation")


def build_qualification_capability_claims(
    report: dict[str, Any],
    *,
    qualification_input: dict[str, Any],
    repo_root: Path,
) -> list[dict[str, Any]]:
    verify_computed_qualification_report(
        report,
        qualification_input=qualification_input,
        repo_root=repo_root,
    )
    contract = build_authority_contract()
    prerequisites = {
        item["prerequisite_id"]: item for item in contract["prerequisites"]
    }
    claims = []
    capability_provenance = {
        "required_simulation_properties_available": "simulation",
        "held_out_twin_metrics_passed": "physical",
    }
    for capability_id in sorted(capability_provenance):
        value = report["capabilities"][capability_id]
        provenance = capability_provenance[capability_id]
        if qualification_input["composition_mode"] == "fixture":
            provenance = "fixture"
        spec = prerequisites[capability_id]
        issuer = spec["authorized_issuers"][0]
        evidence_refs = []
        if value:
            evidence_refs = [
                build_evidence_ref(
                    artifact_kind="computed_twin_qualification_report",
                    artifact_schema_version=report["schema_version"],
                    artifact_identity_sha256=report["identity_sha256"],
                    subject_id=report["subject_id"],
                    scope_id=report["scope_id"],
                    provenance_class=provenance,
                )
            ]
        claims.append(
            build_capability_claim(
                claim_id=f"computed_qualification_{capability_id}",
                capability_id=capability_id,
                value=value,
                subject_id=report["subject_id"],
                scope_id=report["scope_id"],
                provenance_class=provenance,
                issuer=issuer,
                validity=json.loads(json.dumps(qualification_input["validity"])),
                evidence_refs=evidence_refs,
            )
        )
    return claims


def compose_qualification_authority(
    report: dict[str, Any],
    *,
    qualification_input: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    claims = build_qualification_capability_claims(
        report,
        qualification_input=qualification_input,
        repo_root=repo_root,
    )
    request = build_composition_request(
        subject_id=qualification_input["subject_id"],
        scope_id=qualification_input["scope_id"],
        evaluation_time=qualification_input["evaluation_time"],
        claims=claims,
        composition_mode=qualification_input["composition_mode"],
    )
    return {"claims": claims, "request": request, "decision": compose_authority(request)}


def write_qualification_fixture_artifacts(
    *,
    repo_root: Path,
    spec_path: Path = DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH,
    metric_evidence_paths: dict[str, Path] = DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS,
    input_path: Path = DEFAULT_COMPUTED_QUALIFICATION_INPUT_PATH,
    report_path: Path = DEFAULT_COMPUTED_QUALIFICATION_REPORT_PATH,
) -> dict[str, Any]:
    spec = build_computed_qualification_spec(repo_root=repo_root)
    dump_canonical_json(_resolve(repo_root, spec_path), spec)
    evidence = {
        metric_id: build_fixture_metric_evidence(metric_id)
        for metric_id in sorted(metric_evidence_paths)
    }
    for metric_id, payload in evidence.items():
        dump_canonical_json(_resolve(repo_root, metric_evidence_paths[metric_id]), payload)
    qualification_input = build_qualification_input(
        repo_root=repo_root,
        spec_path=spec_path,
        metric_evidence_paths=[metric_evidence_paths[key] for key in sorted(metric_evidence_paths)],
        composition_mode="fixture",
    )
    dump_canonical_json(_resolve(repo_root, input_path), qualification_input)
    report = generate_computed_qualification_report(qualification_input, repo_root=repo_root)
    dump_canonical_json(_resolve(repo_root, report_path), report)
    authority = compose_qualification_authority(
        report,
        qualification_input=qualification_input,
        repo_root=repo_root,
    )
    return {
        "spec": spec,
        "evidence": evidence,
        "input": qualification_input,
        "report": report,
        **authority,
    }


def verify_qualification_fixture_artifacts(
    *,
    repo_root: Path,
    spec_path: Path = DEFAULT_COMPUTED_QUALIFICATION_SPEC_PATH,
    metric_evidence_paths: dict[str, Path] = DEFAULT_FIXTURE_METRIC_EVIDENCE_PATHS,
    input_path: Path = DEFAULT_COMPUTED_QUALIFICATION_INPUT_PATH,
    report_path: Path = DEFAULT_COMPUTED_QUALIFICATION_REPORT_PATH,
) -> dict[str, Any]:
    spec = load_strict_json(_resolve(repo_root, spec_path))
    expected_spec = build_computed_qualification_spec(repo_root=repo_root)
    if spec != expected_spec:
        raise ValueError("Tracked computed qualification spec drifted from deterministic build")
    verify_computed_qualification_spec(spec, repo_root=repo_root)
    evidence: dict[str, dict[str, Any]] = {}
    for metric_id in sorted(metric_evidence_paths):
        observed = load_strict_json(_resolve(repo_root, metric_evidence_paths[metric_id]))
        expected = build_fixture_metric_evidence(metric_id)
        if observed != expected:
            raise ValueError(f"Tracked metric evidence drifted from deterministic fixture: {metric_id}")
        evidence[metric_id] = observed
    qualification_input = load_strict_json(_resolve(repo_root, input_path))
    expected_input = build_qualification_input(
        repo_root=repo_root,
        spec_path=spec_path,
        metric_evidence_paths=[metric_evidence_paths[key] for key in sorted(metric_evidence_paths)],
        composition_mode="fixture",
    )
    if qualification_input != expected_input:
        raise ValueError("Tracked qualification input drifted from deterministic fixture")
    verify_qualification_input(qualification_input, repo_root=repo_root)
    report = load_strict_json(_resolve(repo_root, report_path))
    verify_computed_qualification_report(
        report,
        qualification_input=qualification_input,
        repo_root=repo_root,
    )
    expected_report = generate_computed_qualification_report(
        qualification_input,
        repo_root=repo_root,
    )
    if report != expected_report:
        raise ValueError("Tracked computed qualification report drifted from deterministic build")
    authority = compose_qualification_authority(
        report,
        qualification_input=qualification_input,
        repo_root=repo_root,
    )
    return {
        "spec": spec,
        "evidence": evidence,
        "input": qualification_input,
        "report": report,
        **authority,
    }


def _metric_rules() -> list[dict[str, Any]]:
    rules = [
        {
            "metric_id": "sim_joint_limit_projection_error",
            "description": "Held-out simulator replay stays within joint-space error budget.",
            "units": "radian",
            "aggregation": "maximum",
            "comparison": "less_than_or_equal",
            "tolerance": {"max_value": 0.05, "units": "radian"},
            "uncertainty_mode": "absolute_upper_bound",
            "sample_minimum": 0.0,
            "minimum_sample_count": 3,
            "minimum_trajectory_count": 2,
            "required_evidence_modes": ["simulation_trace"],
            "allowed_provenance_classes": ["simulation"],
            "required_for_proof_states": ["physical_qualified", "simulation_only"],
            "required_conditions": [
                {
                    "condition_id": "simulation_timestep",
                    "units": "second",
                    "minimum": 0.001,
                    "maximum": 0.02,
                }
            ],
        },
        {
            "metric_id": "physical_gripper_contact_latency",
            "description": "Held-out physical contact latency remains inside the declared envelope.",
            "units": "millisecond",
            "aggregation": "maximum",
            "comparison": "less_than_or_equal",
            "tolerance": {"max_value": 35.0, "units": "millisecond"},
            "uncertainty_mode": "absolute_upper_bound",
            "sample_minimum": 0.0,
            "minimum_sample_count": 3,
            "minimum_trajectory_count": 2,
            "required_evidence_modes": ["physical_run"],
            "allowed_provenance_classes": ["physical"],
            "required_for_proof_states": ["physical_qualified"],
            "required_conditions": [
                {
                    "condition_id": "ambient_temperature",
                    "units": "celsius",
                    "minimum": 10.0,
                    "maximum": 45.0,
                },
                {
                    "condition_id": "supply_voltage",
                    "units": "volt",
                    "minimum": 11.0,
                    "maximum": 13.0,
                },
            ],
        },
    ]
    return sorted(rules, key=lambda item: item["metric_id"])


def _verify_metric_rule(rule: Any) -> None:
    fields = {
        "metric_id",
        "description",
        "units",
        "aggregation",
        "comparison",
        "tolerance",
        "uncertainty_mode",
        "sample_minimum",
        "minimum_sample_count",
        "minimum_trajectory_count",
        "required_evidence_modes",
        "allowed_provenance_classes",
        "required_for_proof_states",
        "required_conditions",
    }
    if not isinstance(rule, dict) or set(rule) != fields:
        raise ValueError("Computed qualification metric rule fields are malformed")
    require_nonblank(rule.get("metric_id"), label="qualification metric_id")
    require_nonblank(rule.get("description"), label="qualification metric description")
    require_nonblank(rule.get("units"), label="qualification metric units")
    if rule.get("aggregation") != "maximum":
        raise ValueError("Only maximum qualification aggregation is supported")
    if rule.get("comparison") != "less_than_or_equal":
        raise ValueError("Only less_than_or_equal qualification comparison is supported")
    tolerance = rule.get("tolerance")
    if not isinstance(tolerance, dict) or set(tolerance) != {"max_value", "units"}:
        raise ValueError("Qualification metric tolerance is malformed")
    require_finite_number(tolerance.get("max_value"), label="qualification tolerance", positive=True)
    if tolerance.get("units") != rule.get("units"):
        raise ValueError("Qualification metric tolerance units drifted")
    if rule.get("uncertainty_mode") != "absolute_upper_bound":
        raise ValueError("Qualification metric uncertainty mode is unsupported")
    require_finite_number(rule.get("sample_minimum"), label="qualification sample minimum")
    for field in ("minimum_sample_count", "minimum_trajectory_count"):
        value = rule.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"Qualification metric {field} must be a positive integer")
    modes = rule.get("required_evidence_modes")
    if not isinstance(modes, list) or not modes or modes != sorted(set(modes)):
        raise ValueError("Qualification metric evidence modes are malformed")
    provenance = rule.get("allowed_provenance_classes")
    if not isinstance(provenance, list) or not provenance or provenance != sorted(set(provenance)):
        raise ValueError("Qualification metric provenance classes are malformed")
    states = rule.get("required_for_proof_states")
    if not isinstance(states, list) or not states or states != sorted(set(states)):
        raise ValueError("Qualification metric proof states are malformed")
    if any(state not in _PROOF_STATES for state in states):
        raise ValueError("Qualification metric proof state is unsupported")
    conditions = rule.get("required_conditions")
    if not isinstance(conditions, list) or not conditions:
        raise ValueError("Qualification metric required conditions are missing")
    condition_ids: set[str] = set()
    for condition in conditions:
        if not isinstance(condition, dict) or set(condition) != {
            "condition_id",
            "units",
            "minimum",
            "maximum",
        }:
            raise ValueError("Qualification metric condition rule is malformed")
        condition_id = require_nonblank(condition.get("condition_id"), label="condition_id")
        if condition_id in condition_ids:
            raise ValueError(f"Duplicate qualification condition: {condition_id}")
        condition_ids.add(condition_id)
        minimum = require_finite_number(condition.get("minimum"), label="condition minimum")
        maximum = require_finite_number(condition.get("maximum"), label="condition maximum")
        if maximum < minimum:
            raise ValueError("Qualification condition bounds are reversed")
        require_nonblank(condition.get("units"), label="condition units")
    if conditions != sorted(conditions, key=lambda item: item["condition_id"]):
        raise ValueError("Qualification metric condition rules are not canonical")


def _verify_conditions(payload: Any, *, rule: dict[str, Any]) -> None:
    if not isinstance(payload, list):
        raise ValueError(f"Metric evidence conditions are required: {rule['metric_id']}")
    expected = {item["condition_id"]: item for item in rule["required_conditions"]}
    observed: dict[str, dict[str, Any]] = {}
    for condition in payload:
        if not isinstance(condition, dict) or set(condition) != {"condition_id", "units", "value"}:
            raise ValueError(f"Metric evidence condition fields are malformed: {rule['metric_id']}")
        condition_id = require_nonblank(condition.get("condition_id"), label="condition_id")
        if condition_id in observed:
            raise ValueError(f"Duplicate metric evidence condition: {condition_id}")
        if condition_id not in expected:
            raise ValueError(f"Unexpected metric evidence condition: {condition_id}")
        spec = expected[condition_id]
        if condition.get("units") != spec["units"]:
            raise ValueError(f"Metric evidence condition units drifted: {condition_id}")
        value = require_finite_number(condition.get("value"), label=f"{condition_id} condition value")
        if value < spec["minimum"] or value > spec["maximum"]:
            raise ValueError(f"Metric evidence condition is outside the spec: {condition_id}")
        observed[condition_id] = condition
    if set(observed) != set(expected):
        raise ValueError(f"Metric evidence required condition is missing: {rule['metric_id']}")
    if payload != sorted(payload, key=lambda item: item["condition_id"]):
        raise ValueError("Metric evidence conditions are not canonical")


def _verify_uncertainty(payload: Any, *, rule: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or set(payload) != {
        "kind",
        "value",
        "units",
        "confidence_level",
    }:
        raise ValueError(f"Metric evidence uncertainty is malformed: {rule['metric_id']}")
    if payload.get("kind") != rule["uncertainty_mode"]:
        raise ValueError(f"Metric evidence uncertainty kind drifted: {rule['metric_id']}")
    if payload.get("units") != rule["units"]:
        raise ValueError(f"Metric evidence uncertainty units drifted: {rule['metric_id']}")
    value = require_finite_number(payload.get("value"), label="metric uncertainty")
    if value < 0.0:
        raise ValueError("Metric evidence uncertainty must be nonnegative")
    confidence = require_finite_number(payload.get("confidence_level"), label="confidence level")
    if confidence <= 0.0 or confidence > 1.0:
        raise ValueError("Metric evidence confidence level must be in (0, 1]")


def _generate_metric_result(
    rule: dict[str, Any],
    evidence: dict[str, Any] | None,
    qualification_input: dict[str, Any],
) -> dict[str, Any]:
    del qualification_input
    if evidence is None:
        return _not_run_result(rule)
    aggregate = max(float(sample["value"]) for sample in evidence["samples"])
    uncertainty = float(evidence["uncertainty"]["value"])
    decision_value = aggregate + uncertainty
    if not math.isfinite(decision_value):
        raise ValueError(f"Qualification decision value is non-finite: {rule['metric_id']}")
    tolerance_passed = decision_value <= float(rule["tolerance"]["max_value"])
    reasons = []
    if evidence["evidence_mode"] not in rule["required_evidence_modes"]:
        reasons.append("EVIDENCE_MODE_NOT_AUTHORIZED")
    if evidence["provenance_class"] not in rule["allowed_provenance_classes"]:
        reasons.append("PROVENANCE_NOT_AUTHORIZED")
    if not tolerance_passed:
        reasons.append("TOLERANCE_EXCEEDED")
    if not tolerance_passed:
        qualification_status = "fail"
    elif reasons:
        qualification_status = "withheld"
    else:
        qualification_status = "pass"
    return {
        "metric_id": rule["metric_id"],
        "units": rule["units"],
        "aggregation": rule["aggregation"],
        "aggregate_value": aggregate,
        "uncertainty": json.loads(json.dumps(evidence["uncertainty"])),
        "decision_value": decision_value,
        "tolerance": json.loads(json.dumps(rule["tolerance"])),
        "tolerance_status": "pass" if tolerance_passed else "fail",
        "qualification_status": qualification_status,
        "reason_codes": sorted(reasons),
        "sample_count": len(evidence["samples"]),
        "held_out_trajectory_ids": list(evidence["held_out_trajectory_ids"]),
        "evidence_mode": evidence["evidence_mode"],
        "provenance_class": evidence["provenance_class"],
        "evidence_identity_sha256": evidence["identity_sha256"],
    }


def _independently_recompute_metric(
    rule: dict[str, Any],
    evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    if evidence is None:
        return _not_run_result(rule)
    values = [require_finite_number(item["value"], label="independent metric sample") for item in evidence["samples"]]
    observed_maximum = max(values)
    absolute_bound = require_finite_number(
        evidence["uncertainty"]["value"],
        label="independent uncertainty",
    )
    conservative_upper = observed_maximum + absolute_bound
    if not math.isfinite(conservative_upper):
        raise ValueError("Independent qualification recomputation produced a non-finite value")
    within = conservative_upper <= require_finite_number(
        rule["tolerance"]["max_value"],
        label="independent tolerance",
    )
    reason_codes: set[str] = set()
    if evidence["evidence_mode"] not in set(rule["required_evidence_modes"]):
        reason_codes.add("EVIDENCE_MODE_NOT_AUTHORIZED")
    if evidence["provenance_class"] not in set(rule["allowed_provenance_classes"]):
        reason_codes.add("PROVENANCE_NOT_AUTHORIZED")
    if not within:
        reason_codes.add("TOLERANCE_EXCEEDED")
    status = "fail" if not within else ("withheld" if reason_codes else "pass")
    return {
        "metric_id": rule["metric_id"],
        "units": rule["units"],
        "aggregation": "maximum",
        "aggregate_value": observed_maximum,
        "uncertainty": json.loads(json.dumps(evidence["uncertainty"])),
        "decision_value": conservative_upper,
        "tolerance": json.loads(json.dumps(rule["tolerance"])),
        "tolerance_status": "pass" if within else "fail",
        "qualification_status": status,
        "reason_codes": sorted(reason_codes),
        "sample_count": len(values),
        "held_out_trajectory_ids": sorted({item["trajectory_id"] for item in evidence["samples"]}),
        "evidence_mode": evidence["evidence_mode"],
        "provenance_class": evidence["provenance_class"],
        "evidence_identity_sha256": evidence["identity_sha256"],
    }


def _not_run_result(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric_id": rule["metric_id"],
        "units": rule["units"],
        "aggregation": rule["aggregation"],
        "aggregate_value": None,
        "uncertainty": None,
        "decision_value": None,
        "tolerance": json.loads(json.dumps(rule["tolerance"])),
        "tolerance_status": "not_run",
        "qualification_status": "not_run",
        "reason_codes": ["METRIC_NOT_RUN"],
        "sample_count": 0,
        "held_out_trajectory_ids": [],
        "evidence_mode": "not_run",
        "provenance_class": "not_run",
        "evidence_identity_sha256": None,
    }


def _generate_summary(
    metrics: list[dict[str, Any]],
    *,
    spec: dict[str, Any],
    requested_proof_state: str,
) -> dict[str, Any]:
    required = sorted(
        rule["metric_id"]
        for rule in spec["metric_rules"]
        if requested_proof_state in rule["required_for_proof_states"]
    )
    index = {item["metric_id"]: item for item in metrics}
    return {
        "required_metric_ids": required,
        "passed_metric_ids": [metric_id for metric_id in required if index[metric_id]["qualification_status"] == "pass"],
        "failed_metric_ids": [metric_id for metric_id in required if index[metric_id]["qualification_status"] == "fail"],
        "withheld_metric_ids": [metric_id for metric_id in required if index[metric_id]["qualification_status"] == "withheld"],
        "not_run_metric_ids": [metric_id for metric_id in required if index[metric_id]["qualification_status"] == "not_run"],
        "all_required_metrics_passed": bool(required)
        and all(index[metric_id]["qualification_status"] == "pass" for metric_id in required),
    }


def _independently_recompute_summary(
    metrics: list[dict[str, Any]],
    *,
    spec: dict[str, Any],
    requested_proof_state: str,
) -> dict[str, Any]:
    required_ids = sorted(
        item["metric_id"]
        for item in spec["metric_rules"]
        if requested_proof_state in set(item["required_for_proof_states"])
    )
    results = {item["metric_id"]: item["qualification_status"] for item in metrics}
    buckets = {
        status: [metric_id for metric_id in required_ids if results[metric_id] == status]
        for status in ("pass", "fail", "withheld", "not_run")
    }
    return {
        "required_metric_ids": required_ids,
        "passed_metric_ids": buckets["pass"],
        "failed_metric_ids": buckets["fail"],
        "withheld_metric_ids": buckets["withheld"],
        "not_run_metric_ids": buckets["not_run"],
        "all_required_metrics_passed": bool(required_ids) and len(buckets["pass"]) == len(required_ids),
    }


def _generate_capabilities(
    metrics: list[dict[str, Any]],
    *,
    spec: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, bool]:
    index = {item["metric_id"]: item for item in metrics}
    simulation_required = [
        rule["metric_id"]
        for rule in spec["metric_rules"]
        if "simulation_only" in rule["required_for_proof_states"]
    ]
    physical_required = [
        rule["metric_id"]
        for rule in spec["metric_rules"]
        if "physical_qualified" in rule["required_for_proof_states"]
    ]
    return {
        "twin_qualification_computation_valid": True,
        "required_simulation_properties_available": bool(simulation_required)
        and all(index[item]["qualification_status"] == "pass" for item in simulation_required),
        "held_out_twin_metrics_passed": profile.get("proof_state") == "physical_qualified"
        and bool(physical_required)
        and all(index[item]["qualification_status"] == "pass" for item in physical_required),
    }


def _independently_recompute_capabilities(
    metrics: list[dict[str, Any]],
    *,
    spec: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, bool]:
    statuses = {item["metric_id"]: item["qualification_status"] for item in metrics}
    by_proof = {
        proof_state: [
            rule["metric_id"]
            for rule in spec["metric_rules"]
            if proof_state in set(rule["required_for_proof_states"])
        ]
        for proof_state in _PROOF_STATES
    }
    simulation = by_proof["simulation_only"]
    physical = by_proof["physical_qualified"]
    return {
        "twin_qualification_computation_valid": True,
        "required_simulation_properties_available": bool(simulation)
        and not any(statuses[item] != "pass" for item in simulation),
        "held_out_twin_metrics_passed": profile.get("proof_state") == "physical_qualified"
        and bool(physical)
        and not any(statuses[item] != "pass" for item in physical),
    }


def _metric_rule_index(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["metric_id"]: item for item in spec["metric_rules"]}


def _validate_validity(
    payload: Any,
    *,
    evaluation_time: datetime,
    label: str,
    maximum_age_seconds: int | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "observed_at",
        "valid_from",
        "valid_until",
        "max_age_seconds",
    }:
        raise ValueError(f"{label} validity fields are malformed")
    observed = _parse_timestamp(payload["observed_at"], label=f"{label} observed_at")
    valid_from = _parse_timestamp(payload["valid_from"], label=f"{label} valid_from")
    valid_until = _parse_timestamp(payload["valid_until"], label=f"{label} valid_until")
    max_age = payload.get("max_age_seconds")
    if isinstance(max_age, bool) or not isinstance(max_age, int) or max_age <= 0:
        raise ValueError(f"{label} max_age_seconds must be a positive integer")
    if maximum_age_seconds is not None and max_age > maximum_age_seconds:
        raise ValueError(f"{label} max_age_seconds exceeds the code-pinned maximum")
    if valid_until <= valid_from:
        raise ValueError(f"{label} validity interval is empty or reversed")
    if maximum_age_seconds is not None and (valid_until - valid_from).total_seconds() > maximum_age_seconds:
        raise ValueError(f"{label} validity interval exceeds the code-pinned maximum")
    if observed < valid_from or observed > valid_until:
        raise ValueError(f"{label} observed_at falls outside validity")
    if evaluation_time < valid_from or evaluation_time < observed:
        raise ValueError(f"{label} is not yet valid")
    if evaluation_time > valid_until:
        raise ValueError(f"{label} expired before evaluation")
    if (evaluation_time - observed).total_seconds() > max_age:
        raise ValueError(f"{label} evidence is stale")
    return {
        "observed_at": observed,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "max_age_seconds": max_age,
    }


def _issuer(authority_id: str) -> dict[str, str]:
    return {
        "authority_id": authority_id,
        "authority_identity_sha256": hashlib.sha256(
            f"scenesmith.qualification.authority.identity.v1:{authority_id}".encode("utf-8")
        ).hexdigest(),
    }


def _load_artifact_ref(
    reference: Any,
    *,
    repo_root: Path,
    label: str,
) -> dict[str, Any]:
    if not isinstance(reference, dict):
        raise ValueError(f"{label} linkage is missing")
    path_value = reference.get("path")
    path = _validated_ref_path(path_value, repo_root=repo_root, label=label)
    payload = load_strict_json(path)
    expected = artifact_ref(
        path=Path(str(path_value)),
        payload=payload,
        repo_root=repo_root,
    )
    verify_artifact_ref(reference, expected, label=label)
    return payload


def _validated_ref_path(value: Any, *, repo_root: Path, label: str) -> Path:
    path_text = require_nonblank(value, label=f"{label} path")
    path = Path(path_text)
    if path.is_absolute() or path.as_posix() != path_text or ".." in path.parts or "." in path.parts:
        raise ValueError(f"{label} path must be a canonical repo-relative path")
    resolved_root = repo_root.resolve()
    resolved = (resolved_root / path).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} path escapes the repository") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} path does not name a file")
    return resolved


def _relative_path(repo_root: Path, path: Path) -> Path:
    resolved_root = repo_root.resolve()
    resolved = path.resolve() if path.is_absolute() else (resolved_root / path).resolve()
    try:
        relative = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("Qualification artifact path must remain inside the repository") from exc
    if ".." in relative.parts or "." in relative.parts:
        raise ValueError("Qualification artifact path is not canonical")
    return relative


def _resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _composition_mode(value: Any) -> str:
    if value not in _COMPOSITION_MODES:
        raise ValueError(f"Unknown qualification composition mode: {value}")
    return str(value)


def _canonical_timestamp(value: Any, *, label: str) -> str:
    parsed = _parse_timestamp(value, label=label)
    return parsed.isoformat(timespec="seconds")


def _parse_timestamp(value: Any, *, label: str) -> datetime:
    text = require_nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    if parsed.isoformat(timespec="seconds") != text:
        raise ValueError(f"{label} must be canonical to whole seconds")
    return parsed


def _find_forbidden_fields(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in _FORBIDDEN_CALLER_FIELDS:
                found.add(key)
            found.update(_find_forbidden_fields(value))
    elif isinstance(payload, list):
        for value in payload:
            found.update(_find_forbidden_fields(value))
    return found

"""Pure fail-closed Gate B checkpoint-retention contract for T20.36b."""

from __future__ import annotations

import hashlib
import math
import re

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_36b_gate_b_retention_spec.json")
DECISION_PATH = Path(
    "configurations/robot_lab/t20_36b_gate_b_retention_fixture_decision.json"
)
SOURCE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_result.json"
)
SOURCE_RUN_PATH = Path(
    "outputs/robot_lab/t20_35x_physical_gate_joint_weighted_run_001/run_summary.json"
)
CAMPAIGN_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36_bounded_corrected_coverage_result.json"
)
CAMPAIGN_RUN_PATH = Path(
    "outputs/robot_lab/t20_36_bounded_corrected_coverage_run_001/run_summary.json"
)
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_36a_objective_interference_audit.json"
)
SPEC_SCHEMA_VERSION = "scenesmith.t20_36b_gate_b_retention_spec.v1"
EVIDENCE_SCHEMA_VERSION = "scenesmith.t20_36b_checkpoint_evidence.v1"
DECISION_SCHEMA_VERSION = "scenesmith.t20_36b_gate_b_retention_decision.v1"
TASK_ID = "T20.36b"
INFERENCE_SEEDS = tuple(range(20260721, 20260726))
MAXIMUM_OBJECTIVE_RATIO = 0.10
MAXIMUM_ACTION_ERROR_RAD = 0.05
EXPECTED_SOURCE_RESULT_IDENTITY = (
    "e79dacff684dac507295d839527fb15d4eced8fa9c83973f5534bdf7e99ec6cd"
)
EXPECTED_SOURCE_RUN_IDENTITY = (
    "b5cc16ef53a415a7e0a4b8519332a4197201544fc9ebe5186565562e048c054b"
)
EXPECTED_CAMPAIGN_RESULT_IDENTITY = (
    "02b543be829220f89e0bfe2d16b042507127f488f73a9de0149442e89bc3a638"
)
EXPECTED_CAMPAIGN_RUN_IDENTITY = (
    "88daae0d8239239d064227b9e9561a01b7bf634d849dc4e61237b1713462410e"
)
EXPECTED_AUDIT_IDENTITY = (
    "339a72290b302a2751be02bbccc07ac9441e3b5db65f023741ce38ba190b73aa"
)
EXPECTED_INPUT_FILE_SHA256 = {
    "source_result": "981082fd51f15b3067af6e1a4724d46b5941f3016b8212dc9af385c3167501e4",
    "source_run": "b05fd6c68ea13f2e140861249f16b42a95f517d1b9ab24e36b6995c954a8f02d",
    "campaign_result": "7927aaafa7d7a403487ac228b8cfe7e058b3414ac0a2a6a56993d77b17ba8ee8",
    "campaign_run": "19010302db1e7f41cc6a089914fa7260030eaa57498bea76737a03fb9862e830",
    "audit": "526f88fd114715bd210a2b1719db4d58ce9fd6e7afa79a7cddf1c7a2d856a707",
}
_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def build_checkpoint_evidence(
    *,
    checkpoint_label: str,
    optimizer_update_count: int,
    checkpoint_identity_sha256: str,
    standard_objective_ratio: float,
    decoded_action_maximum_by_seed: list[dict[str, Any]],
    tracked_proxy_metrics: dict[str, float],
    provenance_identity_sha256: dict[str, str] | None = None,
) -> dict[str, Any]:
    _label(checkpoint_label)
    if (
        isinstance(optimizer_update_count, bool)
        or not isinstance(optimizer_update_count, int)
        or optimizer_update_count < 0
    ):
        raise ValueError("T20.36b optimizer update count is invalid")
    _sha(checkpoint_identity_sha256, "checkpoint identity")
    standard_ratio = _nonnegative(
        standard_objective_ratio, "standard objective ratio"
    )
    decoded = _decoded_rows(decoded_action_maximum_by_seed)
    if not isinstance(tracked_proxy_metrics, dict) or any(
        not isinstance(key, str) or not key
        for key in tracked_proxy_metrics
    ):
        raise ValueError("T20.36b tracked proxy metrics are invalid")
    proxies = {
        key: _nonnegative(value, f"tracked proxy metric {key}")
        for key, value in tracked_proxy_metrics.items()
    }
    provenance = dict(provenance_identity_sha256 or {})
    for label, identity in provenance.items():
        if not isinstance(label, str) or not label:
            raise ValueError("T20.36b provenance label is invalid")
        _sha(identity, f"provenance {label}")
    return sign_payload(
        {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "checkpoint_label": checkpoint_label,
            "optimizer_update_count": optimizer_update_count,
            "checkpoint_identity_sha256": checkpoint_identity_sha256,
            "standard_objective_ratio": standard_ratio,
            "decoded_action_maximum_by_seed": decoded,
            "tracked_proxy_metrics": proxies,
            "provenance_identity_sha256": provenance,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def build_retention_spec(
    *,
    evidence_rows: list[dict[str, Any]],
    source_checkpoint_label: str,
    historical_fixture_only: bool,
    schedule_registration_boundary_sha256: str | None,
    fixture_source_identities: dict[str, str] | None = None,
) -> dict[str, Any]:
    rows = _validated_evidence_rows(evidence_rows)
    _label(source_checkpoint_label)
    if not isinstance(historical_fixture_only, bool):
        raise ValueError("T20.36b historical-fixture flag is invalid")
    if historical_fixture_only:
        if schedule_registration_boundary_sha256 is not None:
            raise ValueError("T20.36b historical fixture cannot claim pre-registration")
    else:
        _sha(
            schedule_registration_boundary_sha256,
            "schedule registration boundary",
        )
    if len(rows) < 2 or rows[0]["checkpoint_label"] != source_checkpoint_label:
        raise ValueError("T20.36b schedule must begin with the source checkpoint")
    if rows[0]["optimizer_update_count"] != 0:
        raise ValueError("T20.36b source checkpoint must be update zero")
    labels = [row["checkpoint_label"] for row in rows]
    checkpoint_ids = [row["checkpoint_identity_sha256"] for row in rows]
    evidence_ids = [row["identity_sha256"] for row in rows]
    updates = [row["optimizer_update_count"] for row in rows]
    if (
        len(set(labels)) != len(labels)
        or len(set(checkpoint_ids)) != len(checkpoint_ids)
        or len(set(evidence_ids)) != len(evidence_ids)
        or any(after <= before for before, after in zip(updates, updates[1:]))
    ):
        raise ValueError("T20.36b schedule is duplicated or unordered")
    fixture_sources = dict(fixture_source_identities or {})
    for label, identity in fixture_sources.items():
        if not isinstance(label, str) or not label:
            raise ValueError("T20.36b fixture source label is invalid")
        _sha(identity, f"fixture source {label}")
    return sign_payload(
        {
            "schema_version": SPEC_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "scope": "pure_fail_closed_gate_b_checkpoint_retention_contract",
            "source_checkpoint_label": source_checkpoint_label,
            "ordered_checkpoint_schedule": [
                {
                    "checkpoint_label": row["checkpoint_label"],
                    "optimizer_update_count": row["optimizer_update_count"],
                    "checkpoint_identity_sha256": row[
                        "checkpoint_identity_sha256"
                    ],
                    "evaluation_evidence_identity_sha256": row[
                        "identity_sha256"
                    ],
                }
                for row in rows
            ],
            "inference_seeds": list(INFERENCE_SEEDS),
            "maximum_standard_objective_ratio": MAXIMUM_OBJECTIVE_RATIO,
            "maximum_action_error_rad": MAXIMUM_ACTION_ERROR_RAD,
            "all_inference_seeds_must_pass": True,
            "selection_rule": "latest_predeclared_post_source_gate_b_pass",
            "proxy_metric_substitution_allowed": False,
            "historical_fixture_only": historical_fixture_only,
            "schedule_registration_boundary_sha256": schedule_registration_boundary_sha256,
            "future_schedule_requires_pre_optimizer_remote_preservation": True,
            "fixture_source_identities": fixture_sources,
            "checkpoint_read": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "campaign_authorized": False,
            "gate_b_threshold_changed": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def build_retention_decision(
    *, spec: dict[str, Any], evidence_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    _validate_spec(spec)
    rows = _validated_evidence_rows(evidence_rows)
    schedule = spec["ordered_checkpoint_schedule"]
    if len(rows) != len(schedule):
        raise ValueError("T20.36b retention evidence coverage drifted")
    checkpoint_decisions = []
    for planned, evidence in zip(schedule, rows, strict=True):
        if (
            evidence["checkpoint_label"] != planned["checkpoint_label"]
            or evidence["optimizer_update_count"]
            != planned["optimizer_update_count"]
            or evidence["checkpoint_identity_sha256"]
            != planned["checkpoint_identity_sha256"]
            or evidence["identity_sha256"]
            != planned["evaluation_evidence_identity_sha256"]
        ):
            raise ValueError("T20.36b retention evidence is stale or reordered")
        objective_pass = (
            evidence["standard_objective_ratio"]
            <= spec["maximum_standard_objective_ratio"]
        )
        action_pass = all(
            row["maximum_absolute_error_rad"]
            <= spec["maximum_action_error_rad"]
            for row in evidence["decoded_action_maximum_by_seed"]
        )
        checkpoint_decisions.append(
            {
                "checkpoint_label": evidence["checkpoint_label"],
                "optimizer_update_count": evidence["optimizer_update_count"],
                "checkpoint_identity_sha256": evidence[
                    "checkpoint_identity_sha256"
                ],
                "evaluation_evidence_identity_sha256": evidence[
                    "identity_sha256"
                ],
                "standard_objective_ratio": evidence[
                    "standard_objective_ratio"
                ],
                "objective_ratio_within_threshold": objective_pass,
                "decoded_action_maximum_by_seed": evidence[
                    "decoded_action_maximum_by_seed"
                ],
                "all_decoded_seeds_within_threshold": action_pass,
                "gate_b_retained": objective_pass and action_pass,
                "tracked_proxy_metrics": evidence["tracked_proxy_metrics"],
                "proxy_metrics_used_for_gate_b": False,
            }
        )
    retained = [
        row["checkpoint_label"]
        for row in checkpoint_decisions
        if row["gate_b_retained"]
    ]
    source_label = spec["source_checkpoint_label"]
    post_source = [label for label in retained if label != source_label]
    rollback = source_label if source_label in retained else None
    selected = post_source[-1] if post_source else None
    if selected is not None:
        decision = "post_source_checkpoint_retains_gate_b_candidate_available"
    elif rollback is not None:
        decision = "only_source_checkpoint_retains_gate_b_no_coverage_candidate"
    else:
        decision = "no_checkpoint_retains_gate_b"
    return sign_payload(
        {
            "schema_version": DECISION_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "retention_spec_identity_sha256": spec["identity_sha256"],
            "historical_fixture_only": spec["historical_fixture_only"],
            "schedule_registration_boundary_sha256": spec[
                "schedule_registration_boundary_sha256"
            ],
            "checkpoint_decisions": checkpoint_decisions,
            "retained_checkpoint_labels": retained,
            "post_source_retained_checkpoint_labels": post_source,
            "rollback_checkpoint_label": rollback,
            "selected_coverage_checkpoint_label": selected,
            "decision": decision,
            "contract_valid": True,
            "proxy_metrics_ignored_for_gate_b": True,
            "checkpoint_read": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "optimizer_training_authorized": False,
            "campaign_authorized": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_retention_decision(
    payload: dict[str, Any], *, spec: dict[str, Any], evidence_rows: list[dict[str, Any]]
) -> None:
    verify_signed_payload(payload, label="T20.36b retention decision")
    expected = build_retention_decision(spec=spec, evidence_rows=evidence_rows)
    if payload != expected:
        raise ValueError("T20.36b retention decision drifted")


def build_fixture_artifacts(
    *, repo_root: Path = REPO_ROOT
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    sources = _load_fixture_sources(repo_root=repo_root)
    source_result = sources["source_result"]
    source_run = sources["source_run"]
    campaign_result = sources["campaign_result"]
    campaign_run = sources["campaign_run"]
    audit = sources["audit"]
    source_evidence = build_checkpoint_evidence(
        checkpoint_label="t20_35x_source",
        optimizer_update_count=0,
        checkpoint_identity_sha256=source_run["checkpoint_identity_sha256"],
        standard_objective_ratio=source_result[
            "final_to_source_gate_baseline_objective_ratio"
        ],
        decoded_action_maximum_by_seed=[
            {
                "inference_seed": row["inference_seed"],
                "maximum_absolute_error_rad": row[
                    "maximum_absolute_error_rad"
                ],
            }
            for row in source_result["decoded_action_chunks"]
        ],
        tracked_proxy_metrics={
            "raw_correction_objective_mean": source_result[
                "final_raw_correction_objective_mean"
            ],
            "joint_weighted_correction_objective_mean": source_result[
                "final_joint_weighted_correction_objective_mean"
            ],
        },
        provenance_identity_sha256={
            "result": source_result["identity_sha256"],
            "run": source_run["identity_sha256"],
        },
    )
    campaign_evidence = build_checkpoint_evidence(
        checkpoint_label="t20_36_post_coverage",
        optimizer_update_count=campaign_result["optimizer_update_count"],
        checkpoint_identity_sha256=campaign_run["checkpoint_identity_sha256"],
        standard_objective_ratio=campaign_run[
            "final_to_source_gate_baseline_objective_ratio"
        ],
        decoded_action_maximum_by_seed=[
            {
                "inference_seed": row["inference_seed"],
                "maximum_absolute_error_rad": row[
                    "maximum_absolute_error_rad"
                ],
            }
            for row in campaign_run["decoded_action_chunks"]
        ],
        tracked_proxy_metrics={
            "raw_correction_objective_mean": campaign_run[
                "final_raw_correction_objective_mean"
            ],
            "joint_weighted_correction_objective_mean": campaign_run[
                "final_joint_weighted_correction_objective_mean"
            ],
        },
        provenance_identity_sha256={
            "result": campaign_result["identity_sha256"],
            "run": campaign_run["identity_sha256"],
            "interference_audit": audit["identity_sha256"],
        },
    )
    evidence = [source_evidence, campaign_evidence]
    spec = build_retention_spec(
        evidence_rows=evidence,
        source_checkpoint_label="t20_35x_source",
        historical_fixture_only=True,
        schedule_registration_boundary_sha256=None,
        fixture_source_identities={
            "source_result": source_result["identity_sha256"],
            "source_run": source_run["identity_sha256"],
            "campaign_result": campaign_result["identity_sha256"],
            "campaign_run": campaign_run["identity_sha256"],
            "interference_audit": audit["identity_sha256"],
        },
    )
    decision = build_retention_decision(spec=spec, evidence_rows=evidence)
    return spec, evidence, decision


def write_fixture_artifacts(*, repo_root: Path = REPO_ROOT) -> tuple[dict, dict]:
    root = Path(repo_root)
    spec, _, decision = build_fixture_artifacts(repo_root=root)
    dump_canonical_json(root / SPEC_PATH, spec)
    dump_canonical_json(root / DECISION_PATH, decision)
    return spec, decision


def verify_fixture_artifact_files(
    *, repo_root: Path = REPO_ROOT
) -> tuple[dict, dict]:
    root = Path(repo_root)
    expected_spec, evidence, expected_decision = build_fixture_artifacts(
        repo_root=root
    )
    spec = load_strict_json(root / SPEC_PATH)
    decision = load_strict_json(root / DECISION_PATH)
    if spec != expected_spec:
        raise ValueError("T20.36b retention spec drifted")
    verify_retention_decision(decision, spec=spec, evidence_rows=evidence)
    if decision != expected_decision:
        raise ValueError("T20.36b fixture decision drifted")
    return spec, decision


def _load_fixture_sources(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root)
    paths = {
        "source_result": root / SOURCE_RESULT_PATH,
        "source_run": root / SOURCE_RUN_PATH,
        "campaign_result": root / CAMPAIGN_RESULT_PATH,
        "campaign_run": root / CAMPAIGN_RUN_PATH,
        "audit": root / AUDIT_PATH,
    }
    hashes = {
        label: hashlib.sha256(path.read_bytes()).hexdigest()
        for label, path in paths.items()
    }
    if hashes != EXPECTED_INPUT_FILE_SHA256:
        raise ValueError("T20.36b fixture input file identity drifted")
    sources = {label: load_strict_json(path) for label, path in paths.items()}
    for label, payload in sources.items():
        verify_signed_payload(payload, label=f"T20.36b fixture {label}")
    if (
        sources["source_result"].get("identity_sha256")
        != EXPECTED_SOURCE_RESULT_IDENTITY
        or sources["source_run"].get("identity_sha256")
        != EXPECTED_SOURCE_RUN_IDENTITY
        or sources["campaign_result"].get("identity_sha256")
        != EXPECTED_CAMPAIGN_RESULT_IDENTITY
        or sources["campaign_run"].get("identity_sha256")
        != EXPECTED_CAMPAIGN_RUN_IDENTITY
        or sources["audit"].get("identity_sha256") != EXPECTED_AUDIT_IDENTITY
        or sources["source_result"].get("run_identity_sha256")
        != sources["source_run"]["identity_sha256"]
        or sources["campaign_result"].get("run_identity_sha256")
        != sources["campaign_run"]["identity_sha256"]
        or sources["audit"].get("source_result_identity_sha256")
        != sources["source_result"]["identity_sha256"]
        or sources["audit"].get("campaign_result_identity_sha256")
        != sources["campaign_result"]["identity_sha256"]
    ):
        raise ValueError("T20.36b fixture source lineage drifted")
    return sources


def _validate_spec(spec: dict[str, Any]) -> None:
    verify_signed_payload(spec, label="T20.36b retention spec")
    if (
        spec.get("schema_version") != SPEC_SCHEMA_VERSION
        or spec.get("task_id") != TASK_ID
        or spec.get("inference_seeds") != list(INFERENCE_SEEDS)
        or spec.get("maximum_standard_objective_ratio")
        != MAXIMUM_OBJECTIVE_RATIO
        or spec.get("maximum_action_error_rad") != MAXIMUM_ACTION_ERROR_RAD
        or spec.get("all_inference_seeds_must_pass") is not True
        or spec.get("selection_rule")
        != "latest_predeclared_post_source_gate_b_pass"
        or spec.get("proxy_metric_substitution_allowed") is not False
        or spec.get("future_schedule_requires_pre_optimizer_remote_preservation")
        is not True
    ):
        raise ValueError("T20.36b retention spec contract drifted")
    schedule = spec.get("ordered_checkpoint_schedule")
    if not isinstance(schedule, list) or len(schedule) < 2:
        raise ValueError("T20.36b retention schedule is incomplete")
    labels = []
    updates = []
    for row in schedule:
        if not isinstance(row, dict) or set(row) != {
            "checkpoint_label",
            "optimizer_update_count",
            "checkpoint_identity_sha256",
            "evaluation_evidence_identity_sha256",
        }:
            raise ValueError("T20.36b retention schedule row is invalid")
        _label(row["checkpoint_label"])
        _sha(row["checkpoint_identity_sha256"], "scheduled checkpoint")
        _sha(row["evaluation_evidence_identity_sha256"], "scheduled evidence")
        if (
            isinstance(row["optimizer_update_count"], bool)
            or not isinstance(row["optimizer_update_count"], int)
            or row["optimizer_update_count"] < 0
        ):
            raise ValueError("T20.36b scheduled update count is invalid")
        labels.append(row["checkpoint_label"])
        updates.append(row["optimizer_update_count"])
    if (
        labels[0] != spec.get("source_checkpoint_label")
        or updates[0] != 0
        or len(set(labels)) != len(labels)
        or any(after <= before for before, after in zip(updates, updates[1:]))
    ):
        raise ValueError("T20.36b retention schedule order drifted")
    historical = spec.get("historical_fixture_only")
    boundary = spec.get("schedule_registration_boundary_sha256")
    if historical is True:
        if boundary is not None:
            raise ValueError("T20.36b historical schedule claims registration")
    elif historical is False:
        _sha(boundary, "schedule registration boundary")
    else:
        raise ValueError("T20.36b historical-fixture flag drifted")
    for field in (
        "checkpoint_read",
        "model_loaded",
        "model_inference",
        "optimizer_created",
        "optimizer_training",
        "campaign_authorized",
        "gate_b_threshold_changed",
        "closed_loop_rollout",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
    ):
        if spec.get(field) is not False:
            raise ValueError("T20.36b retention spec authority drifted")


def _validated_evidence_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("T20.36b checkpoint evidence must be a list")
    output = []
    for row in rows:
        verify_signed_payload(row, label="T20.36b checkpoint evidence")
        if (
            row.get("schema_version") != EVIDENCE_SCHEMA_VERSION
            or row.get("task_id") != TASK_ID
        ):
            raise ValueError("T20.36b checkpoint evidence contract drifted")
        _label(row.get("checkpoint_label"))
        _sha(row.get("checkpoint_identity_sha256"), "checkpoint identity")
        if (
            isinstance(row.get("optimizer_update_count"), bool)
            or not isinstance(row.get("optimizer_update_count"), int)
            or row["optimizer_update_count"] < 0
        ):
            raise ValueError("T20.36b checkpoint evidence update is invalid")
        _nonnegative(row.get("standard_objective_ratio"), "standard ratio")
        if row.get("decoded_action_maximum_by_seed") != _decoded_rows(
            row.get("decoded_action_maximum_by_seed")
        ):
            raise ValueError("T20.36b decoded action evidence drifted")
        proxies = row.get("tracked_proxy_metrics")
        if not isinstance(proxies, dict):
            raise ValueError("T20.36b tracked proxy metrics drifted")
        for label, value in proxies.items():
            if not isinstance(label, str) or not label:
                raise ValueError("T20.36b tracked proxy label drifted")
            _nonnegative(value, f"tracked proxy {label}")
        provenance = row.get("provenance_identity_sha256")
        if not isinstance(provenance, dict):
            raise ValueError("T20.36b provenance drifted")
        for label, identity in provenance.items():
            if not isinstance(label, str) or not label:
                raise ValueError("T20.36b provenance label drifted")
            _sha(identity, f"provenance {label}")
        for field in (
            "physical_actuation",
            "external_compute_started",
            "brev_compute_started",
        ):
            if row.get(field) is not False:
                raise ValueError("T20.36b checkpoint evidence authority drifted")
        output.append(row)
    return output


def _decoded_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(INFERENCE_SEEDS):
        raise ValueError("T20.36b decoded seed coverage drifted")
    output = []
    for expected_seed, row in zip(INFERENCE_SEEDS, value, strict=True):
        if not isinstance(row, dict) or set(row) != {
            "inference_seed",
            "maximum_absolute_error_rad",
        }:
            raise ValueError("T20.36b decoded seed row is invalid")
        if row.get("inference_seed") != expected_seed:
            raise ValueError("T20.36b decoded seed order drifted")
        output.append(
            {
                "inference_seed": expected_seed,
                "maximum_absolute_error_rad": _nonnegative(
                    row.get("maximum_absolute_error_rad"),
                    "decoded maximum action error",
                ),
            }
        )
    return output


def _label(value: Any) -> None:
    if not isinstance(value, str) or _LABEL_PATTERN.fullmatch(value) is None:
        raise ValueError("T20.36b checkpoint label is invalid")


def _sha(value: Any, label: str) -> None:
    if not isinstance(value, str) or _SHA_PATTERN.fullmatch(value) is None:
        raise ValueError(f"T20.36b {label} is not a SHA-256")


def _nonnegative(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36b {label} must be finite")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"T20.36b {label} must be finite and nonnegative")
    return number

"""Versioned, fail-closed counterexample archive contracts."""

from __future__ import annotations

import copy
import hashlib
import json

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_19_discrete_recovery_ensemble import (
    verify_cell_manifest,
    verify_scorecard,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CELL_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_19_discrete_recovery_cells.json"
)
SCORECARD_GATE_PATH = Path(
    "configurations/robot_lab/t20_19_discrete_recovery_scorecard_gate.json"
)
RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_39_counterexample_receipt_0001.json"
)
INDEX_PATH = Path("configurations/robot_lab/t20_39_counterexample_archive_index.json")
RECEIPT_SCHEMA_VERSION = "scenesmith.counterexample_receipt.v1"
INDEX_SCHEMA_VERSION = "scenesmith.counterexample_archive_index.v1"
EXPECTED_MANIFEST_IDENTITY = (
    "2842bb35296e1a5b1504ba07932ddb425cff4f1a68115249a26d259ebf708688"
)
EXPECTED_GATE_IDENTITY = (
    "1205e336a81b68b650013572bd96ac8f6d452a5262ab924966aa14b7fa5e10c6"
)
LIFECYCLE_STATES = ("active", "superseded", "retired", "invalid")
LIFECYCLE_TRANSITIONS = {
    "active": ("superseded", "retired", "invalid"),
    "superseded": ("invalid",),
    "retired": ("invalid",),
    "invalid": (),
}
ROUTING_MATRIX = {
    "evidence_only": {
        "archive_eligible": True,
        "fixed_replay_eligible": False,
        "policy_regression_blame_allowed": False,
        "replay_gate_activation_allowed": False,
        "training_ingestion_eligible": False,
    },
    "fixed_regression_candidate": {
        "archive_eligible": True,
        "fixed_replay_eligible": True,
        "policy_regression_blame_allowed": False,
        "replay_gate_activation_allowed": False,
        "training_ingestion_eligible": False,
    },
    "policy_regression_candidate": {
        "archive_eligible": True,
        "fixed_replay_eligible": True,
        "policy_regression_blame_allowed": True,
        "replay_gate_activation_allowed": False,
        "training_ingestion_eligible": False,
    },
    "compiler_quarantine": {
        "archive_eligible": True,
        "fixed_replay_eligible": False,
        "policy_regression_blame_allowed": False,
        "replay_gate_activation_allowed": False,
        "training_ingestion_eligible": False,
    },
}
DUPLICATE_MUTABLE_FIELDS = {
    "identity_sha256",
    "archive_sequence",
    "counterexample_id",
    "lifecycle_state",
    "canonical_counterexample_id",
    "duplicate_of_counterexample_id",
}


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    manifest_path = root / CELL_MANIFEST_PATH
    gate_path = root / SCORECARD_GATE_PATH
    manifest = load_strict_json(manifest_path)
    gate = load_strict_json(gate_path)
    verify_cell_manifest(manifest)
    verify_signed_payload(gate, label="T20.39 source scorecard gate")
    verify_scorecard(gate["scorecard"], manifest)
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    gate_sha = hashlib.sha256(gate_path.read_bytes()).hexdigest()
    if (
        manifest.get("identity_sha256") != EXPECTED_MANIFEST_IDENTITY
        or gate.get("identity_sha256") != EXPECTED_GATE_IDENTITY
        or gate["cell_manifest_ref"].get("identity_sha256")
        != manifest["identity_sha256"]
        or gate["cell_manifest_ref"].get("file_sha256") != manifest_sha
        or gate["scorecard"].get("worst_cell_id") != "gripper_scale_high"
        or gate["scorecard"].get("worst_cell_terminal_outcome")
        != "lifted_without_strict_cycle"
        or gate["scorecard"].get("posterior_calibrated") is not False
    ):
        raise ValueError("T20.39 source binding drifted")
    return {
        "manifest": manifest,
        "gate": gate,
        "manifest_file_sha256": manifest_sha,
        "manifest_size_bytes": manifest_path.stat().st_size,
        "gate_file_sha256": gate_sha,
        "gate_size_bytes": gate_path.stat().st_size,
    }


def build_seed_receipt(*, sources: dict[str, Any]) -> dict[str, Any]:
    manifest = sources["manifest"]
    gate = sources["gate"]
    verify_cell_manifest(manifest)
    verify_scorecard(gate["scorecard"], manifest)
    cell = next(row for row in manifest["cells"] if row["cell_id"] == "gripper_scale_high")
    result = next(
        row
        for row in gate["scorecard"]["results"]
        if row["cell_id"] == "gripper_scale_high"
    )
    if (
        cell != {
            "cell_index": 11,
            "cell_id": "gripper_scale_high",
            "factor": "gripper_command_scale",
            "value": 1.05,
            "one_factor_only": True,
        }
        or result["simulation_semantic_strict_success"] is not False
        or result["first_trace_sha256"] != result["second_trace_sha256"]
        or gate["scorecard"]["worst_cell_id"] != cell["cell_id"]
    ):
        raise ValueError("T20.39 seed counterexample drifted")
    controller_owner = "source_bound_recovery_controller"
    task_scope = "anchor_grasp_strict_v2"
    object_scope = "analytic_turquoise_anchor_cousin_v1"
    semantic_core = {
        "provenance_class": "simulation_source_controller",
        "controller_owner": controller_owner,
        "capability_stage": "source_controller_boundary",
        "failure_class": "source_controller_boundary_negative",
        "task_scope": task_scope,
        "object_scope": object_scope,
        "source_manifest_identity_sha256": manifest["identity_sha256"],
        "source_scorecard_identity_sha256": gate["scorecard"]["identity_sha256"],
        "cell_id": cell["cell_id"],
        "factor": cell["factor"],
        "value": cell["value"],
        "trace_sha256": result["first_trace_sha256"],
        "terminal_outcome": result["terminal_outcome"],
        "simulation_semantic_strict_success": result[
            "simulation_semantic_strict_success"
        ],
        "strict_contact_frame_count": result["strict_contact_frame_count"],
        "maximum_anchor_lift_m": result["maximum_anchor_lift_m"],
    }
    fingerprint = hashlib.sha256(canonical_json_bytes(semantic_core)).hexdigest()
    return sign_payload(
        {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "task_id": "T20.39",
            "archive_sequence": 1,
            "counterexample_id": "cex-0001",
            "semantic_fingerprint_sha256": fingerprint,
            "semantic_core": semantic_core,
            "source_refs": {
                "cell_manifest": {
                    "path": CELL_MANIFEST_PATH.as_posix(),
                    "schema_version": manifest["schema_version"],
                    "identity_sha256": manifest["identity_sha256"],
                    "file_sha256": sources["manifest_file_sha256"],
                    "size_bytes": sources["manifest_size_bytes"],
                },
                "scorecard_gate": {
                    "path": SCORECARD_GATE_PATH.as_posix(),
                    "schema_version": gate["schema_version"],
                    "identity_sha256": gate["identity_sha256"],
                    "file_sha256": sources["gate_file_sha256"],
                    "size_bytes": sources["gate_size_bytes"],
                },
                "full_trace_evidence": {
                    **gate["evidence_ref"],
                    "remotely_retained": False,
                    "local_copy_verified_for_archive": False,
                    "receipt_derived_without_trace_bytes": True,
                },
            },
            "provenance_class": "simulation_source_controller",
            "controller_owner": controller_owner,
            "policy_owned_evidence": False,
            "capability_stage": "source_controller_boundary",
            "failure_class": "source_controller_boundary_negative",
            "task_scope": task_scope,
            "object_scope": object_scope,
            "cell": cell,
            "predicate_evidence": {
                "simulation_semantic_strict_success": result[
                    "simulation_semantic_strict_success"
                ],
                "strict_contact_frame_count": result["strict_contact_frame_count"],
                "maximum_anchor_lift_m": result["maximum_anchor_lift_m"],
                "terminal_outcome": result["terminal_outcome"],
                "first_trace_sha256": result["first_trace_sha256"],
                "second_trace_sha256": result["second_trace_sha256"],
                "replays_hash_identical": True,
            },
            "ensemble_scope": manifest["ensemble_scope"],
            "posterior_calibrated": False,
            "lifecycle_state": "active",
            "canonical_counterexample_id": "cex-0001",
            "duplicate_of_counterexample_id": None,
            "routing_class": "evidence_only",
            "routing": ROUTING_MATRIX["evidence_only"],
            "replay_tier": "evidence_only_no_remotely_retained_trace",
            "replay_eligible": False,
            "replay_ineligibility_reason": "full_trace_bytes_not_remotely_retained",
            "policy_regression_blame_allowed": False,
            "replay_gate_activation_allowed": False,
            "training_ingestion_eligible": False,
            "training_ingestion_authorized": False,
            "source_artifact_mutated": False,
            "simulation_replay_executed": False,
            "policy_replay_executed": False,
            "model_constructed": False,
            "model_inference": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "promotion_eligible": False,
        }
    )


def verify_seed_receipt(
    payload: dict[str, Any], *, sources: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.39 seed counterexample receipt")
    if payload != build_seed_receipt(sources=sources):
        raise ValueError("T20.39 seed counterexample receipt drifted")


def build_archive_index(
    *, receipt_refs: list[dict[str, Any]], receipts: list[dict[str, Any]]
) -> dict[str, Any]:
    _validate_archive_entries(receipt_refs=receipt_refs, receipts=receipts)
    active = [row for row in receipts if row["lifecycle_state"] == "active"]
    return sign_payload(
        {
            "schema_version": INDEX_SCHEMA_VERSION,
            "task_id": "T20.39",
            "archive_version": 1,
            "entry_count": len(receipts),
            "active_entry_count": len(active),
            "next_archive_sequence": len(receipts) + 1,
            "entries": receipt_refs,
            "active_semantic_fingerprints": [
                {
                    "semantic_fingerprint_sha256": row[
                        "semantic_fingerprint_sha256"
                    ],
                    "canonical_counterexample_id": row[
                        "canonical_counterexample_id"
                    ],
                }
                for row in active
            ],
            "lifecycle_states": list(LIFECYCLE_STATES),
            "lifecycle_transitions": {
                key: list(value) for key, value in LIFECYCLE_TRANSITIONS.items()
            },
            "routing_matrix": ROUTING_MATRIX,
            "duplicate_policy": (
                "one_active_canonical_receipt_per_semantic_fingerprint;_exact_"
                "duplicates_reference_canonical;_conflicts_and_aliases_fail_closed"
            ),
            "stale_source_policy": (
                "missing_or_drifted_source_marks_receipt_invalid_and_replay_"
                "ineligible_without_deleting_history"
            ),
            "replay_gate_active": False,
            "training_ingestion_active": False,
            "simulation_replay_executed": False,
            "policy_replay_executed": False,
            "model_constructed": False,
            "model_inference": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "promotion_eligible": False,
        }
    )


def verify_archive_index(
    payload: dict[str, Any], *, receipt_refs: list[dict[str, Any]], receipts: list[dict[str, Any]]
) -> None:
    verify_signed_payload(payload, label="T20.39 counterexample archive index")
    if payload != build_archive_index(receipt_refs=receipt_refs, receipts=receipts):
        raise ValueError("T20.39 counterexample archive index drifted")


def build_receipt_ref(*, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(payload, label="counterexample receipt ref")
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(encoded).hexdigest(),
        "size_bytes": len(encoded),
        "counterexample_id": payload["counterexample_id"],
        "semantic_fingerprint_sha256": payload["semantic_fingerprint_sha256"],
        "lifecycle_state": payload["lifecycle_state"],
        "routing_class": payload["routing_class"],
    }


def validate_lifecycle_transition(*, current: str, target: str) -> None:
    if current not in LIFECYCLE_TRANSITIONS or target not in LIFECYCLE_STATES:
        raise ValueError("Counterexample lifecycle state is unsupported")
    if target not in LIFECYCLE_TRANSITIONS[current]:
        raise ValueError("Counterexample lifecycle transition is not allowed")


def validate_routing(
    *,
    routing_class: str,
    policy_owned_evidence: bool,
    full_trace_remotely_retained: bool,
    requested_policy_blame: bool,
    requested_replay_gate: bool,
    requested_training_ingestion: bool,
) -> dict[str, bool]:
    if routing_class not in ROUTING_MATRIX or not all(
        isinstance(value, bool)
        for value in (
            policy_owned_evidence,
            full_trace_remotely_retained,
            requested_policy_blame,
            requested_replay_gate,
            requested_training_ingestion,
        )
    ):
        raise ValueError("Counterexample routing input drifted")
    route = ROUTING_MATRIX[routing_class]
    if requested_policy_blame and (
        not policy_owned_evidence or not route["policy_regression_blame_allowed"]
    ):
        raise ValueError("Counterexample policy blame is unauthorized")
    if route["fixed_replay_eligible"] and not full_trace_remotely_retained:
        raise ValueError("Counterexample replay route lacks retained trace bytes")
    if requested_replay_gate or requested_training_ingestion:
        raise ValueError("Counterexample replay/training activation requires new authority")
    return route


def derive_source_lifecycle_disposition(
    *, payload: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    """Derive the non-destructive lifecycle required by current source bytes."""

    verify_signed_payload(payload, label="counterexample source lifecycle")
    root = Path(repo_root)
    stale_or_missing = []
    for name in ("cell_manifest", "scorecard_gate"):
        ref = payload.get("source_refs", {}).get(name)
        if not isinstance(ref, dict):
            stale_or_missing.append({"source": name, "reason": "reference_missing"})
            continue
        path = Path(ref.get("path", ""))
        if path.is_absolute() or ".." in path.parts or not path.parts:
            stale_or_missing.append({"source": name, "reason": "path_unsafe"})
            continue
        source_path = root / path
        if not source_path.is_file():
            stale_or_missing.append({"source": name, "reason": "file_missing"})
            continue
        encoded = source_path.read_bytes()
        if (
            hashlib.sha256(encoded).hexdigest() != ref.get("file_sha256")
            or len(encoded) != ref.get("size_bytes")
        ):
            stale_or_missing.append({"source": name, "reason": "file_drifted"})
    sources_valid = not stale_or_missing
    return sign_payload(
        {
            "schema_version": "scenesmith.counterexample_source_lifecycle.v1",
            "counterexample_id": payload.get("counterexample_id"),
            "receipt_identity_sha256": payload["identity_sha256"],
            "sources_valid": sources_valid,
            "required_lifecycle_state": (
                payload.get("lifecycle_state") if sources_valid else "invalid"
            ),
            "replay_eligible": (
                payload.get("replay_eligible") is True if sources_valid else False
            ),
            "stale_or_missing_sources": stale_or_missing,
            "history_delete_allowed": False,
            "history_preserved": True,
        }
    )


def _validate_archive_entries(
    *, receipt_refs: list[dict[str, Any]], receipts: list[dict[str, Any]]
) -> None:
    if (
        not isinstance(receipt_refs, list)
        or not isinstance(receipts, list)
        or not receipts
        or len(receipt_refs) != len(receipts)
    ):
        raise ValueError("Counterexample archive coverage drifted")
    ids = []
    paths = []
    active_fingerprints = []
    canonical_by_fingerprint: dict[str, dict[str, Any]] = {}
    for index, (ref, receipt) in enumerate(zip(receipt_refs, receipts, strict=True), start=1):
        verify_signed_payload(receipt, label="counterexample archive receipt")
        _validate_receipt_contract(receipt)
        path = Path(ref.get("path", ""))
        fingerprint = receipt.get("semantic_fingerprint_sha256")
        if (
            receipt.get("archive_sequence") != index
            or path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or ref != build_receipt_ref(path=path, payload=receipt)
            or fingerprint
            != hashlib.sha256(
                canonical_json_bytes(receipt.get("semantic_core"))
            ).hexdigest()
            or receipt.get("lifecycle_state") not in LIFECYCLE_STATES
            or receipt.get("routing") != ROUTING_MATRIX.get(receipt.get("routing_class"))
            or receipt.get("training_ingestion_eligible") is not False
            or receipt.get("replay_gate_activation_allowed") is not False
        ):
            raise ValueError("Counterexample archive entry drifted")
        canonical_receipt = canonical_by_fingerprint.get(fingerprint)
        if canonical_receipt is None:
            if (
                receipt.get("canonical_counterexample_id")
                != receipt.get("counterexample_id")
                or receipt.get("duplicate_of_counterexample_id") is not None
            ):
                raise ValueError("Counterexample canonical receipt drifted")
            canonical_by_fingerprint[fingerprint] = receipt
        elif (
            receipt.get("lifecycle_state") == "active"
            or receipt.get("canonical_counterexample_id")
            != canonical_receipt["counterexample_id"]
            or receipt.get("duplicate_of_counterexample_id")
            != canonical_receipt["counterexample_id"]
            or _duplicate_projection(receipt)
            != _duplicate_projection(canonical_receipt)
        ):
            raise ValueError("Counterexample conflicting duplicate reference drifted")
        ids.append(receipt["counterexample_id"])
        paths.append(ref["path"])
        if receipt["lifecycle_state"] == "active":
            active_fingerprints.append(fingerprint)
    if (
        len(ids) != len(set(ids))
        or len(paths) != len(set(paths))
        or len(active_fingerprints) != len(set(active_fingerprints))
    ):
        raise ValueError("Counterexample duplicate or path alias detected")


def _validate_receipt_contract(receipt: dict[str, Any]) -> None:
    semantic_core = receipt.get("semantic_core")
    routing = ROUTING_MATRIX.get(receipt.get("routing_class"))
    full_trace = receipt.get("source_refs", {}).get("full_trace_evidence", {})
    if (
        receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION
        or receipt.get("task_id") != "T20.39"
        or not isinstance(semantic_core, dict)
        or receipt.get("semantic_fingerprint_sha256")
        != hashlib.sha256(canonical_json_bytes(semantic_core)).hexdigest()
        or routing is None
        or receipt.get("routing") != routing
        or not isinstance(receipt.get("policy_owned_evidence"), bool)
    ):
        raise ValueError("Counterexample receipt contract drifted")
    aligned_fields = (
        "provenance_class",
        "controller_owner",
        "capability_stage",
        "failure_class",
        "task_scope",
        "object_scope",
    )
    if any(receipt.get(field) != semantic_core.get(field) for field in aligned_fields):
        raise ValueError("Counterexample receipt semantic core contradicts top level")
    predicate = receipt.get("predicate_evidence", {})
    cell = receipt.get("cell", {})
    semantic_cell_fields = ("cell_id", "factor", "value")
    if any(cell.get(field) != semantic_core.get(field) for field in semantic_cell_fields):
        raise ValueError("Counterexample cell contradicts semantic core")
    semantic_predicates = (
        "terminal_outcome",
        "simulation_semantic_strict_success",
        "strict_contact_frame_count",
        "maximum_anchor_lift_m",
    )
    if any(predicate.get(field) != semantic_core.get(field) for field in semantic_predicates):
        raise ValueError("Counterexample predicate evidence contradicts semantic core")
    if predicate.get("first_trace_sha256") != semantic_core.get("trace_sha256"):
        raise ValueError("Counterexample trace evidence contradicts semantic core")
    if (
        receipt.get("policy_regression_blame_allowed")
        is not routing["policy_regression_blame_allowed"]
        or receipt.get("replay_eligible") is not routing["fixed_replay_eligible"]
        or receipt.get("replay_gate_activation_allowed")
        is not routing["replay_gate_activation_allowed"]
        or receipt.get("training_ingestion_eligible")
        is not routing["training_ingestion_eligible"]
        or receipt.get("training_ingestion_authorized") is not False
    ):
        raise ValueError("Counterexample top-level routing authority drifted")
    if (
        receipt["policy_regression_blame_allowed"]
        and not receipt["policy_owned_evidence"]
    ):
        raise ValueError("Counterexample policy blame lacks policy-owned evidence")
    if receipt["replay_eligible"] and full_trace.get("remotely_retained") is not True:
        raise ValueError("Counterexample replay lacks remotely retained trace")


def _duplicate_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    projection = copy.deepcopy(receipt)
    for field in DUPLICATE_MUTABLE_FIELDS:
        projection.pop(field, None)
    return projection

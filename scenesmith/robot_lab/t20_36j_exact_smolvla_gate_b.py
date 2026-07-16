"""Fail-closed live preflight and one-use contracts for T20.36j."""

from __future__ import annotations

import builtins
import contextlib
import hashlib
import importlib.metadata
import io
import os
import socket

from pathlib import Path
from typing import Any, Iterator

from packaging.markers import default_environment
from packaging.utils import canonicalize_name

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    EVALUATION_UPDATE_SCHEDULE,
    MAXIMUM_OPTIMIZER_UPDATES,
)
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (
    _finite_trace,
    _runtime_smoke,
    _saved_checkpoint_tree,
    _validated_evaluations,
    _verify_spec,
    build_evaluation_row,
    load_verified_spec,
)
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (
    ATTEMPT_PATH,
    CORRECTED_PREFLIGHT_PATH,
    CORRECTED_PREFLIGHT_SCHEMA_VERSION,
    EXPECTED_CONTRACT_IDENTITY,
    OFFLINE_ENVIRONMENT,
    PROCESSOR_SMOKE_SCHEMA_VERSION,
    RESULT_PATH as CONTRACT_PATH,
    ROOT_REQUIREMENTS,
    RUN_RESULT_PATH,
    RUN_SUMMARY_PATH,
    TRAINING_PERMIT_PATH,
    WEIGHT_OR_TENSOR_SUFFIXES,
    build_installed_closure,
    build_processor_smoke_evidence,
    verify_contract_file,
    verify_corrected_preflight,
    verify_installed_closure,
    verify_processor_smoke_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ATTEMPT_PATH.parent
FAILURE_PATH = RUN_ROOT / "failure.json"
CHECKPOINT_ROOT = RUN_ROOT / "checkpoint"
INSTALLED_CLOSURE_PATH = Path(
    "configurations/robot_lab/t20_36j_installed_dependency_closure.json"
)
PROCESSOR_SMOKE_PATH = Path(
    "configurations/robot_lab/t20_36j_offline_auto_processor_smoke.json"
)
FAILURE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36j_exact_smolvla_gate_b_failure_result.json"
)
TASK_ID = "T20.36j"
TRAINING_PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_36j_exact_smolvla_gate_b_permit.v1"
)
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36j_exact_smolvla_gate_b_attempt.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_36j_exact_smolvla_gate_b_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36j_exact_smolvla_gate_b_result.v1"
FAILURE_SCHEMA_VERSION = "scenesmith.t20_36j_exact_smolvla_gate_b_failure.v1"
FAILURE_RESULT_SCHEMA_VERSION = (
    "scenesmith.t20_36j_exact_smolvla_gate_b_failure_result.v1"
)
FROZEN_EVALUATOR_SCHEMA_VERSION = (
    "scenesmith.t20_36h_exact_smolvla_gate_b_evaluation.v1"
)
SMOKE_SEED = 20260800


def collect_installed_closure() -> dict[str, Any]:
    """Collect recursive active Requires-Dist evidence without importing models."""

    distributions: dict[str, dict[str, Any]] = {}
    for distribution in importlib.metadata.distributions():
        raw_name = distribution.metadata.get("Name")
        if not raw_name:
            continue
        name = canonicalize_name(raw_name)
        metadata_bytes = _distribution_metadata_bytes(distribution, name=name)
        row = {
            "version": distribution.version,
            "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
            "requires_dist": list(distribution.requires or []),
        }
        if name in distributions and distributions[name] != row:
            raise ValueError(f"T20.36j duplicate installed distribution: {name}")
        distributions[name] = row
    marker_environment = default_environment()
    marker_environment["extra"] = ""
    closure = build_installed_closure(
        root_requirements=ROOT_REQUIREMENTS,
        distributions=distributions,
        marker_environment=marker_environment,
    )
    verify_installed_closure(closure)
    return closure


def _distribution_metadata_bytes(distribution: Any, *, name: str) -> bytes:
    """Read wheel METADATA or its byte-identical editable PKG-INFO form."""

    candidates: list[Path] = []
    metadata_root = getattr(distribution, "_path", None)
    if metadata_root is not None:
        root = Path(metadata_root)
        candidates.extend((root / "METADATA", root / "PKG-INFO"))
    for entry in distribution.files or []:
        if Path(entry).name in {"METADATA", "PKG-INFO"}:
            candidates.append(Path(distribution.locate_file(entry)))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_bytes()
    raise ValueError(f"T20.36j METADATA or PKG-INFO is unavailable for {name}")


class ProcessorAccessGuard:
    """Observe snapshot opens and reject network or tensor/weight file access."""

    def __init__(self, snapshot: Path) -> None:
        self.snapshot = snapshot.resolve()
        self.opened_snapshot_files: set[str] = set()
        self.network_attempted = False
        self._resolved_targets: dict[Path, set[str]] = {}
        for path in self.snapshot.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.snapshot).as_posix()
            self._resolved_targets.setdefault(path.resolve(), set()).add(relative)

    def observe_path(self, raw_path: Any) -> None:
        if isinstance(raw_path, int):
            return
        try:
            lexical = Path(os.path.abspath(os.fspath(raw_path)))
        except (OSError, TypeError, ValueError):
            return
        if lexical.is_relative_to(self.snapshot):
            relative_paths = {lexical.relative_to(self.snapshot).as_posix()}
        else:
            try:
                relative_paths = self._resolved_targets.get(lexical.resolve(), set())
            except OSError:
                relative_paths = set()
        for relative in relative_paths:
            if relative.lower().endswith(WEIGHT_OR_TENSOR_SUFFIXES):
                raise PermissionError(
                    "T20.36j processor smoke blocked tensor/weight read: "
                    f"{relative}"
                )
            self.opened_snapshot_files.add(relative)

    def block_network(self, *_args: Any, **_kwargs: Any) -> Any:
        self.network_attempted = True
        raise RuntimeError("T20.36j processor smoke blocked network access")


@contextlib.contextmanager
def guarded_processor_access(snapshot: Path) -> Iterator[ProcessorAccessGuard]:
    guard = ProcessorAccessGuard(snapshot)
    original_builtin_open = builtins.open
    original_io_open = io.open
    original_os_open = os.open
    original_create_connection = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo

    def guarded_builtin_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        guard.observe_path(file)
        return original_builtin_open(file, *args, **kwargs)

    def guarded_io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        guard.observe_path(file)
        return original_io_open(file, *args, **kwargs)

    def guarded_os_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        guard.observe_path(file)
        return original_os_open(file, *args, **kwargs)

    builtins.open = guarded_builtin_open
    io.open = guarded_io_open
    os.open = guarded_os_open
    socket.create_connection = guard.block_network
    socket.getaddrinfo = guard.block_network
    try:
        yield guard
    finally:
        builtins.open = original_builtin_open
        io.open = original_io_open
        os.open = original_os_open
        socket.create_connection = original_create_connection
        socket.getaddrinfo = original_getaddrinfo


def construct_offline_processor_smoke(
    *, expected_vlm_snapshot: str
) -> dict[str, Any]:
    """Construct only AutoProcessor under explicit offline and file-open guards."""

    snapshot = Path(expected_vlm_snapshot).resolve()
    if not snapshot.is_dir():
        raise FileNotFoundError(snapshot)
    os.environ.update(
        {
            **OFFLINE_ENVIRONMENT,
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "0",
        }
    )
    from transformers import AutoProcessor

    with guarded_processor_access(snapshot) as guard:
        processor = AutoProcessor.from_pretrained(
            str(snapshot), local_files_only=True
        )
    tokenizer = getattr(processor, "tokenizer", None)
    image_processor = getattr(processor, "image_processor", None)
    if image_processor is None:
        image_processor = getattr(processor, "video_processor", None)
    evidence = build_processor_smoke_evidence(
        expected_vlm_snapshot=str(snapshot),
        observed_vlm_snapshot=str(snapshot),
        processor_class=type(processor).__name__,
        tokenizer_class=type(tokenizer).__name__,
        image_processor_class=type(image_processor).__name__,
        opened_snapshot_files=sorted(guard.opened_snapshot_files),
        offline_environment=dict(OFFLINE_ENVIRONMENT),
        local_files_only=True,
        network_attempted=guard.network_attempted,
        constructed=True,
    )
    verify_processor_smoke_evidence(
        evidence, expected_vlm_snapshot=str(snapshot)
    )
    return evidence


def build_training_permit(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    corrected_preflight: dict[str, Any],
) -> dict[str, Any]:
    _verify_spec(spec)
    contract = verify_contract_file(repo_root=REPO_ROOT)
    verify_corrected_preflight(corrected_preflight, contract=contract)
    _sha(authority_identity, "authority decision")
    if (
        corrected_preflight.get("schema_version")
        != CORRECTED_PREFLIGHT_SCHEMA_VERSION
        or corrected_preflight.get("authority_decision_identity_sha256")
        != authority_identity
        or corrected_preflight.get("contract_identity_sha256")
        != EXPECTED_CONTRACT_IDENTITY
        or corrected_preflight.get("processor_smoke", {}).get("schema_version")
        != PROCESSOR_SMOKE_SCHEMA_VERSION
        or spec.get("campaign", {}).get("maximum_optimizer_updates")
        != MAXIMUM_OPTIMIZER_UPDATES
        or spec.get("gate", {}).get(
            "maximum_final_to_baseline_supervised_objective_ratio"
        )
        != 0.10
        or spec.get("gate", {}).get("maximum_physical_action_error_rad")
        != 0.05
    ):
        raise ValueError("T20.36j training permit prerequisites drifted")
    return sign_payload(
        {
            "schema_version": TRAINING_PERMIT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "corrected_preflight_identity_sha256": corrected_preflight[
                "identity_sha256"
            ],
            "installed_closure_identity_sha256": corrected_preflight[
                "installed_closure"
            ]["identity_sha256"],
            "processor_smoke_identity_sha256": corrected_preflight[
                "processor_smoke"
            ]["identity_sha256"],
            "environment_manifest_identity_sha256": corrected_preflight[
                "installed_closure"
            ]["environment_manifest_identity_sha256"],
            "checkpoint_tree_identity_sha256": corrected_preflight[
                "checkpoint_tree_identity_sha256"
            ],
            "required_source_commit": corrected_preflight["source_commit"],
            "authorized_attempt_count": 1,
            "authorized_actions": [
                "simulation_model_construction",
                "simulation_model_inference",
                "simulation_optimizer_training",
            ],
            "evaluation_contract_schema_version": (
                FROZEN_EVALUATOR_SCHEMA_VERSION
            ),
            "evaluation_update_schedule": list(EVALUATION_UPDATE_SCHEDULE),
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "maximum_final_to_baseline_supervised_objective_ratio": 0.10,
            "maximum_physical_action_error_rad": 0.05,
            "attempt_marker_path": str(ATTEMPT_PATH),
            "attempt_marker_must_precede_model_construction": True,
            "runtime_smoke_is_part_of_counted_attempt": True,
            "smoke_failure_consumes_attempt": True,
            "local_execution_eligible_after_remote_preservation": True,
            "retry_or_sweep_allowed": False,
            "policy_track_selected": False,
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


def verify_training_permit(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    corrected_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36j training permit")
    expected = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        corrected_preflight=corrected_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36j training permit drifted")


def build_attempt_marker(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    source_commit: str,
) -> dict[str, Any]:
    _sha(authority_identity, "authority decision")
    _commit(source_commit, "attempt source commit")
    verify_signed_payload(training_permit, label="T20.36j training permit")
    if (
        training_permit.get("schema_version")
        != TRAINING_PERMIT_SCHEMA_VERSION
        or training_permit.get("task_id") != TASK_ID
        or training_permit.get("training_spec_identity_sha256")
        != spec.get("identity_sha256")
        or training_permit.get("authority_decision_identity_sha256")
        != authority_identity
        or training_permit.get("authorized_attempt_count") != 1
        or training_permit.get("smoke_failure_consumes_attempt") is not True
        or training_permit.get("retry_or_sweep_allowed") is not False
        or training_permit.get("maximum_optimizer_updates")
        != MAXIMUM_OPTIMIZER_UPDATES
        or training_permit.get(
            "maximum_final_to_baseline_supervised_objective_ratio"
        )
        != 0.10
        or training_permit.get("maximum_physical_action_error_rad") != 0.05
        or training_permit.get("gate_b_threshold_changed") is not False
        or training_permit.get("gate_c_authorized") is not False
    ):
        raise ValueError("T20.36j attempt permit linkage drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "source_commit": source_commit,
            "training_seed": spec["campaign"]["training_seed"],
            "attempt_number": 1,
            "created_before_model_construction": True,
            "model_constructed": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_attempt_marker(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36j attempt marker")
    expected = build_attempt_marker(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        source_commit=payload.get("source_commit"),
    )
    if payload != expected:
        raise ValueError("T20.36j attempt marker drifted")


def build_failure(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    failure_stage: str,
    error_type: str,
    error_message: str,
    optimizer_update_count: int,
    model_constructed: bool,
    model_loaded: bool,
    model_inference: bool,
    optimizer_created: bool,
    optimizer_training: bool,
) -> dict[str, Any]:
    verify_attempt_marker(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
    )
    if failure_stage not in {
        "model_construction",
        "runtime_smoke",
        "optimizer_training",
        "evaluation",
        "checkpoint_write",
    }:
        raise ValueError("T20.36j failure stage is invalid")
    booleans = (
        model_constructed,
        model_loaded,
        model_inference,
        optimizer_created,
        optimizer_training,
    )
    if (
        not isinstance(error_type, str)
        or not error_type
        or not isinstance(error_message, str)
        or not error_message
        or len(error_message) > 2000
        or isinstance(optimizer_update_count, bool)
        or not isinstance(optimizer_update_count, int)
        or not 0 <= optimizer_update_count <= MAXIMUM_OPTIMIZER_UPDATES
        or any(not isinstance(value, bool) for value in booleans)
    ):
        raise ValueError("T20.36j failure evidence is invalid")
    return sign_payload(
        {
            "schema_version": FAILURE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "failure_stage": failure_stage,
            "error_type": error_type,
            "error_message": error_message,
            "optimizer_update_count": optimizer_update_count,
            "attempt_consumed": True,
            "retry_or_sweep_allowed": False,
            "model_constructed": model_constructed,
            "checkpoint_tensor_read": model_constructed,
            "model_loaded": model_loaded,
            "model_inference": model_inference,
            "optimizer_created": optimizer_created,
            "optimizer_training": optimizer_training,
            "gate_b_passed": False,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_failure(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36j failure")
    expected = build_failure(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
        failure_stage=payload.get("failure_stage"),
        error_type=payload.get("error_type"),
        error_message=payload.get("error_message"),
        optimizer_update_count=payload.get("optimizer_update_count"),
        model_constructed=payload.get("model_constructed"),
        model_loaded=payload.get("model_loaded"),
        model_inference=payload.get("model_inference"),
        optimizer_created=payload.get("optimizer_created"),
        optimizer_training=payload.get("optimizer_training"),
    )
    if payload != expected:
        raise ValueError("T20.36j failure evidence drifted")


def build_failure_result(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    failure: dict[str, Any],
) -> dict[str, Any]:
    verify_failure(
        failure,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
    )
    return sign_payload(
        {
            "schema_version": FAILURE_RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "failure_identity_sha256": failure["identity_sha256"],
            "failure_stage": failure["failure_stage"],
            "error_type": failure["error_type"],
            "error_message": failure["error_message"],
            "failure_class": "bounded_smolvla_replacement_runtime_failure",
            "optimizer_update_count": failure["optimizer_update_count"],
            "attempt_consumed": True,
            "retry_or_sweep_allowed": False,
            "smolvla_gate_b_evaluated": False,
            "gate_b_passed": False,
            "decision": "smolvla_replacement_runtime_failure",
            "selected_next_hypothesis": (
                "close_smolvla_alphabet_and_route_act_control"
            ),
            "smolvla_alphabet_closed": True,
            "model_constructed": failure["model_constructed"],
            "checkpoint_tensor_read": failure["checkpoint_tensor_read"],
            "model_loaded": failure["model_loaded"],
            "model_inference": failure["model_inference"],
            "optimizer_created": failure["optimizer_created"],
            "optimizer_training": failure["optimizer_training"],
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_failure_result(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    failure: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36j failure result")
    expected = build_failure_result(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
        failure=failure,
    )
    if payload != expected:
        raise ValueError("T20.36j failure result drifted")


def build_run_summary(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    runtime_smoke: dict[str, Any],
    optimizer_update_count: int,
    per_update_objective: list[float],
    gradient_norms_before_clip: list[float],
    evaluations: list[dict[str, Any]],
    checkpoint_tree: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_attempt_marker(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
    )
    smoke = _runtime_smoke(runtime_smoke)
    if (
        isinstance(optimizer_update_count, bool)
        or optimizer_update_count not in EVALUATION_UPDATE_SCHEDULE[1:]
    ):
        raise ValueError("T20.36j optimizer update count drifted")
    losses = _finite_trace(
        per_update_objective, optimizer_update_count, "objective trace"
    )
    gradients = _finite_trace(
        gradient_norms_before_clip, optimizer_update_count, "gradient trace"
    )
    normalized_evaluations = _validated_evaluations(evaluations)
    updates = [row["optimizer_update_count"] for row in normalized_evaluations]
    if (
        updates != EVALUATION_UPDATE_SCHEDULE[: len(updates)]
        or updates[-1] != optimizer_update_count
    ):
        raise ValueError("T20.36j evaluation schedule is incomplete or reordered")
    passing = [row for row in normalized_evaluations[1:] if row["gate_b_passed"]]
    passed = bool(passing)
    if passed and normalized_evaluations[-1] != passing[0]:
        raise ValueError("T20.36j run continued after its first Gate B pass")
    if not passed and updates != EVALUATION_UPDATE_SCHEDULE:
        raise ValueError("T20.36j failed run stopped before its ceiling")
    tree = _saved_checkpoint_tree(checkpoint_tree)
    final = normalized_evaluations[-1]
    return sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "frozen_evaluation_contract_schema_version": (
                FROZEN_EVALUATOR_SCHEMA_VERSION
            ),
            "runtime_smoke": smoke,
            "optimizer_update_count": optimizer_update_count,
            "training_seed": spec["campaign"]["training_seed"],
            "per_update_objective": losses,
            "gradient_norms_before_clip": gradients,
            "evaluations": normalized_evaluations,
            "selected_checkpoint_update": optimizer_update_count,
            "checkpoint_tree": tree,
            "checkpoint_identity_sha256": hashlib.sha256(
                canonical_json_bytes(tree)
            ).hexdigest(),
            "gate_b_passed": passed,
            "decision": "smolvla_gate_b_pass" if passed else "smolvla_gate_b_fail",
            "selected_next_hypothesis": (
                "design_smolvla_gate_c_training_episode_reproduction"
                if passed
                else "close_smolvla_alphabet_and_route_act_control"
            ),
            "final_to_baseline_supervised_objective_ratio": final[
                "final_to_baseline_supervised_objective_ratio"
            ],
            "final_maximum_absolute_error_rad": final[
                "maximum_absolute_error_rad"
            ],
            "model_constructed": True,
            "checkpoint_tensor_read": True,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_run_summary(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36j run summary")
    expected = build_run_summary(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
        runtime_smoke=payload.get("runtime_smoke"),
        optimizer_update_count=payload.get("optimizer_update_count"),
        per_update_objective=payload.get("per_update_objective"),
        gradient_norms_before_clip=payload.get("gradient_norms_before_clip"),
        evaluations=payload.get("evaluations"),
        checkpoint_tree=payload.get("checkpoint_tree"),
    )
    if payload != expected:
        raise ValueError("T20.36j run summary drifted")


def build_result(*, spec: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    _verify_spec(spec)
    _validate_result_run(run, spec=spec)
    passed = run.get("gate_b_passed") is True
    if run.get("decision") != (
        "smolvla_gate_b_pass" if passed else "smolvla_gate_b_fail"
    ):
        raise ValueError("T20.36j run decision drifted")
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "run_identity_sha256": run["identity_sha256"],
            "optimizer_update_count": run["optimizer_update_count"],
            "selected_checkpoint_update": run["selected_checkpoint_update"],
            "checkpoint_identity_sha256": run["checkpoint_identity_sha256"],
            "final_to_baseline_supervised_objective_ratio": run[
                "final_to_baseline_supervised_objective_ratio"
            ],
            "final_maximum_absolute_error_rad": run[
                "final_maximum_absolute_error_rad"
            ],
            "gate_b_passed": passed,
            "decision": run["decision"],
            "smolvla_one_batch_capability_verified": passed,
            "gate_c_design_routed": passed,
            "act_control_routed": not passed,
            "smolvla_alphabet_closed": not passed,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "model_constructed": True,
            "checkpoint_tensor_read": True,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_result(
    payload: dict[str, Any], *, spec: dict[str, Any], run: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36j result")
    if payload != build_result(spec=spec, run=run):
        raise ValueError("T20.36j result drifted")


def load_live_contracts(
    *, authority_identity: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = verify_contract_file(repo_root=REPO_ROOT)
    preflight = load_strict_json(REPO_ROOT / CORRECTED_PREFLIGHT_PATH)
    verify_corrected_preflight(preflight, contract=contract)
    permit = load_strict_json(REPO_ROOT / TRAINING_PERMIT_PATH)
    spec = load_verified_spec(repo_root=REPO_ROOT)
    verify_training_permit(
        permit,
        spec=spec,
        authority_identity=authority_identity,
        corrected_preflight=preflight,
    )
    return spec, preflight, permit


def _validate_result_run(run: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(run, label="T20.36j run source")
    updates = run.get("optimizer_update_count")
    if (
        run.get("schema_version") != RUN_SCHEMA_VERSION
        or run.get("task_id") != TASK_ID
        or run.get("training_spec_identity_sha256")
        != spec.get("identity_sha256")
        or run.get("frozen_evaluation_contract_schema_version")
        != FROZEN_EVALUATOR_SCHEMA_VERSION
        or isinstance(updates, bool)
        or updates not in EVALUATION_UPDATE_SCHEDULE[1:]
    ):
        raise ValueError("T20.36j run source linkage drifted")
    _runtime_smoke(run.get("runtime_smoke"))
    _finite_trace(run.get("per_update_objective"), updates, "objective trace")
    _finite_trace(
        run.get("gradient_norms_before_clip"), updates, "gradient trace"
    )
    evaluations = _validated_evaluations(run.get("evaluations"))
    schedule = [row["optimizer_update_count"] for row in evaluations]
    if (
        schedule != EVALUATION_UPDATE_SCHEDULE[: len(schedule)]
        or schedule[-1] != updates
    ):
        raise ValueError("T20.36j intrinsic evaluation schedule drifted")
    passing = [row for row in evaluations[1:] if row["gate_b_passed"]]
    if bool(passing) != run.get("gate_b_passed"):
        raise ValueError("T20.36j intrinsic gate decision drifted")
    if passing and evaluations[-1] != passing[0]:
        raise ValueError("T20.36j intrinsic run continued after pass")
    if not passing and schedule != EVALUATION_UPDATE_SCHEDULE:
        raise ValueError("T20.36j intrinsic failed run is incomplete")
    tree = _saved_checkpoint_tree(run.get("checkpoint_tree"))
    if hashlib.sha256(canonical_json_bytes(tree)).hexdigest() != run.get(
        "checkpoint_identity_sha256"
    ):
        raise ValueError("T20.36j intrinsic checkpoint identity drifted")
    final = evaluations[-1]
    expected_decision = (
        "smolvla_gate_b_pass" if passing else "smolvla_gate_b_fail"
    )
    frozen_false = (
        "policy_track_selected",
        "gate_b_threshold_changed",
        "gate_c_authorized",
        "closed_loop_rollout",
        "simulation_policy_accepted",
        "physical_actuation",
        "network_accessed",
        "weights_downloaded",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if (
        run.get("decision") != expected_decision
        or run.get("selected_checkpoint_update") != updates
        or run.get("final_to_baseline_supervised_objective_ratio")
        != final["final_to_baseline_supervised_objective_ratio"]
        or run.get("final_maximum_absolute_error_rad")
        != final["maximum_absolute_error_rad"]
        or any(
            run.get(field) is not True
            for field in (
                "model_constructed",
                "checkpoint_tensor_read",
                "model_loaded",
                "model_inference",
                "optimizer_created",
                "optimizer_training",
            )
        )
        or any(run.get(field) is not False for field in frozen_false)
    ):
        raise ValueError("T20.36j intrinsic result or authority drifted")


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36j {label} is not a lowercase SHA-256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36j {label} is not a full Git commit")
    return value

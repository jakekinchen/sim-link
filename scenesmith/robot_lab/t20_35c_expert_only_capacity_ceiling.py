"""Fail-closed Gate B expert-only capacity ceiling for T20.35c."""

from __future__ import annotations

import copy
import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    ACTION_HORIZON,
    FRAME_INDEX,
    INFERENCE_SEEDS,
    LEARNING_RATE,
    MAX_ACTION_ERROR_RAD,
    MAX_OBJECTIVE_RATIO,
    OPTIMIZER_UPDATES,
    SOURCE_SEED,
    SPEC_PATH as T20_33_SPEC_PATH,
    TRAINING_SEED,
    verify_preflight as verify_t20_33_preflight,
    verify_training_spec as verify_t20_33_training_spec,
    verify_training_spec_file as verify_t20_33_training_spec_file,
)
from scenesmith.robot_lab.t20_35_rank_capacity_discriminator import (
    RESULT_PATH as T20_35_RESULT_PATH,
)
from scenesmith.robot_lab.t20_35b_pi05_coverage_correction import (
    CORRECTION_PATH,
    verify_correction,
    verify_correction_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_35c_expert_only_training_spec.json")
RESULT_PATH = Path("configurations/robot_lab/t20_35c_expert_only_result.json")
SCHEMA_VERSION = "scenesmith.t20_35c_expert_only_training_spec.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_35c_expert_only_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_35c_expert_only_result.v1"
ADAPTATION_MODE = "expert_only_no_peft"
TRAINABLE_PREFIXES = (
    "model.paligemma_with_expert.gemma_expert.",
    "model.action_in_proj.",
    "model.action_out_proj.",
    "model.time_mlp_in.",
    "model.time_mlp_out.",
)
PALIGEMMA_PREFIX = "model.paligemma_with_expert.paligemma."
EXPECTED_CORRECTION_IDENTITY = (
    "446a06860663be438b3dc1c87e4d2571a9cd4866b1d16feaa1e279e06cfe10f6"
)
EXPECTED_T20_35_RESULT_IDENTITY = (
    "99538521686cf3e3ea16df352e12ddd7d02613bd2fdd2a9877ebe16e9b036ca8"
)
EXPECTED_DATASET_ACTION_CHUNK_SHA256 = (
    "5698babc07b2eebc8a3a96d33b28f03bbb33f1bec9b83a97d4e4f8a325c36b7e"
)


def build_training_spec(
    *, t20_33_spec: dict[str, Any], correction: dict[str, Any]
) -> dict[str, Any]:
    """Derive T20.35c from the frozen T20.33 contract and T20.35b audit."""
    verify_t20_33_training_spec(t20_33_spec)
    verify_correction(correction)
    if (
        correction.get("identity_sha256") != EXPECTED_CORRECTION_IDENTITY
        or correction.get("decision") != "pi05_peft_coverage_fail"
        or correction.get("selected_next_hypothesis")
        != "gate_b_expert_only_unfreeze_capacity_ceiling"
    ):
        raise ValueError("T20.35c source coverage correction drifted")
    payload = copy.deepcopy(t20_33_spec)
    payload.pop("identity_sha256", None)
    payload["schema_version"] = SCHEMA_VERSION
    payload["task_id"] = "T20.35c"
    payload["scope"] = "gate_b_same_batch_expert_only_capacity_ceiling"
    payload["t20_33_training_spec_identity_sha256"] = t20_33_spec[
        "identity_sha256"
    ]
    payload["t20_35b_coverage_correction_identity_sha256"] = correction[
        "identity_sha256"
    ]
    payload["lerobot_stack_identity_sha256"] = correction[
        "lerobot_stack_identity_sha256"
    ]
    payload["pi05_model_source_sha256"] = correction[
        "pi05_model_source_sha256"
    ]
    model = payload["model"]
    model["adapter"] = "none"
    model.pop("lora_rank", None)
    model.pop("lora_alpha", None)
    model["adaptation_mode"] = ADAPTATION_MODE
    model["train_expert_only"] = True
    model["freeze_vision_encoder"] = True
    model["trainable_prefixes"] = list(TRAINABLE_PREFIXES)
    model["paligemma_prefix"] = PALIGEMMA_PREFIX
    return sign_payload(payload)


def verify_training_spec(
    payload: dict[str, Any], *, t20_33_spec: dict[str, Any], correction: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35c expert-only training spec")
    expected = build_training_spec(t20_33_spec=t20_33_spec, correction=correction)
    if payload != expected:
        raise ValueError("T20.35c training spec drifted beyond adaptation boundary")


def verify_preflight(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    activate_lerobot_stack(repo_root=root, stage="training")
    t20_33_spec = verify_t20_33_training_spec_file(repo_root=root)
    t20_33_preflight = verify_t20_33_preflight(repo_root=root)
    correction = verify_correction_file(repo_root=root)
    spec = build_training_spec(t20_33_spec=t20_33_spec, correction=correction)
    verify_training_spec(
        spec, t20_33_spec=t20_33_spec, correction=correction
    )
    return {
        "training_spec": spec,
        "t20_33_training_spec": t20_33_spec,
        "coverage_correction": correction,
        "source_episode": t20_33_preflight["source_episode"],
        "source_entry": t20_33_preflight["source_entry"],
    }


def verify_training_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    preflight = verify_preflight(repo_root=root)
    archived = load_strict_json(root / SPEC_PATH)
    verify_training_spec(
        archived,
        t20_33_spec=preflight["t20_33_training_spec"],
        correction=preflight["coverage_correction"],
    )
    if archived != preflight["training_spec"]:
        raise ValueError("T20.35c training spec drifted from pinned sources")
    return archived


def verify_parameter_boundary(
    *, all_parameter_names: list[str], trainable_parameter_names: list[str]
) -> dict[str, int]:
    """Require complete expert/projection training and a wholly frozen PaliGemma."""
    if (
        not isinstance(all_parameter_names, list)
        or not all_parameter_names
        or len(all_parameter_names) != len(set(all_parameter_names))
        or any(not isinstance(name, str) or not name for name in all_parameter_names)
    ):
        raise ValueError("T20.35c all-parameter name set is invalid")
    if (
        not isinstance(trainable_parameter_names, list)
        or not trainable_parameter_names
        or len(trainable_parameter_names) != len(set(trainable_parameter_names))
        or any(not isinstance(name, str) or not name for name in trainable_parameter_names)
    ):
        raise ValueError("T20.35c trainable parameter name set is invalid")
    all_names = set(all_parameter_names)
    trainable = set(trainable_parameter_names)
    if not trainable.issubset(all_names):
        raise ValueError("T20.35c trainable parameter is absent from model")
    if any("lora_" in name or "peft" in name.lower() for name in all_names):
        raise ValueError("T20.35c PEFT or LoRA parameter detected")
    paligemma = {name for name in all_names if name.startswith(PALIGEMMA_PREFIX)}
    if not paligemma or paligemma & trainable:
        raise ValueError("T20.35c PaliGemma is missing or trainable")
    allowed = {
        name for name in all_names if any(name.startswith(prefix) for prefix in TRAINABLE_PREFIXES)
    }
    if trainable != allowed:
        raise ValueError("T20.35c expert-only trainable boundary is incomplete or broad")
    counts: dict[str, int] = {}
    for prefix in TRAINABLE_PREFIXES:
        count = sum(name.startswith(prefix) for name in trainable)
        if count <= 0:
            raise ValueError(f"T20.35c required trainable prefix is missing: {prefix}")
        counts[prefix] = count
    return counts


def verify_tensor_manifest(
    payload: Any, *, trainable_parameter_names: list[str]
) -> int:
    if (
        not isinstance(payload, list)
        or [row.get("name") for row in payload if isinstance(row, dict)]
        != trainable_parameter_names
    ):
        raise ValueError("T20.35c trainable tensor manifest names drifted")
    total = 0
    for row in payload:
        shape = row.get("shape")
        if (
            not isinstance(shape, list)
            or not shape
            or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in shape)
            or row.get("dtype") != "torch.float32"
            or isinstance(row.get("numel"), bool)
            or not isinstance(row.get("numel"), int)
            or row["numel"] <= 0
        ):
            raise ValueError("T20.35c trainable tensor shape, dtype, or size drifted")
        product = 1
        for dimension in shape:
            product *= dimension
        if product != row["numel"]:
            raise ValueError("T20.35c trainable tensor numel drifted")
        total += product
    return total


def load_t20_35_result(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = load_strict_json(Path(repo_root) / T20_35_RESULT_PATH)
    verify_signed_payload(result, label="frozen T20.35 rank-capacity result")
    if (
        result.get("identity_sha256") != EXPECTED_T20_35_RESULT_IDENTITY
        or result.get("schema_version")
        != "scenesmith.t20_35_rank_capacity_result.v1"
        or result.get("task_id") != "T20.35"
        or result.get("decision") != "gate_b_fail"
        or result.get("gate_b_one_batch_memorization_passed") is not False
    ):
        raise ValueError("T20.35c frozen rank-capacity comparison drifted")
    return result


def build_result(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    run: dict[str, Any],
    t20_35_result: dict[str, Any],
    t20_33_spec: dict[str, Any],
    correction: dict[str, Any],
) -> dict[str, Any]:
    verify_training_spec(
        spec, t20_33_spec=t20_33_spec, correction=correction
    )
    verify_run(
        run,
        spec=spec,
        authority_identity=authority_identity,
        t20_33_spec=t20_33_spec,
        correction=correction,
    )
    _sha(authority_identity, "authority identity")
    if t20_35_result.get("identity_sha256") != EXPECTED_T20_35_RESULT_IDENTITY:
        raise ValueError("T20.35c comparison result identity drifted")
    verify_signed_payload(t20_35_result, label="T20.35c comparison result")
    baseline = _finite(run.get("baseline_objective_mean"), "baseline objective")
    final = _finite(run.get("final_objective_mean"), "final objective")
    if baseline <= 0:
        raise ValueError("T20.35c baseline objective must be positive")
    ratio = final / baseline
    chunks = run["decoded_action_chunks"]
    action_pass = all(
        float(row["maximum_absolute_error_rad"]) <= MAX_ACTION_ERROR_RAD
        for row in chunks
    )
    objective_pass = ratio <= MAX_OBJECTIVE_RATIO
    passed = action_pass and objective_pass
    prior_ratio = _finite(
        t20_35_result.get("final_to_baseline_objective_ratio"),
        "T20.35 objective ratio",
    )
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35c",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "run_identity_sha256": run["identity_sha256"],
            "t20_35_result_identity_sha256": t20_35_result["identity_sha256"],
            "adaptation_mode": ADAPTATION_MODE,
            "t20_35_rank_16_final_to_baseline_objective_ratio": prior_ratio,
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "baseline_objective_mean": baseline,
            "final_objective_mean": final,
            "final_to_baseline_objective_ratio": ratio,
            "objective_ratio_change_from_t20_35_rank_16": ratio - prior_ratio,
            "maximum_allowed_objective_ratio": MAX_OBJECTIVE_RATIO,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "decoded_action_chunks": chunks,
            "all_decoded_chunks_within_threshold": action_pass,
            "objective_ratio_within_threshold": objective_pass,
            "gate_b_one_batch_memorization_passed": passed,
            "decision": "gate_b_pass" if passed else "gate_b_fail",
            "selected_next_hypothesis": _next_hypothesis(
                action_pass=action_pass,
                objective_pass=objective_pass,
            ),
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "twin_updated": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_run(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    t20_33_spec: dict[str, Any],
    correction: dict[str, Any],
) -> None:
    verify_training_spec(
        spec, t20_33_spec=t20_33_spec, correction=correction
    )
    _sha(authority_identity, "authority identity")
    verify_signed_payload(payload, label="T20.35c expert-only run")
    if (
        payload.get("schema_version") != RUN_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35c"
        or payload.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("optimizer_update_count") != OPTIMIZER_UPDATES
        or payload.get("training_seed") != TRAINING_SEED
        or payload.get("fixed_dataset_index") != FRAME_INDEX
        or payload.get("fixed_source_seed") != SOURCE_SEED
        or payload.get("action_horizon") != ACTION_HORIZON
        or payload.get("learning_rate") != LEARNING_RATE
        or payload.get("adaptation_mode") != ADAPTATION_MODE
        or payload.get("peft_wrapper_used") is not False
        or payload.get("train_expert_only") is not True
        or payload.get("freeze_vision_encoder") is not True
        or payload.get("trainable_prefixes") != list(TRAINABLE_PREFIXES)
        or payload.get("paligemma_trainable_parameter_count") != 0
        or payload.get("trainable_boundary_complete") is not True
        or payload.get("lerobot_stack_identity_sha256")
        != spec["lerobot_stack_identity_sha256"]
        or payload.get("source_measured_action_chunk_sha256")
        != spec["source_batch"]["measured_action_chunk_sha256"]
        or payload.get("dataset_action_chunk_sha256")
        != EXPECTED_DATASET_ACTION_CHUNK_SHA256
    ):
        raise ValueError("T20.35c run adaptation, batch, campaign, or authority drifted")
    names = payload.get("trainable_parameter_names")
    counts = verify_parameter_boundary(
        all_parameter_names=payload.get("all_parameter_names"),
        trainable_parameter_names=names,
    )
    if payload.get("required_prefix_parameter_counts") != counts:
        raise ValueError("T20.35c required-prefix parameter counts drifted")
    manifest_total = verify_tensor_manifest(
        payload.get("trainable_tensor_manifest"),
        trainable_parameter_names=names,
    )
    for field in (
        "attempt_identity_sha256",
        "lerobot_stack_identity_sha256",
        "source_measured_action_chunk_sha256",
        "dataset_action_chunk_sha256",
        "checkpoint_identity_sha256",
        "all_parameter_names_sha256",
        "trainable_parameter_names_sha256",
    ):
        _sha(payload.get(field), field)
    if hashlib.sha256(canonical_json_bytes(payload["all_parameter_names"])).hexdigest() != payload[
        "all_parameter_names_sha256"
    ]:
        raise ValueError("T20.35c all-parameter name identity drifted")
    if hashlib.sha256(canonical_json_bytes(names)).hexdigest() != payload[
        "trainable_parameter_names_sha256"
    ]:
        raise ValueError("T20.35c trainable-name identity drifted")
    for field in (
        "all_parameter_count",
        "trainable_parameter_count",
        "paligemma_parameter_count",
    ):
        if isinstance(payload.get(field), bool) or not isinstance(payload.get(field), int) or payload[field] <= 0:
            raise ValueError(f"T20.35c {field} is invalid")
    if (
        manifest_total != payload["trainable_parameter_count"]
        or payload["trainable_parameter_count"] >= payload["all_parameter_count"]
        or payload["paligemma_parameter_count"] >= payload["all_parameter_count"]
    ):
        raise ValueError("T20.35c parameter element accounting drifted")
    tree = payload.get("checkpoint_tree")
    if not isinstance(tree, list) or not tree:
        raise ValueError("T20.35c checkpoint tree is missing")
    required = {"expert_only_config.json", "expert_only_model.safetensors"}
    if not required.issubset({row.get("path") for row in tree if isinstance(row, dict)}):
        raise ValueError("T20.35c checkpoint tree is incomplete")
    if hashlib.sha256(canonical_json_bytes(tree)).hexdigest() != payload[
        "checkpoint_identity_sha256"
    ]:
        raise ValueError("T20.35c checkpoint identity drifted")
    losses = payload.get("per_update_objective")
    gradients = payload.get("gradient_norms_before_clip")
    if not isinstance(losses, list) or len(losses) != OPTIMIZER_UPDATES:
        raise ValueError("T20.35c run loss trace is incomplete")
    if not isinstance(gradients, list) or len(gradients) != OPTIMIZER_UPDATES:
        raise ValueError("T20.35c run gradient trace is incomplete")
    for value in [payload.get("baseline_objective_mean"), payload.get("final_objective_mean"), *losses, *gradients]:
        _finite(value, "run numeric evidence")
    chunks = payload.get("decoded_action_chunks")
    if not isinstance(chunks, list) or [row.get("inference_seed") for row in chunks] != list(INFERENCE_SEEDS):
        raise ValueError("T20.35c run inference seed coverage drifted")
    for row in chunks:
        _sha(row.get("decoded_action_chunk_sha256"), "decoded action chunk")
        _finite(row.get("mean_absolute_error_rad"), "chunk mean error")
        _finite(row.get("maximum_absolute_error_rad"), "chunk maximum error")
    required_false = (
        "closed_loop_rollout", "dataset_mutated", "statistics_changed",
        "twin_updated", "simulation_policy_accepted", "physical_actuation",
        "external_compute_started", "brev_compute_started",
        "physical_transfer_ready", "promotion_eligible",
    )
    if payload.get("optimizer_training") is not True or any(payload.get(field) is not False for field in required_false):
        raise ValueError("T20.35c run execution or authority fields drifted")


def verify_result(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    run: dict[str, Any],
    t20_35_result: dict[str, Any],
    t20_33_spec: dict[str, Any],
    correction: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.35c expert-only result")
    expected = build_result(
        spec=spec,
        authority_identity=payload.get("authority_decision_identity_sha256"),
        run=run,
        t20_35_result=t20_35_result,
        t20_33_spec=t20_33_spec,
        correction=correction,
    )
    if payload != expected:
        raise ValueError("T20.35c result drifted from run evidence")


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"T20.35c {label} must be finite")
    return float(value)


def _next_hypothesis(*, action_pass: bool, objective_pass: bool) -> str:
    if action_pass and objective_pass:
        return "gate_b_expert_only_capacity_ceiling_pass_route_t20_36"
    if objective_pass:
        return "gate_b_objective_pass_action_fail_route_decoded_action_residual_localization"
    if action_pass:
        return "gate_b_action_pass_objective_fail_route_objective_floor_audit"
    return "gate_b_expert_only_both_fail_route_loss_action_attainability_audit"


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"T20.35c {label} must be lowercase SHA-256")
    return value

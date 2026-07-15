"""Fail-closed Gate B rank-capacity discriminator for T20.35."""

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
    RESULT_PATH as T20_33_RESULT_PATH,
    SOURCE_SEED,
    SPEC_PATH as T20_33_SPEC_PATH,
    TRAINING_SEED,
    verify_training_spec as verify_t20_33_training_spec,
    verify_training_spec_file as verify_t20_33_training_spec_file,
    verify_preflight as verify_t20_33_preflight,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_35_rank_capacity_training_spec.json")
RESULT_PATH = Path("configurations/robot_lab/t20_35_rank_capacity_result.json")
SCHEMA_VERSION = "scenesmith.t20_35_rank_capacity_training_spec.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_35_rank_capacity_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_35_rank_capacity_result.v1"
LORA_RANK = 16
LORA_ALPHA = 16
EXPECTED_PEFT_TARGET_MODULES = (
    r"(.*\.gemma_expert\..*\.self_attn\.(q|v)_proj|model\."
    r"(state_proj|action_in_proj|action_out_proj|action_time_mlp_in|"
    r"action_time_mlp_out))"
)
EXPECTED_T20_33_RESULT_IDENTITY = (
    "27cd2be30916234e5eff18eb350449a47b648a9baf0a48e8fe50eb74dc2138ee"
)


def build_training_spec(*, t20_33_spec: dict[str, Any]) -> dict[str, Any]:
    """Derive T20.35 mechanically from the frozen T20.33 specification."""
    verify_t20_33_training_spec(t20_33_spec)
    payload = copy.deepcopy(t20_33_spec)
    payload.pop("identity_sha256", None)
    payload["schema_version"] = SCHEMA_VERSION
    payload["task_id"] = "T20.35"
    payload["scope"] = "gate_b_same_batch_rank_16_capacity_discriminator"
    payload["t20_33_training_spec_identity_sha256"] = t20_33_spec[
        "identity_sha256"
    ]
    payload["model"]["lora_rank"] = LORA_RANK
    payload["model"]["lora_alpha"] = LORA_ALPHA
    return sign_payload(payload)


def verify_training_spec(
    payload: dict[str, Any], *, t20_33_spec: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35 rank-capacity training spec")
    expected = build_training_spec(t20_33_spec=t20_33_spec)
    if payload != expected:
        raise ValueError("T20.35 training spec drifted beyond rank/alpha")


def verify_preflight(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    activate_lerobot_stack(repo_root=Path(repo_root), stage="training")
    t20_33_spec = verify_t20_33_training_spec_file(repo_root=repo_root)
    t20_33_preflight = verify_t20_33_preflight(repo_root=repo_root)
    spec = build_training_spec(t20_33_spec=t20_33_spec)
    verify_training_spec(spec, t20_33_spec=t20_33_spec)
    return {
        "training_spec": spec,
        "t20_33_training_spec": t20_33_spec,
        "source_episode": t20_33_preflight["source_episode"],
        "source_entry": t20_33_preflight["source_entry"],
    }


def verify_training_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    preflight = verify_preflight(repo_root=root)
    archived = load_strict_json(root / SPEC_PATH)
    verify_training_spec(
        archived, t20_33_spec=preflight["t20_33_training_spec"]
    )
    if archived != preflight["training_spec"]:
        raise ValueError("T20.35 training spec drifted from T20.33 source")
    return archived


def verify_t20_33_result(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="frozen T20.33 one-batch result")
    if (
        payload.get("schema_version")
        != "scenesmith.t20_33_one_batch_result.v1"
        or payload.get("task_id") != "T20.33"
        or payload.get("identity_sha256") != EXPECTED_T20_33_RESULT_IDENTITY
        or payload.get("decision") != "gate_b_fail"
        or payload.get("gate_b_one_batch_memorization_passed") is not False
    ):
        raise ValueError("T20.35 frozen T20.33 comparison result drifted")


def load_t20_33_result(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = load_strict_json(Path(repo_root) / T20_33_RESULT_PATH)
    verify_t20_33_result(result)
    return result


def build_result(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    run: dict[str, Any],
    t20_33_result: dict[str, Any],
) -> dict[str, Any]:
    t20_33_spec = load_strict_json(REPO_ROOT / T20_33_SPEC_PATH)
    verify_training_spec(spec, t20_33_spec=t20_33_spec)
    verify_run(run, spec=spec, authority_identity=authority_identity)
    verify_t20_33_result(t20_33_result)
    _sha(authority_identity, "authority identity")
    losses = run.get("per_update_objective")
    gradients = run.get("gradient_norms_before_clip")
    if not isinstance(losses, list) or len(losses) != OPTIMIZER_UPDATES:
        raise ValueError("T20.35 loss trace is incomplete")
    if not isinstance(gradients, list) or len(gradients) != OPTIMIZER_UPDATES:
        raise ValueError("T20.35 gradient trace is incomplete")
    baseline = _finite(run.get("baseline_objective_mean"), "baseline objective")
    final = _finite(run.get("final_objective_mean"), "final objective")
    if baseline <= 0:
        raise ValueError("T20.35 baseline objective must be positive")
    chunks = run["decoded_action_chunks"]
    ratio = final / baseline
    action_pass = all(
        float(row["maximum_absolute_error_rad"]) <= MAX_ACTION_ERROR_RAD
        for row in chunks
    )
    objective_pass = ratio <= MAX_OBJECTIVE_RATIO
    passed = action_pass and objective_pass
    prior_ratio = _finite(
        t20_33_result.get("final_to_baseline_objective_ratio"),
        "T20.33 objective ratio",
    )
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "run_identity_sha256": _sha(
                run.get("identity_sha256"), "run identity"
            ),
            "t20_33_result_identity_sha256": t20_33_result["identity_sha256"],
            "t20_33_rank": 4,
            "t20_35_rank": LORA_RANK,
            "t20_33_final_to_baseline_objective_ratio": prior_ratio,
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "baseline_objective_mean": baseline,
            "final_objective_mean": final,
            "final_to_baseline_objective_ratio": ratio,
            "objective_ratio_change_from_t20_33": ratio - prior_ratio,
            "maximum_allowed_objective_ratio": MAX_OBJECTIVE_RATIO,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "decoded_action_chunks": chunks,
            "all_decoded_chunks_within_threshold": action_pass,
            "objective_ratio_within_threshold": objective_pass,
            "gate_b_one_batch_memorization_passed": passed,
            "decision": "gate_b_pass" if passed else "gate_b_fail",
            "selected_next_hypothesis": (
                "gate_b_corrected_rank_capacity"
                if passed
                else "gate_b_rank_capacity_insufficient_route_t20_35_x"
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
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    t20_33_spec = load_strict_json(REPO_ROOT / T20_33_SPEC_PATH)
    verify_training_spec(spec, t20_33_spec=t20_33_spec)
    _sha(authority_identity, "authority identity")
    verify_signed_payload(payload, label="T20.35 rank-capacity run")
    if (
        payload.get("schema_version") != RUN_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35"
        or payload.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("optimizer_update_count") != OPTIMIZER_UPDATES
        or payload.get("training_seed") != TRAINING_SEED
        or payload.get("fixed_dataset_index") != FRAME_INDEX
        or payload.get("fixed_source_seed") != SOURCE_SEED
        or payload.get("action_horizon") != ACTION_HORIZON
        or payload.get("learning_rate") != LEARNING_RATE
        or payload.get("lora_rank") != LORA_RANK
        or payload.get("lora_alpha") != LORA_ALPHA
        or payload.get("peft_target_modules") != EXPECTED_PEFT_TARGET_MODULES
        or isinstance(payload.get("trainable_parameter_count"), bool)
        or not isinstance(payload.get("trainable_parameter_count"), int)
        or payload.get("trainable_parameter_count") <= 0
    ):
        raise ValueError("T20.35 run rank, batch, campaign, or authority drifted")
    for field in (
        "attempt_identity_sha256",
        "lerobot_stack_identity_sha256",
        "source_measured_action_chunk_sha256",
        "dataset_action_chunk_sha256",
        "checkpoint_identity_sha256",
        "trainable_parameter_names_sha256",
    ):
        _sha(payload.get(field), field)
    tree = payload.get("checkpoint_tree")
    if not isinstance(tree, list) or not tree:
        raise ValueError("T20.35 checkpoint tree is missing")
    required = {"adapter_config.json", "adapter_model.safetensors"}
    if not required.issubset(
        {row.get("path") for row in tree if isinstance(row, dict)}
    ):
        raise ValueError("T20.35 checkpoint tree is incomplete")
    if hashlib.sha256(canonical_json_bytes(tree)).hexdigest() != payload[
        "checkpoint_identity_sha256"
    ]:
        raise ValueError("T20.35 checkpoint identity drifted")
    losses = payload.get("per_update_objective")
    gradients = payload.get("gradient_norms_before_clip")
    if not isinstance(losses, list) or len(losses) != OPTIMIZER_UPDATES:
        raise ValueError("T20.35 run loss trace is incomplete")
    if not isinstance(gradients, list) or len(gradients) != OPTIMIZER_UPDATES:
        raise ValueError("T20.35 run gradient trace is incomplete")
    for value in [
        payload.get("baseline_objective_mean"),
        payload.get("final_objective_mean"),
        *losses,
        *gradients,
    ]:
        _finite(value, "run numeric evidence")
    chunks = payload.get("decoded_action_chunks")
    if not isinstance(chunks, list) or [
        row.get("inference_seed") for row in chunks
    ] != list(INFERENCE_SEEDS):
        raise ValueError("T20.35 run inference seed coverage drifted")
    for row in chunks:
        _sha(row.get("decoded_action_chunk_sha256"), "decoded action chunk")
        _finite(row.get("mean_absolute_error_rad"), "chunk mean error")
        _finite(row.get("maximum_absolute_error_rad"), "chunk maximum error")
    required_false = (
        "closed_loop_rollout",
        "dataset_mutated",
        "statistics_changed",
        "twin_updated",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if payload.get("optimizer_training") is not True or any(
        payload.get(field) is not False for field in required_false
    ):
        raise ValueError("T20.35 run execution or authority fields drifted")


def verify_result(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    run: dict[str, Any],
    t20_33_result: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.35 rank-capacity result")
    expected = build_result(
        spec=spec,
        authority_identity=payload.get("authority_decision_identity_sha256"),
        run=run,
        t20_33_result=t20_33_result,
    )
    if payload != expected:
        raise ValueError("T20.35 result drifted from run evidence")


def _finite(value: Any, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"T20.35 {label} must be finite")
    return float(value)


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35 {label} must be lowercase SHA-256")
    return value

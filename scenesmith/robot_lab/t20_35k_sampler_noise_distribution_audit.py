"""Model-free PI0.5 sampler and padded-action noise audit for T20.35k."""

from __future__ import annotations

import ast
import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_35j_initial_noise_scale_discriminator import (
    ATTEMPT_PATH as T20_35J_ATTEMPT_PATH,
    RESULT_PATH as T20_35J_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35j_sources,
    verify_attempt_marker as verify_t20_35j_attempt,
    verify_result as verify_t20_35j_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_35k_sampler_noise_distribution_audit.json"
)
CONFIG_SOURCE_NAME = "configuration_pi05.py"
SCHEMA_VERSION = "scenesmith.t20_35k_sampler_noise_distribution_audit.v1"
EXPECTED_T20_35J_RESULT_IDENTITY = (
    "e9bbff84864a838f64e67c72a4996fd4eefe13739294becc43a371268f3da75a"
)
_CONTRACT_KEYS = {
    "sampler_distribution",
    "sampler_mean",
    "sampler_standard_deviation",
    "sampler_dtype",
    "training_uses_same_standard_normal_sampler",
    "training_time_distribution",
    "training_time_beta_alpha",
    "training_time_beta_beta",
    "training_time_scale",
    "training_time_offset",
    "training_time_affine_support_minimum",
    "training_time_affine_support_maximum",
    "training_interpolation",
    "training_velocity_target",
    "inference_initial_state",
    "inference_euler_step_expression",
    "inference_time_expression",
    "inference_time_grid",
    "chunk_size",
    "num_inference_steps",
    "supervised_action_dimension_count",
    "maximum_action_dimension_count",
    "padded_action_dimension_count",
    "training_action_padded_to_max_action_dim",
    "inference_noise_uses_max_action_dim",
    "training_loss_truncated_to_supervised_action_dim",
    "returned_actions_truncated_to_supervised_action_dim",
    "stochastic_padded_dimensions_enter_action_projection",
    "padded_dimensions_receive_direct_loss",
}


def extract_sampler_contract(
    *,
    model_source: str,
    config_source: str,
    action_dimension_count: int,
) -> dict[str, Any]:
    """Extract the exact audited semantics from source text without importing it."""
    if not isinstance(model_source, str) or not model_source.strip():
        raise ValueError("T20.35k model source is missing")
    if not isinstance(config_source, str) or not config_source.strip():
        raise ValueError("T20.35k configuration source is missing")
    if (
        isinstance(action_dimension_count, bool)
        or not isinstance(action_dimension_count, int)
        or action_dimension_count <= 0
    ):
        raise ValueError("T20.35k action dimension count is invalid")
    try:
        model_tree = ast.parse(model_source)
        config_tree = ast.parse(config_source)
    except SyntaxError as error:
        raise ValueError("T20.35k source is not valid Python") from error

    model_class = _class(model_tree, "PI05Pytorch")
    policy_class = _class(model_tree, "PI05Policy")
    config_class = _class(config_tree, "PI05Config")
    model_init = _method(model_class, "__init__")
    sample_noise = _method(model_class, "sample_noise")
    sample_time = _method(model_class, "sample_time")
    model_forward = _method(model_class, "forward")
    sample_actions = _method(model_class, "sample_actions")
    embed_suffix = _method(model_class, "embed_suffix")
    prepare_action = _method(policy_class, "prepare_action")
    predict_action_chunk = _method(policy_class, "predict_action_chunk")
    policy_forward = _method(policy_class, "forward")

    sampler_call = _single_return_call(sample_noise, "torch.normal")
    keywords = {item.arg: item.value for item in sampler_call.keywords}
    if set(keywords) != {"mean", "std", "size", "dtype", "device"}:
        raise ValueError("T20.35k sampler keyword contract drifted")
    sampler_mean = _literal_number(keywords["mean"], "sampler mean")
    sampler_std = _literal_number(keywords["std"], "sampler standard deviation")
    if sampler_mean != 0.0 or sampler_std != 1.0:
        raise ValueError("T20.35k sampler is not standard normal")
    _require_expression(keywords["size"], "shape", "sampler size")
    _require_expression(keywords["dtype"], "torch.float32", "sampler dtype")
    _require_expression(keywords["device"], "device", "sampler device")

    _require_assignment(
        sample_time,
        "time_beta",
        "sample_beta(self.config.time_sampling_beta_alpha, "
        "self.config.time_sampling_beta_beta, bsize, device)",
    )
    _require_assignment(
        sample_time,
        "time",
        "time_beta * self.config.time_sampling_scale + "
        "self.config.time_sampling_offset",
    )
    _require_assignment(
        model_forward,
        "x_t",
        "time_expanded * noise + (1 - time_expanded) * actions",
    )
    _require_assignment(model_forward, "u_t", "noise - actions")
    _require_assignment(
        sample_actions,
        "actions_shape",
        "(bsize, self.config.chunk_size, self.config.max_action_dim)",
    )
    _require_assignment(sample_actions, "noise", "self.sample_noise(actions_shape, device)")
    _require_assignment(sample_actions, "dt", "-1.0 / num_steps")
    _require_assignment(sample_actions, "x_t", "noise")
    _require_assignment(sample_actions, "time", "1.0 + step * dt")
    _require_assignment(sample_actions, "x_t", "x_t + dt * v_t")
    _require_linear_input(model_init, "action_in_proj", "config.max_action_dim", 0)
    _require_linear_input(model_init, "action_out_proj", "config.max_action_dim", -1)
    _require_call(embed_suffix, "self.action_in_proj(noisy_actions)")

    _require_assignment(
        prepare_action,
        "actions",
        "pad_vector(batch[ACTION], self.config.max_action_dim)",
    )
    _require_assignment(policy_forward, "actions", "self.prepare_action(batch)")
    _require_assignment(
        policy_forward,
        "noise",
        "self.model.sample_noise(actions.shape, actions.device)",
    )
    _require_assignment(
        policy_forward,
        "time",
        "self.model.sample_time(actions.shape[0], actions.device)",
    )
    _require_assignment(
        policy_forward,
        "losses",
        "losses[:, :, :original_action_dim]",
    )
    _require_assignment(
        predict_action_chunk,
        "actions",
        "actions[:, :, :original_action_dim]",
    )
    for function in (policy_forward, predict_action_chunk):
        _require_assignment(
            function,
            "original_action_dim",
            "self.config.output_features[ACTION].shape[0]",
        )

    chunk_size = _config_number(config_class, "chunk_size", integer=True)
    max_action_dim = _config_number(config_class, "max_action_dim", integer=True)
    num_steps = _config_number(config_class, "num_inference_steps", integer=True)
    beta_alpha = _config_number(config_class, "time_sampling_beta_alpha")
    beta_beta = _config_number(config_class, "time_sampling_beta_beta")
    time_scale = _config_number(config_class, "time_sampling_scale")
    time_offset = _config_number(config_class, "time_sampling_offset")
    if action_dimension_count > max_action_dim:
        raise ValueError("T20.35k action dimensions exceed the configured maximum")
    if chunk_size <= 0 or max_action_dim <= 0 or num_steps <= 0:
        raise ValueError("T20.35k dimensional or cadence configuration is invalid")
    if beta_alpha <= 0 or beta_beta <= 0 or time_scale <= 0:
        raise ValueError("T20.35k training-time distribution is invalid")
    padded = max_action_dim - action_dimension_count
    time_grid = [round(1.0 - step / num_steps, 12) for step in range(num_steps)]
    return {
        "sampler_distribution": "normal",
        "sampler_mean": sampler_mean,
        "sampler_standard_deviation": sampler_std,
        "sampler_dtype": "torch.float32",
        "training_uses_same_standard_normal_sampler": True,
        "training_time_distribution": "beta_affine",
        "training_time_beta_alpha": beta_alpha,
        "training_time_beta_beta": beta_beta,
        "training_time_scale": time_scale,
        "training_time_offset": time_offset,
        "training_time_affine_support_minimum": time_offset,
        "training_time_affine_support_maximum": time_offset + time_scale,
        "training_interpolation": "x_t = time * noise + (1 - time) * actions",
        "training_velocity_target": "u_t = noise - actions",
        "inference_initial_state": "x_t = noise",
        "inference_euler_step_expression": "x_t = x_t + (-1 / num_steps) * v_t",
        "inference_time_expression": "time = 1 + step * (-1 / num_steps)",
        "inference_time_grid": time_grid,
        "chunk_size": chunk_size,
        "num_inference_steps": num_steps,
        "supervised_action_dimension_count": action_dimension_count,
        "maximum_action_dimension_count": max_action_dim,
        "padded_action_dimension_count": padded,
        "training_action_padded_to_max_action_dim": True,
        "inference_noise_uses_max_action_dim": True,
        "training_loss_truncated_to_supervised_action_dim": True,
        "returned_actions_truncated_to_supervised_action_dim": True,
        "stochastic_padded_dimensions_enter_action_projection": padded > 0,
        "padded_dimensions_receive_direct_loss": False,
    }


def build_sampler_noise_distribution_audit(
    *,
    t20_35j_result_identity: str,
    model_source_sha256: str,
    config_source_sha256: str,
    contract: dict[str, Any],
    initial_noise_scale_effect_positive: bool,
    gate_b_passed: bool,
    selected_initial_noise_scale: float,
) -> dict[str, Any]:
    for value, label in (
        (t20_35j_result_identity, "T20.35j result identity"),
        (model_source_sha256, "model source SHA-256"),
        (config_source_sha256, "configuration source SHA-256"),
    ):
        _sha(value, label)
    normalized = _normalize_contract(contract)
    if (
        initial_noise_scale_effect_positive is not True
        or gate_b_passed is not False
        or isinstance(selected_initial_noise_scale, bool)
        or not isinstance(selected_initial_noise_scale, (int, float))
        or not math.isfinite(float(selected_initial_noise_scale))
        or float(selected_initial_noise_scale) != 0.0
    ):
        raise ValueError("T20.35k T20.35j result route drifted")
    distribution_match = (
        normalized["sampler_distribution"] == "normal"
        and normalized["sampler_mean"] == 0.0
        and normalized["sampler_standard_deviation"] == 1.0
        and normalized["training_uses_same_standard_normal_sampler"]
        and normalized["inference_initial_state"] == "x_t = noise"
    )
    padded_exposure = (
        normalized["padded_action_dimension_count"] > 0
        and normalized["training_action_padded_to_max_action_dim"]
        and normalized["inference_noise_uses_max_action_dim"]
        and normalized["stochastic_padded_dimensions_enter_action_projection"]
        and normalized["training_loss_truncated_to_supervised_action_dim"]
        and not normalized["padded_dimensions_receive_direct_loss"]
    )
    if not distribution_match:
        classification = "train_inference_noise_distribution_mismatch"
        route = "correct_train_inference_noise_distribution_mismatch"
    elif padded_exposure:
        classification = (
            "matched_standard_normal_sampler_with_unsupervised_padded_noise_exposure"
        )
        route = "run_separately_reviewed_active_vs_padded_noise_mask_discriminator"
    else:
        classification = "matched_sampler_without_unsupervised_padded_noise_exposure"
        route = "audit_model_flow_consistency_along_integration_path"
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35k",
            "scope": "model_free_active_runtime_sampler_and_padded_action_noise_audit",
            "t20_35j_result_identity_sha256": t20_35j_result_identity,
            "model_source_path": (
                "external/leLab/.venv/lib/python3.12/site-packages/lerobot/"
                "policies/pi05/modeling_pi05.py"
            ),
            "model_source_sha256": model_source_sha256,
            "config_source_path": (
                "external/leLab/.venv/lib/python3.12/site-packages/lerobot/"
                "policies/pi05/configuration_pi05.py"
            ),
            "config_source_sha256": config_source_sha256,
            "source_contract": normalized,
            "default_train_inference_noise_distribution_match": distribution_match,
            "supervised_action_dimension_count": normalized[
                "supervised_action_dimension_count"
            ],
            "maximum_action_dimension_count": normalized[
                "maximum_action_dimension_count"
            ],
            "padded_action_dimension_count": normalized[
                "padded_action_dimension_count"
            ],
            "stochastic_padded_dimensions_enter_action_projection": normalized[
                "stochastic_padded_dimensions_enter_action_projection"
            ],
            "padded_dimensions_receive_direct_loss": normalized[
                "padded_dimensions_receive_direct_loss"
            ],
            "half_and_zero_initial_noise_are_off_default_prior": True,
            "initial_noise_scale_effect_positive": True,
            "selected_initial_noise_scale": 0.0,
            "sampler_classification": classification,
            "selected_next_hypothesis": route,
            "gate_b_passed": False,
            "source_read_only": True,
            "model_imported": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_read": False,
            "checkpoint_mutated": False,
            "dataset_read": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "sampler_mutated": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_sampler_noise_distribution_audit(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.35k sampler/noise-distribution audit")
    expected = build_sampler_noise_distribution_audit(
        t20_35j_result_identity=payload.get("t20_35j_result_identity_sha256"),
        model_source_sha256=payload.get("model_source_sha256"),
        config_source_sha256=payload.get("config_source_sha256"),
        contract=payload.get("source_contract"),
        initial_noise_scale_effect_positive=payload.get(
            "initial_noise_scale_effect_positive"
        ),
        gate_b_passed=payload.get("gate_b_passed"),
        selected_initial_noise_scale=payload.get("selected_initial_noise_scale"),
    )
    if payload != expected:
        raise ValueError("T20.35k sampler/noise-distribution audit drifted")


def build_live_sampler_noise_distribution_audit(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35j_sources(repo_root=root)
    spec = sources["noise_scale_spec"]
    permit = sources["noise_scale_permit"]
    attempt = load_strict_json(root / T20_35J_ATTEMPT_PATH)
    verify_t20_35j_attempt(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
    )
    result = load_strict_json(root / T20_35J_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35j_result(
        result,
        spec=spec,
        permit=permit,
        attempt=attempt,
        target_chunk=target,
    )
    if result["identity_sha256"] != EXPECTED_T20_35J_RESULT_IDENTITY:
        raise ValueError("T20.35k expected T20.35j result identity drifted")
    action_dimensions = {len(row) for row in target if isinstance(row, list)}
    if len(action_dimensions) != 1:
        raise ValueError("T20.35k source action dimensionality is ambiguous")
    model_path = root / spec["sampler_source_path"]
    config_path = model_path.with_name(CONFIG_SOURCE_NAME)
    model_bytes = model_path.read_bytes()
    config_bytes = config_path.read_bytes()
    model_sha = hashlib.sha256(model_bytes).hexdigest()
    config_sha = hashlib.sha256(config_bytes).hexdigest()
    if model_sha != spec["sampler_source_sha256"]:
        raise ValueError("T20.35k active model source drifted from T20.35j")
    contract = extract_sampler_contract(
        model_source=model_bytes.decode("utf-8"),
        config_source=config_bytes.decode("utf-8"),
        action_dimension_count=next(iter(action_dimensions)),
    )
    audit = build_sampler_noise_distribution_audit(
        t20_35j_result_identity=result["identity_sha256"],
        model_source_sha256=model_sha,
        config_source_sha256=config_sha,
        contract=contract,
        initial_noise_scale_effect_positive=result[
            "initial_noise_scale_effect_positive"
        ],
        gate_b_passed=result["gate_b_passed"],
        selected_initial_noise_scale=result["selected_initial_noise_scale"],
    )
    verify_sampler_noise_distribution_audit(audit)
    return audit


def write_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    audit = build_live_sampler_noise_distribution_audit(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / AUDIT_PATH, audit)
    return audit


def verify_audit_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = build_live_sampler_noise_distribution_audit(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / AUDIT_PATH)
    verify_sampler_noise_distribution_audit(archived)
    if archived != expected:
        raise ValueError("T20.35k archived audit drifted from active sources")
    return archived


def _normalize_contract(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _CONTRACT_KEYS:
        raise ValueError("T20.35k source contract schema drifted")
    result = dict(value)
    for key in (
        "sampler_mean",
        "sampler_standard_deviation",
        "training_time_beta_alpha",
        "training_time_beta_beta",
        "training_time_scale",
        "training_time_offset",
        "training_time_affine_support_minimum",
        "training_time_affine_support_maximum",
    ):
        item = result[key]
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"T20.35k {key} is not finite")
        result[key] = float(item)
        if not math.isfinite(result[key]):
            raise ValueError(f"T20.35k {key} is not finite")
    for key in (
        "chunk_size",
        "num_inference_steps",
        "supervised_action_dimension_count",
        "maximum_action_dimension_count",
        "padded_action_dimension_count",
    ):
        item = result[key]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise ValueError(f"T20.35k {key} is invalid")
    if (
        result["chunk_size"] <= 0
        or result["num_inference_steps"] <= 0
        or result["supervised_action_dimension_count"] <= 0
        or result["maximum_action_dimension_count"]
        != result["supervised_action_dimension_count"]
        + result["padded_action_dimension_count"]
    ):
        raise ValueError("T20.35k source contract dimensions drifted")
    for key in (
        "training_uses_same_standard_normal_sampler",
        "training_action_padded_to_max_action_dim",
        "inference_noise_uses_max_action_dim",
        "training_loss_truncated_to_supervised_action_dim",
        "returned_actions_truncated_to_supervised_action_dim",
        "stochastic_padded_dimensions_enter_action_projection",
        "padded_dimensions_receive_direct_loss",
    ):
        if not isinstance(result[key], bool):
            raise ValueError(f"T20.35k {key} is not boolean")
    for key in (
        "sampler_distribution",
        "sampler_dtype",
        "training_time_distribution",
        "training_interpolation",
        "training_velocity_target",
        "inference_initial_state",
        "inference_euler_step_expression",
        "inference_time_expression",
    ):
        if not isinstance(result[key], str) or not result[key]:
            raise ValueError(f"T20.35k {key} is missing")
    grid = result["inference_time_grid"]
    if not isinstance(grid, list) or len(grid) != result["num_inference_steps"]:
        raise ValueError("T20.35k inference time grid drifted")
    expected_grid = [
        round(1.0 - step / result["num_inference_steps"], 12)
        for step in range(result["num_inference_steps"])
    ]
    if grid != expected_grid:
        raise ValueError("T20.35k inference time grid drifted")
    return result


def _class(tree: ast.AST, name: str) -> ast.ClassDef:
    matches = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"T20.35k expected exactly one {name} class")
    return matches[0]


def _method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(matches) != 1 or not isinstance(matches[0], ast.FunctionDef):
        raise ValueError(f"T20.35k expected exactly one {class_node.name}.{name}")
    return matches[0]


def _expression_dump(expression: str) -> str:
    return ast.dump(ast.parse(expression, mode="eval").body, include_attributes=False)


def _require_expression(node: ast.AST, expression: str, label: str) -> None:
    if ast.dump(node, include_attributes=False) != _expression_dump(expression):
        raise ValueError(f"T20.35k {label} drifted")


def _require_assignment(function: ast.FunctionDef, target: str, expression: str) -> None:
    expected = _expression_dump(expression)
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        assigned = node.targets[0]
        if isinstance(assigned, ast.Name) and assigned.id == target:
            if ast.dump(node.value, include_attributes=False) == expected:
                return
    raise ValueError(f"T20.35k {function.name} assignment {target} drifted")


def _require_call(function: ast.FunctionDef, expression: str) -> None:
    expected = _expression_dump(expression)
    if not any(
        isinstance(node, ast.Call)
        and ast.dump(node, include_attributes=False) == expected
        for node in ast.walk(function)
    ):
        raise ValueError(f"T20.35k {function.name} call drifted")


def _single_return_call(function: ast.FunctionDef, expression_name: str) -> ast.Call:
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    if len(returns) != 1 or not isinstance(returns[0].value, ast.Call):
        raise ValueError(f"T20.35k {function.name} return contract drifted")
    call = returns[0].value
    if ast.unparse(call.func) != expression_name:
        raise ValueError(f"T20.35k {function.name} call target drifted")
    return call


def _literal_number(node: ast.AST, label: str) -> float:
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError) as error:
        raise ValueError(f"T20.35k {label} is not literal") from error
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.35k {label} is not numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"T20.35k {label} is not finite")
    return result


def _require_linear_input(
    function: ast.FunctionDef, attribute: str, expression: str, argument_index: int
) -> None:
    expected = _expression_dump(expression)
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == attribute
            and isinstance(node.value, ast.Call)
            and ast.unparse(node.value.func) == "nn.Linear"
        ):
            resolved_index = (
                argument_index
                if argument_index >= 0
                else len(node.value.args) + argument_index
            )
            if not 0 <= resolved_index < len(node.value.args):
                continue
            argument = node.value.args[resolved_index]
            if ast.dump(argument, include_attributes=False) == expected:
                return
    raise ValueError(f"T20.35k {attribute} dimensional contract drifted")


def _config_number(
    class_node: ast.ClassDef, name: str, *, integer: bool = False
) -> int | float:
    matches = []
    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                matches.append(node.value)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name) and node.targets[0].id == name:
                matches.append(node.value)
    if len(matches) != 1:
        raise ValueError(f"T20.35k configuration field {name} drifted")
    value = _literal_number(matches[0], f"configuration field {name}")
    if integer:
        if not value.is_integer():
            raise ValueError(f"T20.35k configuration field {name} is not integral")
        return int(value)
    return value


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35k {label} must be lowercase SHA-256")

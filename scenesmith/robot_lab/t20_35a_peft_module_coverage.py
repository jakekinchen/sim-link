"""Optimizer-free saved-adapter coverage audit for T20.35a."""

from __future__ import annotations

import hashlib
import math
import re

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_35_rank_capacity_discriminator import (
    EXPECTED_PEFT_TARGET_MODULES as EXPECTED_TARGET_MODULES,
    LORA_ALPHA,
    LORA_RANK,
    RESULT_PATH as T20_35_RESULT_PATH,
    SPEC_PATH as T20_35_SPEC_PATH,
    T20_33_SPEC_PATH,
    load_t20_33_result,
    verify_result as verify_t20_35_result,
    verify_run as verify_t20_35_run,
    verify_training_spec,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path("outputs/robot_lab/t20_35_rank_capacity_run_001")
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
ADAPTER_ROOT = RUN_ROOT / "adapter"
ADAPTER_CONFIG_PATH = ADAPTER_ROOT / "adapter_config.json"
ADAPTER_MODEL_PATH = ADAPTER_ROOT / "adapter_model.safetensors"
AUDIT_PATH = Path("configurations/robot_lab/t20_35a_peft_module_coverage.json")
SCHEMA_VERSION = "scenesmith.t20_35a_peft_module_coverage.v1"
EXPECTED_EXPERT_LAYER_COUNT = 18
REQUIRED_ACTION_STATE_MODULES = (
    "model.state_proj",
    "model.action_in_proj",
    "model.action_out_proj",
    "model.action_time_mlp_in",
    "model.action_time_mlp_out",
)
_KEY_PATTERN = re.compile(
    r"^base_model\.model\.(?P<module>.+)\.lora_(?P<side>[AB])\.weight$"
)
_EXPERT_PATTERN = re.compile(
    r"^model\.paligemma_with_expert\.gemma_expert\.model\.layers\."
    r"(?P<layer>\d+)\.self_attn\.(?P<projection>q_proj|v_proj)$"
)


def build_coverage_audit(
    *,
    t20_35_result_identity: str,
    t20_35_run_identity: str,
    checkpoint_identity: str,
    adapter_config_sha256: str,
    adapter_model_sha256: str,
    target_modules: str,
    tensor_descriptors: list[dict[str, Any]],
    expected_trainable_parameter_count: int,
) -> dict[str, Any]:
    for value, label in (
        (t20_35_result_identity, "T20.35 result identity"),
        (t20_35_run_identity, "T20.35 run identity"),
        (checkpoint_identity, "checkpoint identity"),
        (adapter_config_sha256, "adapter config SHA-256"),
        (adapter_model_sha256, "adapter model SHA-256"),
    ):
        _sha(value, label)
    if target_modules != EXPECTED_TARGET_MODULES:
        raise ValueError("T20.35a PEFT target-module regex drifted")
    if (
        isinstance(expected_trainable_parameter_count, bool)
        or not isinstance(expected_trainable_parameter_count, int)
        or expected_trainable_parameter_count <= 0
    ):
        raise ValueError("T20.35a trainable parameter count is invalid")
    normalized, module_sides = _normalize_tensors(tensor_descriptors)
    if sum(row["element_count"] for row in normalized) != (
        expected_trainable_parameter_count
    ):
        raise ValueError("T20.35a saved tensor elements drift from trainable count")

    modules = []
    expected_expert_modules = _expected_expert_modules()
    actual_expert_modules = set()
    for module_path in sorted(module_sides):
        sides = module_sides[module_path]
        if set(sides) != {"A", "B"}:
            raise ValueError(f"T20.35a unpaired LoRA tensors for {module_path}")
        a_row = sides["A"]
        b_row = sides["B"]
        if a_row["shape"][0] != LORA_RANK or b_row["shape"][1] != LORA_RANK:
            raise ValueError(f"T20.35a LoRA rank drifted for {module_path}")
        category = "action_state" if module_path in REQUIRED_ACTION_STATE_MODULES else "expert_attention"
        if category == "expert_attention":
            match = _EXPERT_PATTERN.fullmatch(module_path)
            if match is None or int(match.group("layer")) >= EXPECTED_EXPERT_LAYER_COUNT:
                raise ValueError(f"T20.35a unexpected wrapped module {module_path}")
            actual_expert_modules.add(module_path)
        modules.append(
            {
                "module_path": module_path,
                "category": category,
                "lora_a_key": a_row["key"],
                "lora_b_key": b_row["key"],
                "lora_a_shape": a_row["shape"],
                "lora_b_shape": b_row["shape"],
                "element_count": a_row["element_count"] + b_row["element_count"],
                "nonzero_count": a_row["nonzero_count"] + b_row["nonzero_count"],
            }
        )
    if actual_expert_modules != expected_expert_modules:
        raise ValueError("T20.35a expert attention module coverage drifted")

    coverage = [
        {
            "module_path": module,
            "wrapped_as_lora_pair": module in module_sides,
        }
        for module in REQUIRED_ACTION_STATE_MODULES
    ]
    missing = sorted(
        row["module_path"] for row in coverage if not row["wrapped_as_lora_pair"]
    )
    passed = not missing
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35a",
            "scope": "optimizer_free_saved_peft_module_and_tensor_coverage",
            "t20_35_result_identity_sha256": t20_35_result_identity,
            "t20_35_run_identity_sha256": t20_35_run_identity,
            "checkpoint_identity_sha256": checkpoint_identity,
            "adapter_config_sha256": adapter_config_sha256,
            "adapter_model_sha256": adapter_model_sha256,
            "declared_target_modules": target_modules,
            "lora_rank": LORA_RANK,
            "lora_alpha": LORA_ALPHA,
            "expected_trainable_parameter_count": expected_trainable_parameter_count,
            "saved_tensor_count": len(normalized),
            "saved_tensor_element_count": sum(
                row["element_count"] for row in normalized
            ),
            "saved_tensor_nonzero_count": sum(
                row["nonzero_count"] for row in normalized
            ),
            "wrapped_module_count": len(modules),
            "expert_attention_layer_count": EXPECTED_EXPERT_LAYER_COUNT,
            "expert_attention_module_count": len(actual_expert_modules),
            "expert_attention_module_coverage_complete": True,
            "tensor_descriptors": [
                {
                    "key": row["key"],
                    "shape": row["shape"],
                    "dtype": row["dtype"],
                    "element_count": row["element_count"],
                    "nonzero_count": row["nonzero_count"],
                    "all_finite": row["all_finite"],
                    "content_sha256": row["content_sha256"],
                }
                for row in normalized
            ],
            "wrapped_modules": modules,
            "required_action_state_module_coverage": coverage,
            "missing_required_action_state_modules": missing,
            "all_required_action_state_pathways_wrapped": passed,
            "decision": "peft_coverage_pass" if passed else "peft_coverage_fail",
            "selected_next_hypothesis": (
                "gate_b_objective_floor_attainability_audit"
                if passed
                else "gate_b_expert_only_unfreeze_capacity_ceiling"
            ),
            "model_loaded": False,
            "model_inference": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_coverage_audit(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.35a PEFT module coverage audit")
    expected = build_coverage_audit(
        t20_35_result_identity=payload.get("t20_35_result_identity_sha256"),
        t20_35_run_identity=payload.get("t20_35_run_identity_sha256"),
        checkpoint_identity=payload.get("checkpoint_identity_sha256"),
        adapter_config_sha256=payload.get("adapter_config_sha256"),
        adapter_model_sha256=payload.get("adapter_model_sha256"),
        target_modules=payload.get("declared_target_modules"),
        tensor_descriptors=payload.get("tensor_descriptors"),
        expected_trainable_parameter_count=payload.get(
            "expected_trainable_parameter_count"
        ),
    )
    if payload != expected:
        raise ValueError("T20.35a PEFT module coverage audit drifted")


def build_live_coverage_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    t20_33_spec = load_strict_json(root / T20_33_SPEC_PATH)
    spec = load_strict_json(root / T20_35_SPEC_PATH)
    verify_training_spec(spec, t20_33_spec=t20_33_spec)
    run = load_strict_json(root / RUN_SUMMARY_PATH)
    result = load_strict_json(root / T20_35_RESULT_PATH)
    t20_33_result = load_t20_33_result(repo_root=root)
    verify_t20_35_run(
        run,
        spec=spec,
        authority_identity=result["authority_decision_identity_sha256"],
    )
    verify_t20_35_result(
        result,
        spec=spec,
        run=run,
        t20_33_result=t20_33_result,
    )
    adapter_root = root / ADAPTER_ROOT
    tree = _file_tree(adapter_root)
    if tree != run["checkpoint_tree"]:
        raise ValueError("T20.35a adapter checkpoint tree drifted")
    config_path = root / ADAPTER_CONFIG_PATH
    model_path = root / ADAPTER_MODEL_PATH
    config = load_strict_json(config_path)
    if (
        config.get("r") != LORA_RANK
        or config.get("lora_alpha") != LORA_ALPHA
        or config.get("peft_type") != "LORA"
        or config.get("target_modules") != EXPECTED_TARGET_MODULES
    ):
        raise ValueError("T20.35a adapter configuration drifted")
    tensors = _read_safetensor_descriptors(model_path)
    audit = build_coverage_audit(
        t20_35_result_identity=result["identity_sha256"],
        t20_35_run_identity=run["identity_sha256"],
        checkpoint_identity=run["checkpoint_identity_sha256"],
        adapter_config_sha256=_file_sha(config_path),
        adapter_model_sha256=_file_sha(model_path),
        target_modules=config["target_modules"],
        tensor_descriptors=tensors,
        expected_trainable_parameter_count=run["trainable_parameter_count"],
    )
    verify_coverage_audit(audit)
    return audit


def write_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    audit = build_live_coverage_audit(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / AUDIT_PATH, audit)
    return audit


def verify_audit_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = build_live_coverage_audit(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / AUDIT_PATH)
    verify_coverage_audit(archived)
    if archived != expected:
        raise ValueError("T20.35a archived coverage audit drifted from adapter")
    return archived


def _normalize_tensors(
    descriptors: Any,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    if not isinstance(descriptors, list) or not descriptors:
        raise ValueError("T20.35a tensor descriptors are missing")
    normalized = []
    seen = set()
    module_sides: dict[str, dict[str, dict[str, Any]]] = {}
    expected_keys = {
        "key",
        "shape",
        "dtype",
        "element_count",
        "nonzero_count",
        "all_finite",
        "content_sha256",
    }
    for source in sorted(descriptors, key=lambda row: row.get("key", "")):
        if not isinstance(source, dict) or set(source) != expected_keys:
            raise ValueError("T20.35a tensor descriptor schema drifted")
        key = source.get("key")
        match = _KEY_PATTERN.fullmatch(key) if isinstance(key, str) else None
        if match is None or key in seen:
            raise ValueError("T20.35a tensor key is malformed or duplicated")
        seen.add(key)
        module = match.group("module")
        side = match.group("side")
        if module not in REQUIRED_ACTION_STATE_MODULES and _EXPERT_PATTERN.fullmatch(module) is None:
            raise ValueError(f"T20.35a unexpected wrapped module {module}")
        shape = source.get("shape")
        if (
            not isinstance(shape, list)
            or len(shape) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in shape)
        ):
            raise ValueError("T20.35a tensor shape is invalid")
        element_count = source.get("element_count")
        nonzero_count = source.get("nonzero_count")
        if element_count != math.prod(shape):
            raise ValueError("T20.35a tensor element count drifted")
        if (
            isinstance(nonzero_count, bool)
            or not isinstance(nonzero_count, int)
            or not 0 <= nonzero_count <= element_count
            or source.get("all_finite") is not True
        ):
            raise ValueError("T20.35a tensor numeric evidence is invalid")
        if source.get("dtype") != "float32":
            raise ValueError("T20.35a tensor dtype drifted")
        _sha(source.get("content_sha256"), "tensor content identity")
        row = {
            "key": key,
            "module_path": module,
            "lora_side": side,
            "shape": list(shape),
            "dtype": source["dtype"],
            "element_count": element_count,
            "nonzero_count": nonzero_count,
            "all_finite": True,
            "content_sha256": source["content_sha256"],
        }
        normalized.append(row)
        if side in module_sides.setdefault(module, {}):
            raise ValueError(f"T20.35a duplicate LoRA side for {module}")
        module_sides[module][side] = row
    return normalized, module_sides


def _expected_expert_modules() -> set[str]:
    return {
        "model.paligemma_with_expert.gemma_expert.model.layers."
        f"{layer}.self_attn.{projection}"
        for layer in range(EXPECTED_EXPERT_LAYER_COUNT)
        for projection in ("q_proj", "v_proj")
    }


def _read_safetensor_descriptors(path: Path) -> list[dict[str, Any]]:
    import numpy as np
    from safetensors import safe_open

    rows = []
    with safe_open(path, framework="np") as source:
        for key in sorted(source.keys()):
            tensor = np.asarray(source.get_tensor(key))
            rows.append(
                {
                    "key": key,
                    "shape": list(tensor.shape),
                    "dtype": str(tensor.dtype),
                    "element_count": int(tensor.size),
                    "nonzero_count": int(np.count_nonzero(tensor)),
                    "all_finite": bool(np.isfinite(tensor).all()),
                    "content_sha256": hashlib.sha256(
                        tensor.tobytes(order="C")
                    ).hexdigest(),
                }
            )
    return rows


def _file_tree(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": str(path.relative_to(root)),
            "size_bytes": path.stat().st_size,
            "sha256": _file_sha(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35a {label} must be lowercase SHA-256")
    return value

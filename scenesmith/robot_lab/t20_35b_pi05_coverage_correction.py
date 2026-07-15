"""Source-grounded PI0.5 coverage semantic correction for T20.35b."""

from __future__ import annotations

import ast
import hashlib
import re

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_stack import build_stack_identity
from scenesmith.robot_lab.t20_35a_peft_module_coverage import (
    AUDIT_PATH as T20_35A_AUDIT_PATH,
    verify_coverage_audit,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PI05_SOURCE_PATH = Path("external/lerobot/src/lerobot/policies/pi05/modeling_pi05.py")
CORRECTION_PATH = Path(
    "configurations/robot_lab/t20_35b_pi05_coverage_correction.json"
)
SCHEMA_VERSION = "scenesmith.t20_35b_pi05_coverage_correction.v1"
EXPECTED_PI05_SOURCE_SHA256 = (
    "b05b6afe70a4a09f2eb610827b9ae09e8b08e43cd748d435e47879344e3fa619"
)
EXPECTED_T20_35A_AUDIT_IDENTITY = (
    "d1109ae8ea393b4577444d54f1675a78993e5c09de3c9ee87a0f78cf9b1b48a1"
)
ACTUAL_PI05_MODULES = (
    "model.action_in_proj",
    "model.action_out_proj",
    "model.time_mlp_in",
    "model.time_mlp_out",
)
DECLARED_DEFAULT_PEFT_MODULES = (
    "model.state_proj",
    "model.action_in_proj",
    "model.action_out_proj",
    "model.action_time_mlp_in",
    "model.action_time_mlp_out",
)
_EXPERT_PATTERN = re.compile(
    r"^model\.paligemma_with_expert\.gemma_expert\.model\.layers\."
    r"\d+\.self_attn\.(q_proj|v_proj)$"
)


def build_correction(
    *,
    t20_35a_audit_identity: str,
    lerobot_stack_identity: str,
    lerobot_revision: str,
    patch_set_sha256: str,
    pi05_source_sha256: str,
    actual_pi05_modules: list[str],
    declared_default_peft_modules: list[str],
    saved_lora_module_paths: list[str],
) -> dict[str, Any]:
    for value, label in (
        (t20_35a_audit_identity, "T20.35a audit identity"),
        (lerobot_stack_identity, "LeRobot stack identity"),
        (patch_set_sha256, "patch-set identity"),
        (pi05_source_sha256, "PI0.5 source identity"),
    ):
        _sha(value, label)
    _sha40(lerobot_revision, "LeRobot revision")
    if actual_pi05_modules != list(ACTUAL_PI05_MODULES):
        raise ValueError("T20.35b actual PI0.5 module set drifted")
    if declared_default_peft_modules != list(DECLARED_DEFAULT_PEFT_MODULES):
        raise ValueError("T20.35b declared default PEFT module set drifted")
    if (
        not isinstance(saved_lora_module_paths, list)
        or len(saved_lora_module_paths) != len(set(saved_lora_module_paths))
        or any(not isinstance(module, str) for module in saved_lora_module_paths)
    ):
        raise ValueError("T20.35b saved LoRA module paths are invalid")
    allowed_saved = set(ACTUAL_PI05_MODULES) | {
        "model.action_time_mlp_in",
        "model.action_time_mlp_out",
        "model.state_proj",
    }
    if any(
        module not in allowed_saved and _EXPERT_PATTERN.fullmatch(module) is None
        for module in saved_lora_module_paths
    ):
        raise ValueError("T20.35b saved LoRA module path is unexpected")

    actual = set(actual_pi05_modules)
    declared = set(declared_default_peft_modules)
    saved = set(saved_lora_module_paths)
    missing = sorted(actual - saved)
    stale = sorted(declared - actual)
    actual_missing_from_default = sorted(actual - declared)
    passed = not missing
    coverage = [
        {"module_path": module, "wrapped_as_lora_pair": module in saved}
        for module in ACTUAL_PI05_MODULES
    ]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35b",
            "scope": "optimizer_free_pi05_source_grounded_peft_coverage_correction",
            "supersedes_t20_35a_audit_identity_sha256": t20_35a_audit_identity,
            "lerobot_stack_identity_sha256": lerobot_stack_identity,
            "lerobot_revision": lerobot_revision,
            "patch_set_sha256": patch_set_sha256,
            "pi05_model_source_path": str(PI05_SOURCE_PATH),
            "pi05_model_source_sha256": pi05_source_sha256,
            "actual_pi05_action_time_modules": list(ACTUAL_PI05_MODULES),
            "declared_default_peft_modules": list(DECLARED_DEFAULT_PEFT_MODULES),
            "saved_lora_module_paths": sorted(saved_lora_module_paths),
            "corrected_real_module_coverage": coverage,
            "missing_real_pi05_action_time_modules": missing,
            "stale_or_nonexistent_declared_peft_modules": stale,
            "real_modules_missing_from_default_peft_names": actual_missing_from_default,
            "state_proj_intentionally_absent": "model.state_proj" not in actual,
            "action_time_to_time_mlp_name_mismatch": {
                "model.action_time_mlp_in": "model.time_mlp_in",
                "model.action_time_mlp_out": "model.time_mlp_out",
            },
            "all_real_pi05_action_time_pathways_wrapped": passed,
            "t20_35a_generic_five_pathway_semantics_superseded": True,
            "decision": (
                "pi05_peft_coverage_pass" if passed else "pi05_peft_coverage_fail"
            ),
            "selected_next_hypothesis": (
                "gate_b_objective_floor_attainability_audit"
                if passed
                else "gate_b_expert_only_unfreeze_capacity_ceiling"
            ),
            "upstream_source_mutated": False,
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


def verify_correction(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.35b PI0.5 coverage correction")
    expected = build_correction(
        t20_35a_audit_identity=payload.get(
            "supersedes_t20_35a_audit_identity_sha256"
        ),
        lerobot_stack_identity=payload.get("lerobot_stack_identity_sha256"),
        lerobot_revision=payload.get("lerobot_revision"),
        patch_set_sha256=payload.get("patch_set_sha256"),
        pi05_source_sha256=payload.get("pi05_model_source_sha256"),
        actual_pi05_modules=payload.get("actual_pi05_action_time_modules"),
        declared_default_peft_modules=payload.get("declared_default_peft_modules"),
        saved_lora_module_paths=payload.get("saved_lora_module_paths"),
    )
    if payload != expected:
        raise ValueError("T20.35b PI0.5 coverage correction drifted")


def build_live_correction(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    stack = build_stack_identity(repo_root=root)
    source_path = root / PI05_SOURCE_PATH
    source_bytes = source_path.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    if source_sha != EXPECTED_PI05_SOURCE_SHA256:
        raise ValueError("T20.35b pinned PI0.5 source identity drifted")
    actual_modules, declared_modules, state_proj_declared = _parse_pi05_source(
        source_bytes.decode("utf-8")
    )
    if state_proj_declared:
        raise ValueError("T20.35b PI0.5 unexpectedly declares state_proj")
    prior = load_strict_json(root / T20_35A_AUDIT_PATH)
    verify_coverage_audit(prior)
    if prior["identity_sha256"] != EXPECTED_T20_35A_AUDIT_IDENTITY:
        raise ValueError("T20.35b source T20.35a audit drifted")
    saved_modules = [row["module_path"] for row in prior["wrapped_modules"]]
    correction = build_correction(
        t20_35a_audit_identity=prior["identity_sha256"],
        lerobot_stack_identity=stack["identity_sha256"],
        lerobot_revision=stack["base_revision"],
        patch_set_sha256=stack["patch_set_sha256"],
        pi05_source_sha256=source_sha,
        actual_pi05_modules=actual_modules,
        declared_default_peft_modules=declared_modules,
        saved_lora_module_paths=saved_modules,
    )
    verify_correction(correction)
    return correction


def write_correction(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    correction = build_live_correction(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / CORRECTION_PATH, correction)
    return correction


def verify_correction_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = build_live_correction(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / CORRECTION_PATH)
    verify_correction(archived)
    if archived != expected:
        raise ValueError("T20.35b archived correction drifted from pinned source")
    return archived


def _parse_pi05_source(source: str) -> tuple[list[str], list[str], bool]:
    tree = ast.parse(source)
    pi05_pytorch = _class(tree, "PI05Pytorch")
    init = _method(pi05_pytorch, "__init__")
    linear_names = []
    state_proj_declared = False
    for node in ast.walk(init):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                state_proj_declared |= target.attr == "state_proj"
                value = node.value
                if (
                    isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute)
                    and isinstance(value.func.value, ast.Name)
                    and value.func.value.id == "nn"
                    and value.func.attr == "Linear"
                    and target.attr
                    in {"action_in_proj", "action_out_proj", "time_mlp_in", "time_mlp_out"}
                ):
                    linear_names.append(f"model.{target.attr}")
    policy = _class(tree, "PI05Policy")
    peft_method = _method(policy, "_get_default_peft_targets")
    declared = None
    for node in ast.walk(peft_method):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "common_projections" for target in node.targets)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            declared = [f"model.{name}" for name in node.value.value.split("|")]
    if declared is None:
        raise ValueError("T20.35b could not derive default PEFT module names")
    return linear_names, declared, state_proj_declared


def _class(tree: ast.AST, name: str) -> ast.ClassDef:
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"T20.35b expected one {name} class")
    return matches[0]


def _method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    matches = [item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == name]
    if len(matches) != 1:
        raise ValueError(f"T20.35b expected one {node.name}.{name} method")
    return matches[0]


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35b {label} must be lowercase SHA-256")
    return value


def _sha40(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35b {label} must be lowercase 40-hex")
    return value

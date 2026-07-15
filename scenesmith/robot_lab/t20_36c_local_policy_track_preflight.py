"""Read-only local ACT and SmolVLA policy-track preflight for T20.36c."""

from __future__ import annotations

import hashlib
import subprocess

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_36c_local_policy_track_preflight.json"
)
SCHEMA_VERSION = "scenesmith.t20_36c_local_policy_track_preflight.v1"
TASK_ID = "T20.36c"
LEROBOT_HEAD = "e40b58a8dfa9e7b86918c374791599d070518d11"
LEROBOT_DIRTY_PATHS = (
    " M src/lerobot/policies/pi05/modeling_pi05.py",
    " M src/lerobot/scripts/lerobot_train.py",
)
SOURCE_SHA256 = {
    "src/lerobot/configs/policies.py": (
        "94bfe65715b2d35ac0ddfd79e52b8f9c1cf8a28fc1d62d56cd6fb2c3908a8876"
    ),
    "src/lerobot/policies/act/configuration_act.py": (
        "35a60c0dd3c811b137b5eb035bdbd40d40e2c24ba0cda61756052e6e1c829282"
    ),
    "src/lerobot/policies/act/modeling_act.py": (
        "a6c1a49c5daafa513b9abee9b986205d327e25c70ed13623ab2e6c0ab6b1f577"
    ),
    "src/lerobot/policies/act/processor_act.py": (
        "2bff84913c264eba5c2e65239d685ca1b497c1d9d2259958da293ec604b5830a"
    ),
    "src/lerobot/policies/factory.py": (
        "7d8a74352cb8691bd59de44a478b6f3a2bbe212583fdb04a5c19b669311b4ebe"
    ),
    "src/lerobot/policies/smolvla/configuration_smolvla.py": (
        "2fb637cb428fa2fdf1d114646dcffaf4728216bfe5b7039d5d0cac4857ffc4e0"
    ),
    "src/lerobot/policies/smolvla/modeling_smolvla.py": (
        "5daaa297954acf9ae89397b571322f07bf30798e72f566e61a09393342cb1f99"
    ),
    "src/lerobot/policies/smolvla/processor_smolvla.py": (
        "d34594291b2ecf7801f8c27a940a998c52a7e308cbc89f2403c9cbecfb368f22"
    ),
    "src/lerobot/policies/smolvla/smolvlm_with_expert.py": (
        "f7542fa2bf904f9ef64d26843809f913a5e93c4dfa538dda06db0b288391ab4d"
    ),
}
DATASET_FILES = {
    "manifest": Path(
        "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
    ),
    "info": Path(
        "outputs/robot_lab/t20_23_recovery_augmented_dataset/meta/info.json"
    ),
    "stats": Path(
        "outputs/robot_lab/t20_23_recovery_augmented_dataset/meta/stats.json"
    ),
    "tasks": Path(
        "outputs/robot_lab/t20_23_recovery_augmented_dataset/meta/tasks.parquet"
    ),
}
DATASET_SHA256 = {
    "manifest": "df6e63d86cd053937c9e4d4c267f057b76aaf418761e7dc3356a9ae08c06fea5",
    "info": "789ab860cae39d100f1d28e0e547e2229b860cdcacc2916c230074ff5e7ed9fc",
    "stats": "aae49a26834aa3684d17bede1da1407f2664c61d0bb9f33a650b269af6123bc1",
    "tasks": "75d507d99b8f12e63006844a0034e3ce8570ca47b22d7417f2096c29dbfa3f4f",
}
DATASET_MANIFEST_IDENTITY = (
    "f12c95a3cdf3e0005fa093000a5e44e1cddd08dbfb049ab405f462e2c9e760fa"
)
ACT_EVIDENCE_FILES = {
    "overfit": Path("outputs/robot_lab/t20_2_act_overfit_run_003/run_summary.json"),
    "closed_loop": Path("outputs/robot_lab/t20_2_act_closed_loop_run_002.json"),
}
ACT_EVIDENCE_SHA256 = {
    "overfit": "0bde6870afda7adc62c44c2bf8b67e3b97b51c677af659b00bd4795c00ee8ca6",
    "closed_loop": "f58fe5adc50823fd861bd494e8f5104740ec6577047a2d2946a7ec4919360d1d",
}
CACHE_REVISIONS = {
    "act_candidate": (
        "models--binhpham--sim_so101_cubes_act_small",
        "9332873218eaba2c64ac1115c4b9742177f64c13",
    ),
    "smolvla_base": (
        "models--lerobot--smolvla_base",
        "c83c3163b8ca9b7e67c509fffd9121e66cb96205",
    ),
    "smolvlm_base": (
        "models--HuggingFaceTB--SmolVLM2-500M-Video-Instruct",
        "7b375e1b73b11138ff12fe22c8f2822d8fe03467",
    ),
}
CACHE_REQUIRED_FILES = {
    "act_candidate": {"config.json", "model.safetensors"},
    "smolvla_base": {
        "config.json",
        "model.safetensors",
        "policy_postprocessor.json",
        "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
        "policy_preprocessor.json",
        "policy_preprocessor_step_5_normalizer_processor.safetensors",
    },
    "smolvlm_base": {
        "added_tokens.json",
        "chat_template.json",
        "config.json",
        "generation_config.json",
        "merges.txt",
        "model.safetensors",
        "preprocessor_config.json",
        "processor_config.json",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
    },
}
CACHE_PINNED_METADATA_SHA256 = {
    "act_candidate": {
        "config.json": (
            "7bfd75f3f29092b25a7687622695c806913f879371b3fa075df0a3867bb2a565"
        ),
    },
    "smolvla_base": {
        "config.json": (
            "650584b56c104720f7a3c91d1ec6bec9e8de8ac11e60c92ba2fa82d93eda147d"
        ),
        "policy_preprocessor.json": (
            "7683d648280a72f0d51e869fb8dd1596beed90b7f84849330cf1bc26634a4bd6"
        ),
        "policy_postprocessor.json": (
            "2b78bb742065288df2ec63b0ee35f97a1f6950171cf2272f7e34b1fe3873b17b"
        ),
    },
    "smolvlm_base": {
        "config.json": (
            "ea6bc1237e96247f6258de3e202e2e62b93d6f386dc47e7b36b5588bf3a15e17"
        ),
        "processor_config.json": (
            "f3ad45028447b3562b4752be0d5916d6806c1ef589091a469608dcf0faa1737c"
        ),
        "tokenizer_config.json": (
            "dd9ce2ab89a3dd881bd9378f1a79b943a064b9275a7e1706d5b7b47b68977913"
        ),
    },
}
CACHE_PINNED_WEIGHT_SIZE = {
    "act_candidate": {"model.safetensors": 62_292_104},
    "smolvla_base": {
        "model.safetensors": 906_712_520,
        "policy_postprocessor_step_0_unnormalizer_processor.safetensors": 640,
        "policy_preprocessor_step_5_normalizer_processor.safetensors": 640,
    },
    "smolvlm_base": {"model.safetensors": 2_029_990_624},
}
AUTHORITY_FIELDS = (
    "network_accessed",
    "weights_downloaded",
    "checkpoint_tensor_read",
    "model_loaded",
    "model_inference",
    "optimizer_created",
    "optimizer_training",
    "policy_track_selected",
    "gate_b_threshold_changed",
    "gate_c_authorized",
    "closed_loop_rollout",
    "simulation_policy_accepted",
    "physical_actuation",
    "external_compute_started",
    "brev_compute_started",
    "physical_transfer_ready",
    "promotion_eligible",
)
_TENSOR_SUFFIXES = {".bin", ".pt", ".pth", ".safetensors"}


def load_local_snapshot(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Load source and metadata only; checkpoint and model tensors stay unopened."""

    lerobot_root = repo_root / "external/lerobot"
    source_files = [
        {
            "path": path,
            "sha256": _file_sha256(lerobot_root / path),
        }
        for path in sorted(SOURCE_SHA256)
    ]
    cache_root = Path.home() / ".cache/huggingface/hub"
    cache_inventory = {
        label: _inventory_cache(
            label=label,
            directory=cache_root / model / "snapshots" / revision,
            home=Path.home(),
        )
        for label, (model, revision) in CACHE_REVISIONS.items()
    }
    dataset_manifest = load_strict_json(repo_root / DATASET_FILES["manifest"])
    dataset_info = load_strict_json(repo_root / DATASET_FILES["info"])
    overfit = load_strict_json(repo_root / ACT_EVIDENCE_FILES["overfit"])
    closed_loop = load_strict_json(repo_root / ACT_EVIDENCE_FILES["closed_loop"])
    return {
        "lerobot_head": _git_output(lerobot_root, "rev-parse", "HEAD"),
        "lerobot_dirty_paths": _git_lines(
            lerobot_root,
            "status",
            "--short",
            "--untracked-files=no",
        ),
        "source_files": source_files,
        "dataset_manifest": dataset_manifest,
        "dataset_info": dataset_info,
        "dataset_file_sha256": {
            label: _file_sha256(repo_root / path)
            for label, path in DATASET_FILES.items()
        },
        "dataset_tasks": _dataset_tasks(repo_root / DATASET_FILES["tasks"]),
        "act_overfit_evidence": {
            "schema_version": overfit.get("schema_version"),
            "task_id": overfit.get("task_id"),
            "updates": overfit.get("updates"),
            "runtime": overfit.get("runtime"),
            "model": overfit.get("model"),
            "loss": {
                "baseline_train_l1": overfit.get("loss", {}).get(
                    "baseline_train_l1"
                ),
                "final_train_l1": overfit.get("loss", {}).get("final_train_l1"),
                "held_out_l1": overfit.get("loss", {}).get("held_out_l1"),
            },
            "physical_actuation": overfit.get("physical_actuation"),
            "external_compute_started": overfit.get("external_compute_started"),
            "brev_compute_started": overfit.get("brev_compute_started"),
        },
        "act_closed_loop_evidence": {
            "schema_version": closed_loop.get("schema_version"),
            "task_id": closed_loop.get("task_id"),
            "maximum_anchor_lift_m": closed_loop.get("maximum_anchor_lift_m"),
            "simulation_semantic_strict_success": closed_loop.get(
                "simulation_semantic_strict_success"
            ),
            "simulation_policy_accepted": closed_loop.get(
                "simulation_policy_accepted"
            ),
            "physical_actuation": closed_loop.get("physical_actuation"),
            "external_compute_started": closed_loop.get(
                "external_compute_started"
            ),
            "brev_compute_started": closed_loop.get("brev_compute_started"),
        },
        "act_evidence_file_sha256": {
            label: _file_sha256(repo_root / path)
            for label, path in ACT_EVIDENCE_FILES.items()
        },
        "cache_inventory": cache_inventory,
        "act_candidate_config": _cache_json(
            cache_inventory["act_candidate"], "config.json", cache_root
        ),
        "smolvla_base_config": _cache_json(
            cache_inventory["smolvla_base"], "config.json", cache_root
        ),
    }


def build_audit(*, snapshot: dict[str, Any]) -> dict[str, Any]:
    _validate_source_snapshot(snapshot)
    _validate_dataset_snapshot(snapshot)
    dataset = _dataset_summary(snapshot)
    act_cache_complete = _cache_complete(snapshot, "act_candidate")
    smolvla_cache_complete = _cache_complete(snapshot, "smolvla_base")
    smolvlm_cache_complete = _cache_complete(snapshot, "smolvlm_base")
    act_config = _dict(snapshot.get("act_candidate_config"), "ACT config")
    smolvla_config = _dict(snapshot.get("smolvla_base_config"), "SmolVLA config")
    act_input = _dict(act_config.get("input_features"), "ACT input features")
    act_output = _dict(act_config.get("output_features"), "ACT output features")
    smol_input = _dict(
        smolvla_config.get("input_features"), "SmolVLA input features"
    )
    smol_output = _dict(
        smolvla_config.get("output_features"), "SmolVLA output features"
    )
    dataset_image_keys = dataset["image_feature_keys"]
    act_image_keys = _visual_feature_keys(act_input)
    smol_image_keys = _visual_feature_keys(smol_input)
    act_source_complete = _source_group_complete(snapshot, "/act/")
    smol_source_complete = _source_group_complete(snapshot, "/smolvla/")
    act_dataset_shape = (
        dataset["state_dimension"] == 6
        and dataset["action_dimension"] == 6
        and dataset["image_feature_count"] == 2
        and dataset["image_shape"] == [3, 256, 256]
    )
    act_drop_in = (
        act_cache_complete
        and _feature_dimension(act_input, "observation.state")
        == dataset["state_dimension"]
        and _feature_dimension(act_output, "action")
        == dataset["action_dimension"]
        and act_image_keys == dataset_image_keys
        and act_config.get("chunk_size") == 50
        and act_config.get("n_action_steps") == 50
    )
    smol_horizon_match = (
        _feature_dimension(smol_input, "observation.state")
        == dataset["state_dimension"]
        == 6
        and _feature_dimension(smol_output, "action")
        == dataset["action_dimension"]
        == 6
        and smolvla_config.get("chunk_size") == 50
        and smolvla_config.get("n_action_steps") == 50
    )
    smol_camera_match = smol_image_keys == dataset_image_keys
    mps_previously_observed = _act_mps_observed(snapshot)
    act_design_ready = (
        act_source_complete
        and act_cache_complete
        and act_dataset_shape
        and mps_previously_observed
        and dataset["language_task_available"]
    )
    smol_design_ready = (
        smol_source_complete
        and smolvla_cache_complete
        and smolvlm_cache_complete
        and smol_horizon_match
        and dataset["language_task_available"]
    )
    if act_design_ready:
        hypothesis = "design_exact_act_gate_b_control_before_smolvla_entry"
    else:
        hypothesis = "stop_missing_local_act_control_design_prerequisites"
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "scope": "read_only_local_act_and_smolvla_source_cache_dataset_preflight",
        "classification": "local_metadata_supports_act_first_control_design_only",
        "lerobot_source": {
            "head": snapshot["lerobot_head"],
            "dirty_paths_preserved": snapshot["lerobot_dirty_paths"],
            "source_files": snapshot["source_files"],
            "source_bound": True,
        },
        "dataset": dataset,
        "cache_inventory": snapshot["cache_inventory"],
        "act": {
            "source_entrypoints_complete": act_source_complete,
            "mps_runtime_previously_observed": mps_previously_observed,
            "previous_mps_evidence_file_sha256": snapshot[
                "act_evidence_file_sha256"
            ]["overfit"],
            "previous_closed_loop_evidence_file_sha256": snapshot[
                "act_evidence_file_sha256"
            ]["closed_loop"],
            "previous_mps_updates": snapshot["act_overfit_evidence"]["updates"],
            "previous_mps_chunk_size": snapshot["act_overfit_evidence"]["model"][
                "chunk_size"
            ],
            "previous_closed_loop_strict_success": snapshot[
                "act_closed_loop_evidence"
            ]["simulation_semantic_strict_success"],
            "local_checkpoint_metadata_complete": act_cache_complete,
            "cached_checkpoint_integrity_verified": False,
            "cached_checkpoint_drop_in_compatible": act_drop_in,
            "cached_checkpoint_image_feature_keys": act_image_keys,
            "canonical_dataset_shape_compatible": act_dataset_shape,
            "exact_gate_b_control_already_run": False,
            "diagnostic_control_design_ready": act_design_ready,
        },
        "smolvla": {
            "source_entrypoints_complete": smol_source_complete,
            "base_cache_metadata_complete": smolvla_cache_complete,
            "vlm_cache_metadata_complete": smolvlm_cache_complete,
            "cached_checkpoint_integrity_verified": False,
            "action_state_horizon_match": smol_horizon_match,
            "camera_feature_match": smol_camera_match,
            "cached_image_feature_keys": smol_image_keys,
            "two_camera_override_required": not smol_camera_match,
            "mps_source_not_explicitly_blocked": smol_source_complete,
            "mps_runtime_verified": False,
            "drop_in_ready": False,
            "local_entry_design_ready": smol_design_ready,
        },
        "selected_next_hypothesis": hypothesis,
        "next_hypothesis_is_design_only": True,
        "no_policy_performance_inference_from_cache_presence": True,
        "no_checkpoint_integrity_inference_from_stat_only_inventory": True,
        "exact_act_control_requires_separate_authority_and_spec": True,
        "smolvla_entry_requires_two_camera_override_test_and_mps_runtime_proof": True,
    }
    payload.update({field: False for field in AUTHORITY_FIELDS})
    return sign_payload(payload)


def verify_audit(payload: dict[str, Any], *, snapshot: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36c local policy-track preflight")
    expected = build_audit(snapshot=snapshot)
    if payload != expected:
        raise ValueError("T20.36c local policy-track preflight drifted")


def write_audit(
    *, repo_root: Path = REPO_ROOT, output_path: Path = AUDIT_PATH
) -> dict[str, Any]:
    snapshot = load_local_snapshot(repo_root=repo_root)
    audit = build_audit(snapshot=snapshot)
    destination = output_path if output_path.is_absolute() else repo_root / output_path
    dump_canonical_json(destination, audit)
    verify_audit_file(
        repo_root=repo_root,
        output_path=output_path,
        snapshot=snapshot,
    )
    return audit


def verify_audit_file(
    *,
    repo_root: Path = REPO_ROOT,
    output_path: Path = AUDIT_PATH,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    destination = output_path if output_path.is_absolute() else repo_root / output_path
    payload = load_strict_json(destination)
    verify_audit(
        payload,
        snapshot=snapshot or load_local_snapshot(repo_root=repo_root),
    )
    return payload


def _validate_source_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("lerobot_head") != LEROBOT_HEAD:
        raise ValueError("T20.36c LeRobot HEAD drifted")
    if tuple(snapshot.get("lerobot_dirty_paths", ())) != LEROBOT_DIRTY_PATHS:
        raise ValueError("T20.36c LeRobot dirty-path evidence drifted")
    rows = snapshot.get("source_files")
    if not isinstance(rows, list):
        raise ValueError("T20.36c source-file evidence is missing")
    observed = {
        row.get("path"): row.get("sha256")
        for row in rows
        if isinstance(row, dict)
    }
    if observed != SOURCE_SHA256 or len(rows) != len(SOURCE_SHA256):
        raise ValueError("T20.36c LeRobot source hashes drifted")


def _validate_dataset_snapshot(snapshot: dict[str, Any]) -> None:
    manifest = _dict(snapshot.get("dataset_manifest"), "dataset manifest")
    verify_signed_payload(manifest, label="T20.36c source dataset manifest")
    if manifest.get("identity_sha256") != DATASET_MANIFEST_IDENTITY:
        raise ValueError("T20.36c source dataset manifest identity drifted")
    if snapshot.get("dataset_file_sha256") != DATASET_SHA256:
        raise ValueError("T20.36c dataset metadata files drifted")


def _dataset_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    info = _dict(snapshot.get("dataset_info"), "dataset info")
    features = _dict(info.get("features"), "dataset features")
    state_dimension = _feature_dimension(features, "observation.state")
    action_dimension = _feature_dimension(features, "action")
    image_keys = sorted(
        key
        for key, value in features.items()
        if isinstance(value, dict) and value.get("dtype") == "image"
    )
    image_shapes = [_shape(features[key], f"dataset image {key}") for key in image_keys]
    common_image_shape = image_shapes[0] if image_shapes and len(set(map(tuple, image_shapes))) == 1 else None
    tasks = snapshot.get("dataset_tasks")
    if not isinstance(tasks, list) or any(
        not isinstance(task, str) or not task.strip() for task in tasks
    ):
        raise ValueError("T20.36c dataset language-task metadata is invalid")
    return {
        "manifest_identity_sha256": DATASET_MANIFEST_IDENTITY,
        "metadata_file_sha256": snapshot["dataset_file_sha256"],
        "episode_count": info.get("total_episodes"),
        "total_frames": info.get("total_frames"),
        "fps": info.get("fps"),
        "state_dimension": state_dimension,
        "action_dimension": action_dimension,
        "image_feature_count": len(image_keys),
        "image_feature_keys": image_keys,
        "image_shape": common_image_shape,
        "language_tasks": tasks,
        "language_task_available": bool(tasks),
        "dataset_examples_read": False,
    }


def _cache_complete(snapshot: dict[str, Any], label: str) -> bool:
    inventory = _dict(snapshot.get("cache_inventory"), "cache inventory")
    cache = inventory.get(label)
    model, revision = CACHE_REVISIONS[label]
    expected_path = f"~/.cache/huggingface/hub/{model}/snapshots/{revision}"
    if (
        not isinstance(cache, dict)
        or cache.get("revision") != revision
        or cache.get("model_cache") != model
        or cache.get("path") != expected_path
        or cache.get("tensor_content_read") is not False
    ):
        return False
    rows = cache.get("files")
    if not isinstance(rows, list):
        return False
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            return False
        name = row.get("name")
        size = row.get("size_bytes")
        is_tensor = row.get("is_weight_or_tensor_file")
        content_read = row.get("content_read")
        if (
            not isinstance(name, str)
            or not name
            or name in indexed
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size <= 0
            or not isinstance(is_tensor, bool)
            or not isinstance(content_read, bool)
            or (is_tensor and (content_read or "sha256" in row))
            or (not is_tensor and not content_read)
        ):
            return False
        indexed[name] = row
    if not CACHE_REQUIRED_FILES[label].issubset(indexed):
        return False
    for name, expected_hash in CACHE_PINNED_METADATA_SHA256[label].items():
        row = indexed[name]
        if row.get("sha256") != expected_hash or not row.get("content_read"):
            return False
    for name, expected_size in CACHE_PINNED_WEIGHT_SIZE[label].items():
        row = indexed[name]
        if (
            row.get("size_bytes") != expected_size
            or not row.get("is_weight_or_tensor_file")
            or row.get("content_read") is not False
            or "sha256" in row
        ):
            return False
    return True


def _source_group_complete(snapshot: dict[str, Any], marker: str) -> bool:
    rows = snapshot.get("source_files")
    return isinstance(rows, list) and sum(
        marker in row.get("path", "") for row in rows if isinstance(row, dict)
    ) >= 3


def _act_mps_observed(snapshot: dict[str, Any]) -> bool:
    evidence = _dict(snapshot.get("act_overfit_evidence"), "ACT overfit evidence")
    runtime = _dict(evidence.get("runtime"), "ACT runtime evidence")
    model = _dict(evidence.get("model"), "ACT model evidence")
    hashes = snapshot.get("act_evidence_file_sha256")
    return (
        hashes == ACT_EVIDENCE_SHA256
        and evidence.get("schema_version") == "scenesmith.t20_2_act_overfit.v1"
        and evidence.get("task_id") == "T20.2"
        and evidence.get("updates") == 100
        and runtime.get("device") == "mps"
        and runtime.get("mps_available") is True
        and model.get("kind") == "lerobot_act"
        and model.get("chunk_size") == 8
        and evidence.get("physical_actuation") is False
        and evidence.get("external_compute_started") is False
        and evidence.get("brev_compute_started") is False
    )


def _inventory_cache(*, label: str, directory: Path, home: Path) -> dict[str, Any]:
    revision = CACHE_REVISIONS[label][1]
    rows: list[dict[str, Any]] = []
    if directory.is_dir():
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if not path.is_file():
                continue
            is_tensor = path.suffix.lower() in _TENSOR_SUFFIXES
            row: dict[str, Any] = {
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "is_weight_or_tensor_file": is_tensor,
                "content_read": not is_tensor,
            }
            if not is_tensor:
                row["sha256"] = _file_sha256(path)
            rows.append(row)
    try:
        display_path = "~/" + str(directory.relative_to(home))
    except ValueError:
        display_path = str(directory)
    return {
        "model_cache": CACHE_REVISIONS[label][0],
        "revision": revision,
        "path": display_path,
        "files": rows,
        "tensor_content_read": False,
    }


def _cache_json(
    inventory: dict[str, Any], filename: str, cache_root: Path
) -> dict[str, Any]:
    path_text = inventory.get("path")
    if not isinstance(path_text, str):
        raise ValueError("T20.36c cache path is invalid")
    if path_text.startswith("~/"):
        directory = Path.home() / path_text[2:]
    else:
        directory = Path(path_text)
    path = directory / filename
    if cache_root not in path.parents:
        raise ValueError("T20.36c cache metadata escaped the cache root")
    return load_strict_json(path)


def _dataset_tasks(path: Path) -> list[str]:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover - runtime dependency preflight
        raise RuntimeError("T20.36c requires local pyarrow for dataset metadata") from exc
    table = parquet.read_table(path, columns=["task"])
    return sorted(set(table.column("task").to_pylist()))


def _visual_feature_keys(features: dict[str, Any]) -> list[str]:
    return sorted(
        key
        for key, value in features.items()
        if isinstance(value, dict) and value.get("type") == "VISUAL"
    )


def _feature_dimension(features: dict[str, Any], key: str) -> int | None:
    value = features.get(key)
    if not isinstance(value, dict):
        return None
    shape = value.get("shape")
    if (
        not isinstance(shape, list)
        or len(shape) != 1
        or isinstance(shape[0], bool)
        or not isinstance(shape[0], int)
    ):
        return None
    return shape[0]


def _shape(value: dict[str, Any], label: str) -> list[int]:
    shape = value.get("shape")
    if not isinstance(shape, list) or any(
        isinstance(item, bool) or not isinstance(item, int) or item <= 0
        for item in shape
    ):
        raise ValueError(f"T20.36c {label} shape is invalid")
    return list(shape)


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"T20.36c {label} is invalid")
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_output(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_lines(repo: Path, *arguments: str) -> list[str]:
    output = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")
    return output.splitlines() if output else []

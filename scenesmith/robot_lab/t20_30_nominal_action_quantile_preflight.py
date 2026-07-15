"""T20.30 recovery dataset view with clean nominal action quantiles."""

from __future__ import annotations

import copy
import hashlib
import math
import shutil

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_17_clean_base_preflight import EXPECTED_MODEL_REVISION
from scenesmith.robot_lab.t20_23_recovery_augmented_preflight import (
    DATASET_ROOT as SOURCE_DATASET_ROOT,
    REPO_ROOT,
    TRAINING_SPEC_PATH as SOURCE_SPEC_PATH,
    verify_training_spec_file as verify_source_spec,
)


DATASET_ROOT = Path("outputs/robot_lab/t20_30_nominal_action_quantile_dataset")
MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_30_nominal_action_quantile_dataset_manifest.json"
)
TRAINING_SPEC_PATH = Path(
    "configurations/robot_lab/t20_30_nominal_action_quantile_training_spec.json"
)
CLEAN_STATS_PATH = Path(
    "outputs/robot_lab/t20_17_lerobot_training_dataset/meta/stats.json"
)
RECOVERY_STATS_PATH = SOURCE_DATASET_ROOT / "meta/stats.json"
T20_29_PATH = Path(
    "configurations/robot_lab/t20_29_quantile_postprocessor_counterfactual.json"
)
DATASET_REPO_ID = "scenesmith/t20-30-recovery-clean-action-quantiles"
SCHEMA_VERSION = "scenesmith.t20_30_nominal_action_quantile_training_spec.v1"
MANIFEST_SCHEMA_VERSION = "scenesmith.t20_30_nominal_action_quantile_dataset.v1"
EXPECTED_EPISODES = 10
EXPECTED_FRAMES = 2330
EXPECTED_UPDATES = 500
TRAINING_SEED = 20260714
FALSE_FIELDS = (
    "model_loaded",
    "model_inference",
    "optimizer_training",
    "simulation_rollout_executed",
    "simulation_policy_accepted",
    "physical_actuation",
    "external_compute_started",
    "brev_compute_started",
)


def build_ablation_stats(
    clean_stats: dict[str, Any], recovery_stats: dict[str, Any]
) -> dict[str, Any]:
    _validate_stats(clean_stats, "clean")
    _validate_stats(recovery_stats, "recovery")
    result = copy.deepcopy(recovery_stats)
    result["action"]["q01"] = copy.deepcopy(clean_stats["action"]["q01"])
    result["action"]["q99"] = copy.deepcopy(clean_stats["action"]["q99"])
    _verify_stats_delta(result, clean_stats, recovery_stats)
    return result


def build_manifest(
    *,
    source_root: Path,
    derived_root: Path,
    clean_stats: dict[str, Any],
    recovery_stats: dict[str, Any],
    episode_count: int,
    frame_count: int,
) -> dict[str, Any]:
    expected_stats = build_ablation_stats(clean_stats, recovery_stats)
    source_files = _file_map(source_root)
    derived_files = _file_map(derived_root)
    if set(source_files) != set(derived_files):
        raise ValueError("T20.30 derived dataset file coverage drifted")
    stats_name = "meta/stats.json"
    if stats_name not in source_files:
        raise ValueError("T20.30 source dataset statistics are missing")
    for relative in source_files:
        source_path = source_root / relative
        derived_path = derived_root / relative
        if source_path.samefile(derived_path):
            raise ValueError("T20.30 derived dataset contains a source inode alias")
        if relative != stats_name and source_files[relative] != derived_files[relative]:
            raise ValueError("T20.30 non-statistics dataset byte drifted")
    recorded = load_strict_json(derived_root / stats_name)
    if recorded != expected_stats:
        raise ValueError("T20.30 derived action statistics drifted")
    if episode_count != EXPECTED_EPISODES or frame_count != EXPECTED_FRAMES:
        raise ValueError("T20.30 package dataset cardinality drifted")
    return sign_payload(
        {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "source_dataset_root": SOURCE_DATASET_ROOT.as_posix(),
            "derived_dataset_root": DATASET_ROOT.as_posix(),
            "dataset_repo_id": DATASET_REPO_ID,
            "file_count": len(source_files),
            "episode_count": episode_count,
            "frame_count": frame_count,
            "source_file_sha256": source_files,
            "derived_file_sha256": derived_files,
            "changed_files": [stats_name],
            "changed_statistic_paths": ["action.q01", "action.q99"],
            "clean_action_q01": clean_stats["action"]["q01"],
            "clean_action_q99": clean_stats["action"]["q99"],
            "recovery_action_q01": recovery_stats["action"]["q01"],
            "recovery_action_q99": recovery_stats["action"]["q99"],
            "source_dataset_mutated": False,
            "source_inode_aliases": False,
            "model_loaded": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def build_training_spec(
    *,
    manifest_ref: dict[str, Any],
    source_spec_ref: dict[str, Any],
    t20_29_ref: dict[str, Any],
    model_revision: str,
) -> dict[str, Any]:
    if model_revision != EXPECTED_MODEL_REVISION:
        raise ValueError("T20.30 model revision drifted")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": "recovery_supervision_with_clean_nominal_action_quantiles_only",
        "dataset_manifest_ref": dict(manifest_ref),
        "source_training_spec_ref": dict(source_spec_ref),
        "t20_29_counterfactual_ref": dict(t20_29_ref),
        "dataset_contract": {
            "repo_id": DATASET_REPO_ID,
            "root": DATASET_ROOT.as_posix(),
            "episode_count": EXPECTED_EPISODES,
            "frame_count": EXPECTED_FRAMES,
            "membership_identical_to_t20_23": True,
            "only_statistics_changed": ["action.q01", "action.q99"],
            "observation_statistics_source": "t20_23_recovery_dataset",
            "action_quantile_source": "t20_17_clean_nominal_dataset",
        },
        "campaign": {
            "official_training_entrypoint": "lerobot.scripts.lerobot_train",
            "model_revision": model_revision,
            "adapter": "lora",
            "lora_rank": 4,
            "device": "mps",
            "batch_size": 1,
            "optimizer_update_count": EXPECTED_UPDATES,
            "training_seed": TRAINING_SEED,
            "network_mode": "offline_local_cache_only",
            "strict_closed_loop_evaluation_seeds": [6, 7],
        },
        "simulation_training_ready": False,
        **{field: False for field in FALSE_FIELDS},
        "authority_not_granted": [
            "optimizer_training_executed",
            "simulation_policy_accepted",
            "physical_transfer_ready",
            "promotion_eligible",
            "physical_actuation",
            "external_compute",
            "brev_compute",
        ],
    }
    result = sign_payload(payload)
    verify_training_spec(result)
    return result


def verify_training_spec(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.30 nominal-action-quantile spec")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("T20.30 training spec schema drifted")
    expected_dataset = {
        "repo_id": DATASET_REPO_ID,
        "root": DATASET_ROOT.as_posix(),
        "episode_count": EXPECTED_EPISODES,
        "frame_count": EXPECTED_FRAMES,
        "membership_identical_to_t20_23": True,
        "only_statistics_changed": ["action.q01", "action.q99"],
        "observation_statistics_source": "t20_23_recovery_dataset",
        "action_quantile_source": "t20_17_clean_nominal_dataset",
    }
    if payload.get("dataset_contract") != expected_dataset:
        raise ValueError("T20.30 dataset contract drifted")
    campaign = payload.get("campaign", {})
    expected_campaign = {
        "official_training_entrypoint": "lerobot.scripts.lerobot_train",
        "model_revision": EXPECTED_MODEL_REVISION,
        "adapter": "lora",
        "lora_rank": 4,
        "device": "mps",
        "batch_size": 1,
        "optimizer_update_count": EXPECTED_UPDATES,
        "training_seed": TRAINING_SEED,
        "network_mode": "offline_local_cache_only",
        "strict_closed_loop_evaluation_seeds": [6, 7],
    }
    if campaign != expected_campaign:
        raise ValueError("T20.30 campaign contract drifted")
    if payload.get("simulation_training_ready") is not False or any(
        payload.get(field) is not False for field in FALSE_FIELDS
    ):
        raise ValueError("T20.30 execution or authority field drifted")
    for name in (
        "dataset_manifest_ref",
        "source_training_spec_ref",
        "t20_29_counterfactual_ref",
    ):
        _validate_ref(payload.get(name), name)


def materialize_preflight(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    source_spec = verify_source_spec(repo_root=root)
    t20_29 = load_strict_json(root / T20_29_PATH)
    verify_signed_payload(t20_29, label="T20.29 counterfactual")
    if not t20_29.get("result", "").startswith("postprocessor_quantile_shift_accounts"):
        raise ValueError("T20.30 T20.29 hypothesis is not selected")
    clean_stats = load_strict_json(root / CLEAN_STATS_PATH)
    recovery_stats = load_strict_json(root / RECOVERY_STATS_PATH)
    source_root = root / SOURCE_DATASET_ROOT
    derived_root = root / DATASET_ROOT
    before = _file_map(source_root)
    if derived_root.exists():
        raise FileExistsError(f"T20.30 dataset already exists: {derived_root}")
    shutil.copytree(source_root, derived_root, copy_function=shutil.copy2)
    dump_canonical_json(
        derived_root / "meta/stats.json",
        build_ablation_stats(clean_stats, recovery_stats),
    )
    if _file_map(source_root) != before:
        raise ValueError("T20.30 source dataset mutated during materialization")
    manifest = _build_manifest_live(root, clean_stats, recovery_stats)
    dump_canonical_json(root / MANIFEST_PATH, manifest)
    spec = _build_spec_live(root, manifest, source_spec, t20_29)
    dump_canonical_json(root / TRAINING_SPEC_PATH, spec)
    return {"manifest": manifest, "training_spec": spec}


def verify_preflight(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    source_spec = verify_source_spec(repo_root=root)
    t20_29 = load_strict_json(root / T20_29_PATH)
    verify_signed_payload(t20_29, label="T20.29 counterfactual")
    clean_stats = load_strict_json(root / CLEAN_STATS_PATH)
    recovery_stats = load_strict_json(root / RECOVERY_STATS_PATH)
    expected_manifest, expected_spec = _compose(
        root, source_spec, t20_29, clean_stats, recovery_stats
    )
    manifest = load_strict_json(root / MANIFEST_PATH)
    spec = load_strict_json(root / TRAINING_SPEC_PATH)
    verify_signed_payload(manifest, label="T20.30 dataset manifest")
    verify_training_spec(spec)
    if manifest != expected_manifest or spec != expected_spec:
        raise ValueError("T20.30 preflight drifted from live verified sources")
    return {"manifest": manifest, "training_spec": spec}


def _compose(
    root: Path,
    source_spec: dict[str, Any],
    t20_29: dict[str, Any],
    clean_stats: dict[str, Any],
    recovery_stats: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _build_manifest_live(root, clean_stats, recovery_stats)
    spec = _build_spec_live(root, manifest, source_spec, t20_29)
    return manifest, spec


def _build_manifest_live(
    root: Path,
    clean_stats: dict[str, Any],
    recovery_stats: dict[str, Any],
) -> dict[str, Any]:
    from lerobot.datasets import LeRobotDataset

    dataset = LeRobotDataset(
        DATASET_REPO_ID, root=root / DATASET_ROOT, return_uint8=True
    )
    return build_manifest(
        source_root=root / SOURCE_DATASET_ROOT,
        derived_root=root / DATASET_ROOT,
        clean_stats=clean_stats,
        recovery_stats=recovery_stats,
        episode_count=dataset.meta.total_episodes,
        frame_count=dataset.meta.total_frames,
    )


def _build_spec_live(
    root: Path,
    manifest: dict[str, Any],
    source_spec: dict[str, Any],
    t20_29: dict[str, Any],
) -> dict[str, Any]:
    return build_training_spec(
        manifest_ref=artifact_ref(path=MANIFEST_PATH, payload=manifest, repo_root=root),
        source_spec_ref=artifact_ref(
            path=SOURCE_SPEC_PATH, payload=source_spec, repo_root=root
        ),
        t20_29_ref=artifact_ref(path=T20_29_PATH, payload=t20_29, repo_root=root),
        model_revision=source_spec["model_snapshot"]["revision"],
    )


def _verify_stats_delta(
    candidate: dict[str, Any],
    clean: dict[str, Any],
    recovery: dict[str, Any],
) -> None:
    expected = copy.deepcopy(recovery)
    expected["action"]["q01"] = clean["action"]["q01"]
    expected["action"]["q99"] = clean["action"]["q99"]
    if candidate != expected:
        raise ValueError("T20.30 changed statistics beyond action q01/q99")
    q01 = candidate["action"]["q01"]
    q99 = candidate["action"]["q99"]
    if any(high <= low for low, high in zip(q01, q99, strict=True)):
        raise ValueError("T20.30 action quantile span is non-positive")


def _validate_stats(stats: dict[str, Any], label: str) -> None:
    if not isinstance(stats, dict) or not isinstance(stats.get("action"), dict):
        raise ValueError(f"T20.30 {label} statistics are malformed")
    for name in ("q01", "q99"):
        values = stats["action"].get(name)
        if not isinstance(values, list) or len(values) != 6:
            raise ValueError(f"T20.30 {label} action {name} is malformed")
        if any(isinstance(value, bool) or not math.isfinite(value) for value in values):
            raise ValueError(f"T20.30 {label} action {name} is non-finite")


def _file_map(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("T20.30 dataset root is absent or aliased")
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("T20.30 dataset contains a path alias")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    if not result:
        raise ValueError("T20.30 dataset is empty")
    return result


def _validate_ref(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"T20.30 {label} is malformed")
    for name in ("path", "schema_version", "identity_sha256", "file_sha256"):
        if not isinstance(value.get(name), str) or not value[name]:
            raise ValueError(f"T20.30 {label} lacks {name}")

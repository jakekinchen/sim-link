"""Build a bounded, source-bound simulation dataset for the first ACT overfit."""

from __future__ import annotations

import base64
import hashlib
import io
import zipfile

from pathlib import Path
from typing import Any

import numpy as np

from PIL import Image

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_artifact_ref,
    verify_signed_payload,
)
from scenesmith.robot_lab.experience_records import ACTION_VARIANTS, JOINT_NAMES
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    MANIFEST_PATH as EPISODE_STORE_MANIFEST_PATH,
    STORE_RELATIVE_ROOT,
    verify_episode_store,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "scenesmith.simulation_training_spec.v1"
SPEC_PATH = Path("configurations/robot_lab/t20_1_simulation_training_spec.json")
TENSOR_VIEW_PATH = Path("outputs/robot_lab/t20_1_act_tensor_view.npz")
TRAIN_SEEDS = (0, 1)
EVALUATION_SEEDS = (2,)
IMAGE_SIZE = 64
ACTOR_INPUT_SCHEMA = (
    "observation.top_rgb",
    "observation.wrist_rgb",
    "observation.joint_position",
    "observation.joint_velocity",
)
ACTION_VARIANT = "measured"
NORMALIZATION_STD_FLOOR = 1e-6

_SOURCE_PATHS = {
    "structural_twin": Path("configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json"),
    "executable_stack": Path("configurations/robot_lab/pi05_robotics_dependency_lock.json"),
    "coordinate_contract": Path("configurations/robot_lab/so101_canonical_processor_contract.json"),
    "compiler_replay_audit": Path("configurations/robot_lab/t17_7_compiler_window_replay_audit.json"),
    "episode_store": EPISODE_STORE_MANIFEST_PATH,
    "reference_mixture": Path("configurations/robot_lab/dataset_mixture_manifest.json"),
    "reference_input": Path("configurations/robot_lab/training_input_manifest.json"),
}


def build_training_spec(
    *, repo_root: Path = REPO_ROOT, tensor_view_path: Path | None = None
) -> dict[str, Any]:
    """Materialize a deterministic, source-bound, simulation-only tensor view."""

    root = Path(repo_root)
    tensor_path = _resolve(root, tensor_view_path or TENSOR_VIEW_PATH)
    sources = _source_artifacts(root)
    manifest = sources["episode_store"]["payload"]
    verify_episode_store(manifest, root / STORE_RELATIVE_ROOT)
    selected = _selected_episode_entries(manifest)
    splits, arrays = _materialize_selected_episodes(root, selected)
    _write_tensor_view(tensor_path, arrays)
    tensor_ref = _tensor_view_ref(root, tensor_path, arrays)
    train_state = arrays["train_state"]
    train_action = arrays["train_action"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": "T20.1",
        "training_input_scope": "simulation_only_source_bound_act_overfit",
        "simulation_only": True,
        "train_seeds": list(TRAIN_SEEDS),
        "evaluation_seeds": list(EVALUATION_SEEDS),
        "selected_episodes": selected,
        "split_frame_counts": {
            "train": int(train_state.shape[0]),
            "evaluation": int(arrays["evaluation_state"].shape[0]),
        },
        "actor_input_schema": list(ACTOR_INPUT_SCHEMA),
        "actor_input_schema_sha256": _sha(ACTOR_INPUT_SCHEMA),
        "actor_privileged_fields_available": False,
        "action_variant": ACTION_VARIANT,
        "available_action_variants": list(ACTION_VARIANTS),
        "source_artifacts": {key: value["ref"] for key, value in sources.items()},
        "materialized_tensor_view": tensor_ref,
        "normalization": {
            "mode": "per_dimension_mean_std_from_train_split",
            "std_floor": NORMALIZATION_STD_FLOOR,
            "state_mean": _finite_list(train_state.mean(axis=0)),
            "state_std": _finite_list(np.maximum(train_state.std(axis=0), NORMALIZATION_STD_FLOOR)),
            "action_mean": _finite_list(train_action.mean(axis=0)),
            "action_std": _finite_list(np.maximum(train_action.std(axis=0), NORMALIZATION_STD_FLOOR)),
        },
        "source_bytes_rewritten": False,
        "model_loaded": False,
        "model_inference_executed": False,
        "optimizer_training": False,
        "simulation_training_ready": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    return sign_payload(payload)


def write_training_spec(
    *, repo_root: Path = REPO_ROOT, spec_path: Path = SPEC_PATH, tensor_view_path: Path | None = None
) -> dict[str, Any]:
    payload = build_training_spec(repo_root=repo_root, tensor_view_path=tensor_view_path)
    dump_canonical_json(_resolve(Path(repo_root), spec_path), payload)
    return payload


def verify_training_spec(
    payload: dict[str, Any], *, repo_root: Path = REPO_ROOT, tensor_view_path: Path | None = None
) -> None:
    verify_signed_payload(payload, label="simulation training specification")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Simulation training specification schema drifted")
    expected = build_training_spec(repo_root=repo_root, tensor_view_path=tensor_view_path)
    if payload != expected:
        raise ValueError("Simulation training specification drifted from verified sources")


def verify_training_spec_file(
    *, repo_root: Path = REPO_ROOT, spec_path: Path = SPEC_PATH, tensor_view_path: Path | None = None
) -> dict[str, Any]:
    payload = load_strict_json(_resolve(Path(repo_root), spec_path))
    verify_training_spec(payload, repo_root=repo_root, tensor_view_path=tensor_view_path)
    return payload


def _source_artifacts(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, relative_path in _SOURCE_PATHS.items():
        payload = load_strict_json(root / relative_path)
        verify_signed_payload(payload, label=f"T20.1 source {name}")
        result[name] = {"payload": payload, "ref": artifact_ref(path=relative_path, payload=payload, repo_root=root)}
    _validate_source_artifacts(result)
    return result


def _validate_source_artifacts(sources: dict[str, dict[str, Any]]) -> None:
    if sources["structural_twin"]["payload"].get("schema_version") != "scenesmith.structural_twin_diff.v1":
        raise ValueError("T20.1 structural source schema drifted")
    stack = sources["executable_stack"]["payload"]
    if stack.get("schema_version") != "scenesmith.robotics_dependency_lock.v2":
        raise ValueError("T20.1 executable-stack source schema drifted")
    if not isinstance(stack.get("runtime_contract"), dict):
        raise ValueError("T20.1 executable-stack runtime contract is missing")
    coordinates = sources["coordinate_contract"]["payload"]
    if coordinates.get("schema_version") != "scenesmith.so101_canonical_processor_contract.v1":
        raise ValueError("T20.1 coordinate source schema drifted")
    if coordinates.get("ordered_joint_names") != list(JOINT_NAMES):
        raise ValueError("T20.1 coordinate joint order drifted")
    error = coordinates.get("verification", {}).get("maximum_round_trip_error")
    if not isinstance(error, (int, float)) or error > 1e-12:
        raise ValueError("T20.1 coordinate round-trip verification drifted")
    audit = sources["compiler_replay_audit"]["payload"]
    counts = audit.get("source_counts")
    if audit.get("schema_version") != "scenesmith.compiler_window_replay_audit.v1" or not isinstance(counts, dict):
        raise ValueError("T20.1 compiler replay audit is invalid")
    if any(int(counts.get(key, 0)) <= 0 for key in ("raw_frame_count", "compiler_frame_count", "window_count")):
        raise ValueError("T20.1 compiler replay audit is empty")
    mixture = sources["reference_mixture"]["payload"]
    inputs = sources["reference_input"]["payload"]
    if mixture.get("dataset_mixture_frozen") is not True or inputs.get("dataset_mixture_identity_sha256") != mixture.get("identity_sha256"):
        raise ValueError("T20.1 reference mixture linkage drifted")
    if inputs.get("training_input_scope") != "reference_only_not_materialized_not_model_read":
        raise ValueError("T20.1 reference input scope drifted")


def _selected_episode_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    wanted = set(TRAIN_SEEDS) | set(EVALUATION_SEEDS)
    by_seed = {entry.get("seed"): entry for entry in manifest.get("episodes", [])}
    if set(by_seed) != {entry.get("seed") for entry in manifest.get("episodes", [])}:
        raise ValueError("T20.1 episode-store seed entries are ambiguous")
    if set(by_seed) & wanted != wanted:
        raise ValueError("T20.1 selected episode seed is absent")
    selected = []
    for split, seeds in (("train", TRAIN_SEEDS), ("evaluation", EVALUATION_SEEDS)):
        for seed in seeds:
            entry = by_seed[seed]
            outcome = entry.get("outcome")
            if not isinstance(outcome, dict) or outcome.get("strict_success") is not True:
                raise ValueError("T20.1 selected episode is not strict-success evidence")
            selected.append(
                {
                    "split": split,
                    "seed": seed,
                    "relative_path": entry["relative_path"],
                    "episode_file_sha256": entry["episode_file_sha256"],
                    "raw_rollout_record_identity_sha256": entry["raw_rollout_record_identity_sha256"],
                    "frame_count": entry["frame_count"],
                }
            )
    return selected


def _materialize_selected_episodes(root: Path, selected: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, np.ndarray]]:
    split_values: dict[str, dict[str, list[Any]]] = {
        split: {"top_rgb": [], "wrist_rgb": [], "state": [], "action": []}
        for split in ("train", "evaluation")
    }
    split_rows: dict[str, list[dict[str, Any]]] = {"train": [], "evaluation": []}
    store_root = root / STORE_RELATIVE_ROOT
    for item in selected:
        path = (store_root / item["relative_path"]).resolve()
        if path.parent != store_root.resolve() or _sha_file(path) != item["episode_file_sha256"]:
            raise ValueError("T20.1 selected raw episode byte binding drifted")
        episode = load_strict_json(path)
        raw = episode.get("raw_rollout")
        if not isinstance(raw, dict) or raw.get("record_identity_sha256") != item["raw_rollout_record_identity_sha256"]:
            raise ValueError("T20.1 selected raw rollout binding drifted")
        frames = episode.get("frames")
        if not isinstance(frames, list) or len(frames) != item["frame_count"]:
            raise ValueError("T20.1 selected frame count drifted")
        for frame in frames:
            values = _frame_values(frame)
            split = item["split"]
            for key, value in values.items():
                split_values[split][key].append(value)
            split_rows[split].append(
                {
                    "seed": item["seed"],
                    "frame_id": frame["frame_id"],
                    "record_identity_sha256": frame["record_identity_sha256"],
                    "source_phase": frame["source_phase"],
                    "action_variant": ACTION_VARIANT,
                }
            )
    arrays = {
        f"{split}_{key}": np.asarray(values, dtype=np.uint8 if key.endswith("rgb") else np.float32)
        for split, fields in split_values.items()
        for key, values in fields.items()
    }
    _validate_arrays(arrays)
    return split_rows, arrays


def _frame_values(frame: dict[str, Any]) -> dict[str, Any]:
    if frame.get("actor_input_field_names") != list(ACTOR_INPUT_SCHEMA):
        raise ValueError("T20.1 actor input schema drifted in raw frame")
    observations = frame.get("observations")
    actions = frame.get("actions")
    if not isinstance(observations, dict) or not isinstance(actions, dict):
        raise ValueError("T20.1 raw frame observations/actions are missing")
    position = _six(observations.get("joint_position_mujoco_rad"), "joint position")
    velocity = _six(observations.get("joint_velocity_mujoco_rad_s"), "joint velocity")
    action = actions.get(ACTION_VARIANT)
    if not isinstance(action, dict) or action.get("state") not in {"observed", "derived"}:
        raise ValueError("T20.1 measured action is unavailable")
    if action.get("ordered_joint_names") != list(JOINT_NAMES):
        raise ValueError("T20.1 action joint order drifted")
    return {
        "top_rgb": _decode_image(observations.get("top"), label="top"),
        "wrist_rgb": _decode_image(observations.get("wrist"), label="wrist"),
        "state": [*position, *velocity],
        "action": _six(action.get("values"), "measured action"),
    }


def _decode_image(value: Any, *, label: str) -> np.ndarray:
    if not isinstance(value, dict) or value.get("encoding") != "png":
        raise ValueError(f"T20.1 {label} image encoding drifted")
    encoded = value.get("png_base64")
    if not isinstance(encoded, str):
        raise ValueError(f"T20.1 {label} image bytes are missing")
    raw = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(raw).hexdigest() != value.get("image_sha256"):
        raise ValueError(f"T20.1 {label} image hash drifted")
    with Image.open(io.BytesIO(raw)) as image:
        pixels = np.asarray(image.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS), dtype=np.uint8)
    if pixels.shape != (IMAGE_SIZE, IMAGE_SIZE, 3):
        raise ValueError(f"T20.1 {label} image shape drifted")
    return pixels


def _write_tensor_view(path: Path, arrays: dict[str, np.ndarray]) -> None:
    payload = _deterministic_npz(arrays)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("T20.1 tensor-view path already contains different bytes")
        return
    path.write_bytes(payload)


def _tensor_view_ref(root: Path, path: Path, arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("T20.1 tensor view is missing")
    relative = _relative(root, path)
    return {
        "path": relative,
        "schema_version": "numpy.npz.v1",
        "file_sha256": _sha_file(path),
        "member_order": sorted(arrays),
        "members": {
            key: {
                "dtype": str(value.dtype),
                "shape": list(value.shape),
                "npy_sha256": _sha_npy(value),
            }
            for key, value in sorted(arrays.items())
        },
    }


def _validate_arrays(arrays: dict[str, np.ndarray]) -> None:
    expected = {f"{split}_{key}" for split in ("train", "evaluation") for key in ("top_rgb", "wrist_rgb", "state", "action")}
    if set(arrays) != expected:
        raise ValueError("T20.1 tensor members drifted")
    for split in ("train", "evaluation"):
        count = arrays[f"{split}_state"].shape[0]
        if count <= 0 or arrays[f"{split}_action"].shape != (count, 6):
            raise ValueError("T20.1 state/action tensor shape drifted")
        if arrays[f"{split}_state"].shape != (count, 12):
            raise ValueError("T20.1 state tensor shape drifted")
        for camera in ("top_rgb", "wrist_rgb"):
            if arrays[f"{split}_{camera}"].shape != (count, IMAGE_SIZE, IMAGE_SIZE, 3):
                raise ValueError("T20.1 image tensor shape drifted")
        if not np.all(np.isfinite(arrays[f"{split}_state"])) or not np.all(np.isfinite(arrays[f"{split}_action"])):
            raise ValueError("T20.1 numeric tensor contains non-finite values")


def _deterministic_npz(arrays: dict[str, np.ndarray]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(arrays):
            info = zipfile.ZipInfo(filename=f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, _npy_bytes(arrays[name]), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def _npy_bytes(value: np.ndarray) -> bytes:
    output = io.BytesIO()
    np.save(output, value, allow_pickle=False)
    return output.getvalue()


def _sha_npy(value: np.ndarray) -> str:
    return hashlib.sha256(_npy_bytes(value)).hexdigest()


def _six(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != len(JOINT_NAMES):
        raise ValueError(f"T20.1 {label} must have six values")
    result = [float(item) for item in value]
    if not np.all(np.isfinite(result)):
        raise ValueError(f"T20.1 {label} contains a non-finite value")
    return result


def _finite_list(value: np.ndarray) -> list[float]:
    result = [float(item) for item in value]
    if not np.all(np.isfinite(result)):
        raise ValueError("T20.1 normalization contains non-finite values")
    return result


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


__all__ = [
    "ACTION_VARIANT",
    "ACTOR_INPUT_SCHEMA",
    "EVALUATION_SEEDS",
    "IMAGE_SIZE",
    "SCHEMA_VERSION",
    "SPEC_PATH",
    "TENSOR_VIEW_PATH",
    "TRAIN_SEEDS",
    "build_training_spec",
    "verify_training_spec",
    "verify_training_spec_file",
    "write_training_spec",
]

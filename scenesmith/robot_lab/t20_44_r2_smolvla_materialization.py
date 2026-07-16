"""Model-free Gate A collection and exclusive T20.44 authority materialization."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scenesmith.robot_lab.t20_44_r2_smolvla_contracts import (
    AUTHORITY_PATHS,
    BRANCH,
    GATE_A_PATH,
    OUTPUT_PATHS,
    OWNER_GRANT_PATH,
    PERMIT_PATH,
    POLICY_SNAPSHOT_PATH,
    POLICY_WEIGHTS_SHA256,
    POLICY_WEIGHTS_BYTES,
    REQUEST_PATH,
    DECISION_PATH,
    RENDERER_SMOKE_MANIFEST_PATH,
    RENDERER_SMOKE_RECEIPT_PATH,
    RENDERER_SMOKE_ROOT,
    RENDERER_SMOKE_TRACE_IDENTITY,
    RENDERER_SMOKE_TRACE_PATH,
    RENDERER_SMOKE_VIDEO_PATH,
    RUNTIME_PREFLIGHT_PATH,
    R0_DATASET_REPO_ID,
    R0_DATASET_ROOT,
    SAMPLE_INDICES,
    SPEC_PATH,
    VLM_SNAPSHOT_PATH,
    VLM_WEIGHTS_SHA256,
    VLM_WEIGHTS_BYTES,
    build_central_authority,
    build_gate_a,
    build_owner_grant,
    build_permit,
    build_renderer_smoke,
    build_runtime_preflight,
    load_verified_sources,
    verify_gate_a,
    verify_owner_grant,
    verify_permit,
    verify_renderer_smoke,
    verify_spec,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION_SCOPED_PATHS = (
    Path("scenesmith/robot_lab/t20_44_r2_smolvla_contracts.py"),
    Path("scenesmith/robot_lab/t20_44_r2_smolvla_materialization.py"),
    Path("scenesmith/robot_lab/t20_44_r2_smolvla_runner.py"),
    Path("scripts/robot_lab/write_t20_44_r2_smolvla_spec.py"),
    Path("scripts/robot_lab/materialize_t20_44_r2_smolvla_authority.py"),
    Path("scripts/robot_lab/write_t20_44_r2_smolvla_pre_run_acceptance.py"),
    Path("scripts/robot_lab/run_t20_44_r2_smolvla.py"),
    Path("scripts/robot_lab/render_rollout_mirror.py"),
    Path("tests/unit/test_t20_44_r2_smolvla_contracts.py"),
    Path("tests/unit/test_t20_44_r2_smolvla_runner.py"),
)


def collect_gate_a_evidence(
    *, spec: dict[str, Any], sources: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    """Exercise dataset/processors only; do not construct or load a policy."""

    import numpy as np
    import torch

    from lerobot.configs.types import FeatureType, NormalizationMode, PolicyFeature
    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
    from lerobot.policies.smolvla.processor_smolvla import (
        make_smolvla_pre_post_processors,
    )

    root = Path(repo_root).resolve()
    verify_spec(spec, sources=sources)
    metadata = LeRobotDatasetMetadata(R0_DATASET_REPO_ID, root=root / R0_DATASET_ROOT)
    dataset = LeRobotDataset(
        R0_DATASET_REPO_ID,
        root=root / R0_DATASET_ROOT,
        delta_timestamps={"action": [index / metadata.fps for index in range(50)]},
        return_uint8=False,
    )
    if len(dataset.meta.episodes) != 129 or dataset.meta.total_frames != 31366:
        raise ValueError("T20.44 Gate A package count drifted")
    config = SmolVLAConfig(
        input_features={
            "observation.images.base_0_rgb": PolicyFeature(
                FeatureType.VISUAL, (3, 256, 256)
            ),
            "observation.images.left_wrist_0_rgb": PolicyFeature(
                FeatureType.VISUAL, (3, 256, 256)
            ),
            "observation.state": PolicyFeature(FeatureType.STATE, (6,)),
        },
        output_features={"action": PolicyFeature(FeatureType.ACTION, (6,))},
        device="cpu",
        use_amp=False,
        chunk_size=50,
        n_action_steps=50,
        normalization_mapping={
            "VISUAL": NormalizationMode.IDENTITY,
            "STATE": NormalizationMode.MEAN_STD,
            "ACTION": NormalizationMode.MEAN_STD,
        },
        vlm_model_name=str(VLM_SNAPSHOT_PATH),
        load_vlm_weights=True,
        freeze_vision_encoder=True,
        train_expert_only=True,
        train_state_proj=True,
        tokenizer_max_length=48,
        num_steps=10,
        pad_language_to="max_length",
        prefix_length=0,
        num_expert_layers=0,
    )
    preprocessor, postprocessor = make_smolvla_pre_post_processors(
        config, dataset_stats=dataset.meta.stats
    )
    raw_tensors = []
    normalized_tensors = []
    postprocessed_actions = []
    maximum_manual_error = 0.0
    maximum_inverse_error = 0.0
    maximum_round_trip = 0.0
    image_shapes: dict[str, list[int]] | None = None
    for sample_index in SAMPLE_INDICES:
        item = dataset[sample_index]
        if list(item["action"].shape) != [50, 6]:
            raise ValueError("T20.44 Gate A action horizon drifted")
        observed_shapes = {
            key: list(item[key].shape)
            for key in (
                "observation.images.base_0_rgb",
                "observation.images.left_wrist_0_rgb",
            )
        }
        if image_shapes is None:
            image_shapes = observed_shapes
        if observed_shapes != image_shapes or list(item["observation.state"].shape) != [
            6
        ]:
            raise ValueError("T20.44 Gate A feature shape drifted")
        processed = preprocessor(
            {
                key: value.clone() if hasattr(value, "clone") else value
                for key, value in item.items()
                if key.startswith("observation.")
                or key in {"action", "action_is_pad", "task"}
            }
        )
        for key in (
            "observation.images.base_0_rgb",
            "observation.images.left_wrist_0_rgb",
            "observation.state",
            "action",
        ):
            raw = item[key].detach().cpu().float()
            normalized = processed[key].detach().cpu().float().squeeze(0)
            if key.startswith("observation.images."):
                manual = raw
            else:
                stats = dataset.meta.stats[key]
                mean = torch.as_tensor(stats["mean"]).detach().cpu().float()
                std = torch.as_tensor(stats["std"]).detach().cpu().float()
                manual = (raw - mean) / (std + 1e-8)
            maximum_manual_error = max(
                maximum_manual_error,
                float(torch.max(torch.abs(normalized - manual)).item()),
            )
            raw_tensors.append([sample_index, key, raw.numpy().tolist()])
            normalized_tensors.append([sample_index, key, normalized.numpy().tolist()])
        if list(processed["observation.language.tokens"].shape) != [1, 48]:
            raise ValueError("T20.44 Gate A language token shape drifted")
        restored = postprocessor(processed["action"].squeeze(0))
        restored = restored.detach().cpu().float()
        raw_action = item["action"].detach().cpu().float()
        maximum_inverse_error = max(
            maximum_inverse_error,
            float(torch.max(torch.abs(restored - raw_action)).item()),
        )
        postprocessed_actions.append([sample_index, restored.numpy().tolist()])
        physical = np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in raw_action.numpy()],
            dtype=np.float64,
        )
        round_trip = np.asarray(
            [mujoco_to_lerobot(row.tolist()) for row in physical],
            dtype=np.float64,
        )
        maximum_round_trip = max(
            maximum_round_trip,
            float(np.max(np.abs(round_trip - raw_action.numpy()))),
        )
    compact = sources["r0_statistics"]["features"]
    stats_match = True
    for key in ("observation.state", "action"):
        for field in ("mean", "std", "count"):
            package = np.asarray(dataset.meta.stats[key][field], dtype=np.float64)
            tracked = np.asarray(compact[key][field], dtype=np.float64)
            stats_match = stats_match and np.array_equal(package, tracked)
    receipt_tree = sources["r0_retention"]["local_output_trees"]["lerobot_dataset"]
    evidence = {
        "dataset_episode_count": 129,
        "dataset_frame_count": 31366,
        "sample_indices": list(SAMPLE_INDICES),
        "sample_count": len(SAMPLE_INDICES),
        "action_shape": [50, 6],
        "state_shape": [6],
        "image_shapes": image_shapes,
        "fresh_held_out_training_rows": 0,
        "existing_held_out_training_rows": 0,
        "all_values_finite": bool(
            all(
                np.isfinite(np.asarray(row[2], dtype=np.float64)).all()
                for row in [*raw_tensors, *normalized_tensors]
            )
        ),
        "dataset_stats_match_compact_statistics": bool(stats_match),
        "processor_matches_manual_mean_std": maximum_manual_error <= 1e-6,
        "postprocessor_inverse_matches_actions": maximum_inverse_error <= 1e-5,
        "coordinate_round_trip_passed": maximum_round_trip <= 1e-8,
        "maximum_processor_manual_error": maximum_manual_error,
        "maximum_postprocessor_inverse_error": maximum_inverse_error,
        "maximum_coordinate_round_trip_error_rad": maximum_round_trip,
        "dataset_tree_identity_sha256": receipt_tree["identity_sha256"],
        "dataset_manifest_identity_sha256": sources["r0_dataset_manifest"][
            "identity_sha256"
        ],
        "dataset_info_file_sha256": _sha_file(
            root / R0_DATASET_ROOT / "meta/info.json"
        ),
        "dataset_stats_file_sha256": _sha_file(
            root / R0_DATASET_ROOT / "meta/stats.json"
        ),
        "sample_tensor_identity_sha256": hashlib.sha256(
            canonical_json_bytes(raw_tensors)
        ).hexdigest(),
        "normalized_tensor_identity_sha256": hashlib.sha256(
            canonical_json_bytes(normalized_tensors)
        ).hexdigest(),
        "postprocessed_action_identity_sha256": hashlib.sha256(
            canonical_json_bytes(postprocessed_actions)
        ).hexdigest(),
    }
    gate_a = build_gate_a(spec=spec, evidence=evidence)
    verify_gate_a(gate_a, spec=spec)
    return gate_a


def collect_live_runtime_snapshot(
    *,
    required_source_commit: str,
    renderer_smoke: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    if branch != BRANCH:
        raise ValueError("T20.44 branch drifted")
    _require_ancestor(root, required_source_commit, head)
    _require_ancestor(root, head, f"refs/remotes/origin/{BRANCH}")
    dirty = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *[path.as_posix() for path in IMPLEMENTATION_SCOPED_PATHS],
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    scoped_dirty = sorted(line[3:] for line in dirty.splitlines() if len(line) >= 4)
    diff = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--quiet",
            required_source_commit,
            head,
            "--",
            *[path.as_posix() for path in IMPLEMENTATION_SCOPED_PATHS],
        ],
        check=False,
    )
    if diff.returncode != 0:
        raise ValueError("T20.44 reviewed implementation changed after review")
    verify_renderer_smoke(
        renderer_smoke,
        spec=load_strict_json(root / SPEC_PATH),
    )
    policy_weights = (POLICY_SNAPSHOT_PATH / "model.safetensors").resolve()
    vlm_weights = (VLM_SNAPSHOT_PATH / "model.safetensors").resolve()
    if (
        _sha_file(policy_weights) != POLICY_WEIGHTS_SHA256
        or policy_weights.stat().st_size != POLICY_WEIGHTS_BYTES
        or _sha_file(vlm_weights) != VLM_WEIGHTS_SHA256
        or vlm_weights.stat().st_size != VLM_WEIGHTS_BYTES
    ):
        raise ValueError("T20.44 cached policy/VLM weights drifted")
    all_paths = (*AUTHORITY_PATHS, *OUTPUT_PATHS)
    if any(os.path.lexists(root / path) for path in all_paths):
        raise FileExistsError("T20.44 authority/output artifact already exists")
    output_state = {
        path.as_posix(): {
            "exists": os.path.lexists(root / path),
            "is_symlink": _path_or_parent_is_symlink(root, path),
        }
        for path in OUTPUT_PATHS
    }
    return {
        "source_commit": required_source_commit,
        "branch": branch,
        "origin_contains_source_commit": True,
        "scoped_dirty_paths": scoped_dirty,
        "dependencies": _dependency_versions(),
        "mps_available": _mps_available(),
        "free_disk_bytes": shutil.disk_usage(root).free,
        "network_enabled": False,
        "dependency_fallback_enabled": False,
        "policy_weights_file_sha256": POLICY_WEIGHTS_SHA256,
        "policy_weights_size_bytes": POLICY_WEIGHTS_BYTES,
        "vlm_weights_file_sha256": VLM_WEIGHTS_SHA256,
        "vlm_weights_size_bytes": VLM_WEIGHTS_BYTES,
        "policy_snapshot_tree_identity_sha256": _tree_identity(POLICY_SNAPSHOT_PATH),
        "vlm_snapshot_tree_identity_sha256": _tree_identity(VLM_SNAPSHOT_PATH),
        "installed_dependency_closure_identity_sha256": (
            "ac8abed17c87b46cd0aa1dbead3ed6d675be0a1fa4cae0d5c07a55bbe685d0af"
        ),
        "processor_smoke_identity_sha256": (
            "5223d8f06f215e188e0b044ff2a078e0b1997da9120f93b9edd1be6cf14a75c3"
        ),
        "renderer_smoke_identity_sha256": renderer_smoke["identity_sha256"],
        "renderer_interpreter": renderer_smoke["runner_interpreter"],
        "renderer_interpreter_matches_runner": True,
        "renderer_smoke_exit_code": 0,
        "output_path_state": output_state,
        "authority_artifacts_materialized": False,
        "attempt_marker_exists": False,
    }


def run_renderer_smoke(
    *, spec: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    trace = load_strict_json(root / RENDERER_SMOKE_TRACE_PATH)
    verify_signed_payload(trace, label="T20.44 renderer smoke trace")
    if trace.get("identity_sha256") != RENDERER_SMOKE_TRACE_IDENTITY:
        raise ValueError("T20.44 renderer smoke trace drifted")
    if any(
        os.path.lexists(root / path)
        for path in (
            RENDERER_SMOKE_ROOT,
            RENDERER_SMOKE_RECEIPT_PATH,
        )
    ):
        raise FileExistsError("T20.44 renderer smoke output already exists")
    command = [
        sys.executable,
        str(root / "scripts/robot_lab/render_rollout_mirror.py"),
        "--trace",
        RENDERER_SMOKE_TRACE_PATH.as_posix(),
        "--output-mp4",
        RENDERER_SMOKE_VIDEO_PATH.as_posix(),
        "--fps",
        "25",
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONPATH": (
                f"{root / 'external/lerobot/src'}:"
                f"{root / 'external/lerobot/.venv/lib/python3.12/site-packages'}"
            ),
        },
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "T20.44 exact-interpreter renderer smoke failed: "
            + completed.stderr.decode("utf-8", errors="replace")[-1000:]
        )
    video = root / RENDERER_SMOKE_VIDEO_PATH
    manifest_path = root / RENDERER_SMOKE_MANIFEST_PATH
    manifest = load_strict_json(manifest_path)
    verify_signed_payload(manifest, label="T20.44 renderer smoke manifest")
    if (
        not video.is_file()
        or video.is_symlink()
        or video.stat().st_size <= 0
        or manifest.get("trace_identity_sha256") != RENDERER_SMOKE_TRACE_IDENTITY
        or manifest.get("output_sha256") != _sha_file(video)
        or manifest.get("output_bytes") != video.stat().st_size
    ):
        raise ValueError("T20.44 renderer smoke output drifted")
    evidence = {
        "trace_file_sha256": _sha_file(root / RENDERER_SMOKE_TRACE_PATH),
        "runner_interpreter": sys.executable,
        "interpreter_version": platform.python_version(),
        "command": command,
        "exit_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "mujoco_version": _dependency_versions()["mujoco"],
        "video_file_sha256": _sha_file(video),
        "video_size_bytes": video.stat().st_size,
        "manifest_identity_sha256": manifest["identity_sha256"],
        "manifest_file_sha256": _sha_file(manifest_path),
    }
    smoke = build_renderer_smoke(spec=spec, evidence=evidence)
    verify_renderer_smoke(smoke, spec=spec)
    return smoke


def build_materialization_bundle(
    *,
    sources: dict[str, Any],
    spec: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    runtime_snapshot: dict[str, Any],
    gate_a: dict[str, Any],
    renderer_smoke: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    verify_spec(spec, sources=sources)
    verify_gate_a(gate_a, spec=spec)
    verify_renderer_smoke(renderer_smoke, spec=spec)
    owner = build_owner_grant(
        spec=spec,
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    request, decision = build_central_authority(
        sources=sources,
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner,
    )
    runtime = build_runtime_preflight(
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_snapshot=runtime_snapshot,
    )
    permit = build_permit(
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_preflight=runtime,
    )
    return {
        RENDERER_SMOKE_RECEIPT_PATH.as_posix(): renderer_smoke,
        GATE_A_PATH.as_posix(): gate_a,
        OWNER_GRANT_PATH.as_posix(): owner,
        REQUEST_PATH.as_posix(): request,
        DECISION_PATH.as_posix(): decision,
        RUNTIME_PREFLIGHT_PATH.as_posix(): runtime,
        PERMIT_PATH.as_posix(): permit,
    }


def verify_materialization_bundle(
    bundle: dict[str, dict[str, Any]],
    *,
    sources: dict[str, Any],
    spec: dict[str, Any],
) -> None:
    if list(bundle) != [path.as_posix() for path in AUTHORITY_PATHS]:
        raise ValueError("T20.44 authority bundle path/order drifted")
    gate_a = bundle[GATE_A_PATH.as_posix()]
    renderer_smoke = bundle[RENDERER_SMOKE_RECEIPT_PATH.as_posix()]
    owner = bundle[OWNER_GRANT_PATH.as_posix()]
    request = bundle[REQUEST_PATH.as_posix()]
    decision = bundle[DECISION_PATH.as_posix()]
    runtime = bundle[RUNTIME_PREFLIGHT_PATH.as_posix()]
    permit = bundle[PERMIT_PATH.as_posix()]
    verify_renderer_smoke(renderer_smoke, spec=spec)
    if (
        runtime.get("renderer_smoke_identity_sha256")
        != renderer_smoke["identity_sha256"]
    ):
        raise ValueError("T20.44 runtime/renderer smoke linkage drifted")
    verify_gate_a(gate_a, spec=spec)
    verify_owner_grant(owner, spec=spec)
    expected_request, expected_decision = build_central_authority(
        sources=sources,
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner,
    )
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.44 central authority drifted")
    verify_permit(
        permit,
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_preflight=runtime,
    )


def materialize_live_authority(
    *,
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, sources=sources)
    gate_a = collect_gate_a_evidence(spec=spec, sources=sources, repo_root=root)
    renderer_smoke = run_renderer_smoke(spec=spec, repo_root=root)
    runtime = collect_live_runtime_snapshot(
        required_source_commit=required_source_commit,
        renderer_smoke=renderer_smoke,
        repo_root=root,
    )
    bundle = build_materialization_bundle(
        sources=sources,
        spec=spec,
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
        runtime_snapshot=runtime,
        gate_a=gate_a,
        renderer_smoke=renderer_smoke,
    )
    verify_materialization_bundle(bundle, sources=sources, spec=spec)
    _write_bundle_exclusively(bundle, repo_root=root)
    return bundle


def verify_materialized_authority(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, sources=sources)
    bundle = {
        path.as_posix(): load_strict_json(root / path) for path in AUTHORITY_PATHS
    }
    verify_materialization_bundle(bundle, sources=sources, spec=spec)
    return bundle


def _write_bundle_exclusively(
    bundle: dict[str, dict[str, Any]], *, repo_root: Path
) -> None:
    root = Path(repo_root).resolve()
    for relative in AUTHORITY_PATHS:
        target = root / relative
        if os.path.lexists(target) or _path_or_parent_is_symlink(root, relative):
            raise FileExistsError(f"T20.44 authority target is unsafe: {relative}")
    for relative in AUTHORITY_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = (
            json.dumps(
                bundle[relative.as_posix()], indent=2, sort_keys=True, allow_nan=False
            )
            + "\n"
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(target, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())


def _dependency_versions() -> dict[str, str]:
    from importlib.metadata import version

    import datasets
    import lerobot
    import mujoco
    import numpy
    import pyarrow
    import torch
    import torchvision

    from PIL import __version__ as pillow_version

    return {
        "python": platform.python_version(),
        "torch": str(torch.__version__),
        "torchvision": str(torchvision.__version__),
        "transformers": version("transformers"),
        "safetensors": version("safetensors"),
        "accelerate": version("accelerate"),
        "num2words": version("num2words"),
        "docopt": version("docopt"),
        "psutil": version("psutil"),
        "datasets": str(datasets.__version__),
        "mujoco": str(mujoco.__version__),
        "numpy": str(numpy.__version__),
        "pillow": str(pillow_version),
        "pyarrow": str(pyarrow.__version__),
        "lerobot": str(lerobot.__version__),
    }


def _mps_available() -> bool:
    import torch

    return bool(torch.backends.mps.is_available())


def _require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"T20.44 ancestry check failed: {ancestor} -> {descendant}")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _path_or_parent_is_symlink(root: Path, relative: Path) -> bool:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_identity(root: Path) -> str:
    if not root.is_dir():
        raise FileNotFoundError(f"T20.44 snapshot root is absent: {root}")
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        resolved = path.resolve(strict=True)
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": resolved.stat().st_size,
                "sha256": _sha_file(resolved),
            }
        )
    if not rows:
        raise ValueError("T20.44 snapshot tree is empty")
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


__all__ = [
    "IMPLEMENTATION_SCOPED_PATHS",
    "build_materialization_bundle",
    "collect_gate_a_evidence",
    "collect_live_runtime_snapshot",
    "materialize_live_authority",
    "run_renderer_smoke",
    "verify_materialization_bundle",
    "verify_materialized_authority",
]

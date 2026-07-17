"""Model-free renderer smoke and authority materialization for T20.43c."""

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
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (
    MUJOCO_SUPPORT_SITE_PACKAGES,
    STABLE_RUNNER_INTERPRETER,
)
from scenesmith.robot_lab.t20_43c_act_continuation import (
    AUTHORITY_PATHS,
    BRANCH,
    DECISION_PATH,
    OUTPUT_PATHS,
    OWNER_PATH,
    PERMIT_PATH,
    REQUEST_PATH,
    RUNTIME_PATH,
    SMOKE_MANIFEST_PATH,
    SMOKE_RECEIPT_PATH,
    SMOKE_ROOT,
    SMOKE_VIDEO_PATH,
    SOURCE_ATTEMPT_IDENTITY,
    SOURCE_CHECKPOINT_IDENTITY,
    SOURCE_FAILURE_IDENTITY,
    SOURCE_MODEL_FILE_SHA256,
    SOURCE_TRACE_FILE_SHA256,
    SOURCE_TRACE_IDENTITY,
    SOURCE_TRACE_PATH,
    build_central_authority,
    build_owner_grant,
    build_permit,
    build_renderer_smoke,
    build_runtime_preflight,
    load_continuation_sources,
    verify_permit,
    verify_renderer_smoke,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION_SCOPED_PATHS = (
    Path("scenesmith/robot_lab/t20_43c_act_continuation.py"),
    Path("scenesmith/robot_lab/t20_43c_act_continuation_materialization.py"),
    Path("scenesmith/robot_lab/t20_43c_act_continuation_runner.py"),
    Path("scripts/robot_lab/materialize_t20_43c_act_continuation.py"),
    Path("scripts/robot_lab/write_t20_43c_act_continuation_acceptance.py"),
    Path("scripts/robot_lab/run_t20_43c_act_continuation.py"),
    Path("scripts/robot_lab/render_rollout_mirror_v2.py"),
    Path("tests/unit/test_t20_43c_act_continuation.py"),
)


def run_renderer_smoke(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    load_continuation_sources(repo_root=root)
    if any(os.path.lexists(root / path) for path in (SMOKE_ROOT, SMOKE_RECEIPT_PATH)):
        raise FileExistsError("T20.43c renderer smoke output already exists")
    command = [
        STABLE_RUNNER_INTERPRETER.as_posix(),
        str(root / "scripts/robot_lab/render_rollout_mirror_v2.py"),
        "--trace",
        SOURCE_TRACE_PATH.as_posix(),
        "--output-mp4",
        SMOKE_VIDEO_PATH.as_posix(),
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
                f"{root / 'external/lerobot/.venv/lib/python3.12/site-packages'}:"
                f"{MUJOCO_SUPPORT_SITE_PACKAGES}"
            ),
        },
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "T20.43c actual-schema renderer smoke failed: "
            + completed.stderr.decode("utf-8", errors="replace")[-2000:]
        )
    video = root / SMOKE_VIDEO_PATH
    manifest_path = root / SMOKE_MANIFEST_PATH
    manifest = load_strict_json(manifest_path)
    verify_signed_payload(manifest, label="T20.43c renderer smoke manifest")
    if (
        not video.is_file()
        or video.is_symlink()
        or video.stat().st_size <= 0
        or manifest.get("trace_identity_sha256") != SOURCE_TRACE_IDENTITY
        or manifest.get("output_sha256") != _sha_file(video)
    ):
        raise ValueError("T20.43c renderer smoke evidence drifted")
    smoke = build_renderer_smoke(
        evidence={
            "renderer_v2_file_sha256": _sha_file(
                root / "scripts/robot_lab/render_rollout_mirror_v2.py"
            ),
            "legacy_renderer_file_sha256": _sha_file(
                root / "scripts/robot_lab/render_rollout_mirror.py"
            ),
            "video_file_sha256": _sha_file(video),
            "video_size_bytes": video.stat().st_size,
            "manifest_identity_sha256": manifest["identity_sha256"],
            "manifest_file_sha256": _sha_file(manifest_path),
            "runner_interpreter": STABLE_RUNNER_INTERPRETER.as_posix(),
        }
    )
    verify_renderer_smoke(smoke)
    if (
        load_continuation_sources(repo_root=root)["trace"]["identity_sha256"]
        != SOURCE_TRACE_IDENTITY
    ):
        raise ValueError("T20.43c renderer smoke source changed during execution")
    return smoke


def collect_runtime_snapshot(
    *, required_source_commit: str, smoke: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = load_continuation_sources(repo_root=root)
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    origin_head = _git(root, "rev-parse", f"refs/remotes/origin/{BRANCH}")
    if branch != BRANCH or head != required_source_commit or origin_head != head:
        raise ValueError("T20.43c source is not exact on origin")
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
    if scoped_dirty:
        raise ValueError("T20.43c reviewed implementation has dirty paths")
    if Path(sys.executable).resolve() != (root / STABLE_RUNNER_INTERPRETER).resolve():
        raise ValueError("T20.43c materializer interpreter drifted")
    output_state = {
        path.as_posix(): {
            "exists": os.path.lexists(root / path),
            "is_symlink": _path_or_parent_is_symlink(root, path),
        }
        for path in OUTPUT_PATHS
    }
    return {
        "source_commit": head,
        "branch": branch,
        "origin_contains_source_commit": True,
        "scoped_dirty_paths": scoped_dirty,
        "dependencies": _dependency_versions(),
        "mps_available": _mps_available(),
        "free_disk_bytes": shutil.disk_usage(root).free,
        "network_enabled": False,
        "source_attempt_identity_sha256": SOURCE_ATTEMPT_IDENTITY,
        "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
        "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
        "source_model_file_sha256": SOURCE_MODEL_FILE_SHA256,
        "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
        "source_trace_file_sha256": SOURCE_TRACE_FILE_SHA256,
        "source_partial_tree_identity_sha256": hashlib.sha256(
            _canonical(sources["failure"]["partial_run_tree"])
        ).hexdigest(),
        "output_path_state": output_state,
        "authority_artifacts_materialized": False,
        "continuation_marker_exists": False,
    }


def build_materialization_bundle(
    *,
    sources: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    smoke: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    owner = build_owner_grant(
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    request, decision = build_central_authority(
        sources=sources, smoke=smoke, owner=owner
    )
    runtime = build_runtime_preflight(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        snapshot=snapshot,
    )
    permit = build_permit(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )
    return {
        SMOKE_RECEIPT_PATH.as_posix(): smoke,
        OWNER_PATH.as_posix(): owner,
        REQUEST_PATH.as_posix(): request,
        DECISION_PATH.as_posix(): decision,
        RUNTIME_PATH.as_posix(): runtime,
        PERMIT_PATH.as_posix(): permit,
    }


def verify_materialization_bundle(
    bundle: dict[str, dict[str, Any]], *, sources: dict[str, Any]
) -> None:
    if list(bundle) != [path.as_posix() for path in AUTHORITY_PATHS]:
        raise ValueError("T20.43c authority bundle path/order drifted")
    smoke = bundle[SMOKE_RECEIPT_PATH.as_posix()]
    owner = bundle[OWNER_PATH.as_posix()]
    request = bundle[REQUEST_PATH.as_posix()]
    decision = bundle[DECISION_PATH.as_posix()]
    runtime = bundle[RUNTIME_PATH.as_posix()]
    permit = bundle[PERMIT_PATH.as_posix()]
    expected_request, expected_decision = build_central_authority(
        sources=sources, smoke=smoke, owner=owner
    )
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.43c central authority drifted")
    verify_permit(
        permit,
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )


def materialize_live_authority(
    *,
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_continuation_sources(repo_root=root)
    smoke = run_renderer_smoke(repo_root=root)
    snapshot = collect_runtime_snapshot(
        required_source_commit=required_source_commit, smoke=smoke, repo_root=root
    )
    bundle = build_materialization_bundle(
        sources=sources,
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
        smoke=smoke,
        snapshot=snapshot,
    )
    verify_materialization_bundle(bundle, sources=sources)
    _write_bundle_exclusively(bundle, repo_root=root)
    return bundle


def _write_bundle_exclusively(
    bundle: dict[str, dict[str, Any]], *, repo_root: Path
) -> None:
    for relative in AUTHORITY_PATHS:
        target = repo_root / relative
        if os.path.lexists(target) or _path_or_parent_is_symlink(repo_root, relative):
            raise FileExistsError(f"T20.43c authority target is unsafe: {relative}")
    for relative in AUTHORITY_PATHS:
        target = repo_root / relative
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


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


__all__ = [
    "IMPLEMENTATION_SCOPED_PATHS",
    "build_materialization_bundle",
    "collect_runtime_snapshot",
    "materialize_live_authority",
    "run_renderer_smoke",
    "verify_materialization_bundle",
]

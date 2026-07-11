"""Fail-closed executable identity for every SceneSmith LeRobot stage."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys

from pathlib import Path
from typing import Any, Literal


RUNTIME_CONFIG = Path("configurations/robot_lab/pi05_lerobot_runtime.json")
STAGES = ("collection", "training", "finalization", "inference", "lelab")


def load_runtime_config(*, repo_root: Path) -> dict[str, Any]:
    path = repo_root.resolve() / RUNTIME_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(payload, dict) or payload.get("schema_version") != "scenesmith.lerobot_runtime.v1":
        raise ValueError("Unsupported LeRobot runtime config")
    return payload


def build_stack_identity(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    config = load_runtime_config(repo_root=root)
    checkout = root / "external/lerobot"
    revision = _git(checkout, "rev-parse", "HEAD").strip()
    if revision != config["base_revision"]:
        raise ValueError("LeRobot checkout is not at the pinned base revision")

    patch_evidence = [_file_evidence(root / relative, root) for relative in config["patches"]]
    expected_patch = b"".join((root / item["path"]).read_bytes() for item in patch_evidence)
    actual_patch = subprocess.run(
        ["git", "diff", "--binary", "HEAD", "--"],
        cwd=checkout,
        check=True,
        capture_output=True,
    ).stdout
    if actual_patch != expected_patch:
        raise ValueError("LeRobot checkout diff does not match the tracked patch-set")

    environment = dict(config["critical_environment"])
    for name, expected in environment.items():
        actual = os.environ.get(name, expected)
        if actual != expected:
            raise ValueError(f"Critical LeRobot environment drifted: {name}")

    payload = {
        "schema_version": "scenesmith.lerobot_stack_identity.v1",
        "base_revision": revision,
        "source_root": config["source_root"],
        "patches": patch_evidence,
        "patch_set_sha256": hashlib.sha256(expected_patch).hexdigest(),
        "environment_lock": _file_evidence(root / config["environment_lock"], root),
        "critical_environment": environment,
        "processor_contract": config["processor_contract"],
        "roles": list(config["roles"]),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    payload["identity_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def activate_lerobot_stack(*, repo_root: Path, stage: str) -> dict[str, Any]:
    if stage not in STAGES:
        raise ValueError(f"Unsupported LeRobot stage: {stage}")
    identity = build_stack_identity(repo_root=repo_root)
    source = (repo_root.resolve() / identity["source_root"]).resolve()
    for name, module in tuple(sys.modules.items()):
        if name != "lerobot" and not name.startswith("lerobot."):
            continue
        module_path = getattr(module, "__file__", None)
        if module_path is not None and not Path(module_path).resolve().is_relative_to(source):
            raise RuntimeError(f"LeRobot was imported from outside the unified stack: {module_path}")
    source_text = str(source)
    sys.path[:] = [item for item in sys.path if item != source_text]
    sys.path.insert(0, source_text)
    return identity


def process_saved_sample(
    sample: dict[str, Any],
    *,
    repo_root: Path,
    stage: Literal["collection", "training", "inference"],
) -> dict[str, Any]:
    """Apply the shared deterministic SO-101 sample boundary used for parity proof."""

    identity = build_stack_identity(repo_root=repo_root)
    contract = identity["processor_contract"]
    names = contract["joint_names"]
    state = _six_finite(sample.get("observation_state"), "observation_state", len(names))
    action = _six_finite(sample.get("action"), "action", len(names))
    factor = 180.0 / math.pi
    width = int(contract["tensor_width"])
    padding = float(contract["padding_value"])
    state_tensor = [value * factor for value in state] + [padding] * (width - len(state))
    action_tensor = [value * factor for value in action] + [padding] * (width - len(action))
    return {
        "stage": stage,
        "stack_identity_sha256": identity["identity_sha256"],
        "joint_names": list(names),
        "observation_state_tensor": state_tensor,
        "action_tensor": action_tensor,
        "decoded_action_radians": [value / factor for value in action_tensor[: len(names)]],
    }


def _six_finite(value: Any, name: str, expected_length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != expected_length:
        raise ValueError(f"{name} must contain exactly {expected_length} values")
    output = [float(item) for item in value]
    if not all(math.isfinite(item) for item in output):
        raise ValueError(f"{name} must contain only finite values")
    return output


def _file_evidence(path: Path, root: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path.resolve().relative_to(root)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def _git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=path, check=True, capture_output=True, text=True
    ).stdout


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")

#!/usr/bin/env python3
"""Write or verify the strict-offline PI0.5 fixture tensor-parity artifact."""

from __future__ import annotations

import argparse
import json
import os
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.pi05_fixture_preprocessing import (
    build_pi05_fixture_model_ready_parity,
    execute_pi05_fixture_preprocessing,
    verify_pi05_fixture_model_ready_parity,
)


DEFAULT_CALIBRATION = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
DEFAULT_HF_CACHE = Path.home() / ".cache/huggingface/hub"
DEFAULT_OUTPUT = Path(
    "configurations/robot_lab/pi05_fixture_model_ready_tensor_parity.json"
)
PINNED_PYTHON = REPO_ROOT / "external/leLab/.venv/bin/python"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--print-runtime-identity", action="store_true")
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--hf-cache", type=Path, default=DEFAULT_HF_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _require_pinned_python()
    identity = activate_lerobot_stack(repo_root=REPO_ROOT, stage="lelab")
    source = str((REPO_ROOT / identity["source_root"]).resolve())
    if sys.path[0] != source:
        sys.path.insert(0, source)
    os.environ["SCENESMITH_LEROBOT_STACK_IDENTITY"] = identity["identity_sha256"]

    calibration = _resolve_exact_file(
        args.calibration,
        expected=DEFAULT_CALIBRATION,
        label="follower calibration",
    )
    cache = _resolve_exact_directory(
        args.hf_cache,
        expected=DEFAULT_HF_CACHE,
        label="Hugging Face cache",
    )
    output = _resolve_output(args.output)
    runtime = execute_pi05_fixture_preprocessing(
        repo_root=REPO_ROOT,
        hf_cache_root=cache,
        calibration_path=calibration,
    )
    if args.print_runtime_identity:
        print(
            json.dumps(
                {
                    "schema_version": runtime["schema_version"],
                    "runtime_identity_sha256": runtime["identity_sha256"],
                    "model_instantiated": runtime["model_instantiated"],
                    "model_weights_read": runtime["model_weights_read"],
                    "policy_inference_run": runtime["policy_inference_run"],
                    "network_accessed": runtime["network_accessed"],
                    "hardware_accessed": runtime["hardware_accessed"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    payload = build_pi05_fixture_model_ready_parity(
        runtime,
        repo_root=REPO_ROOT,
        hf_cache_root=cache,
        calibration_path=calibration,
    )
    if args.verify:
        stored = load_strict_json(output)
        if stored != payload:
            raise ValueError("Checked PI0.5 fixture tensor-parity artifact drifted")
        verify_pi05_fixture_model_ready_parity(
            stored,
            repo_root=REPO_ROOT,
            hf_cache_root=cache,
            calibration_path=calibration,
        )
        status = "verified"
    else:
        if output.exists() or output.is_symlink():
            raise ValueError("PI0.5 fixture tensor-parity artifact exists; use --verify")
        dump_canonical_json(output, payload)
        stored = load_strict_json(output)
        if stored != payload:
            raise ValueError("Stored PI0.5 fixture tensor-parity bytes drifted")
        verify_pi05_fixture_model_ready_parity(
            stored,
            repo_root=REPO_ROOT,
            hf_cache_root=cache,
            calibration_path=calibration,
        )
        status = "written"

    print(
        json.dumps(
            {
                "status": status,
                "schema_version": payload["schema_version"],
                "identity_sha256": payload["identity_sha256"],
                "runtime_identity_sha256": runtime["identity_sha256"],
                "capabilities": payload["local_capabilities"],
                "model_instantiated": payload["model_instantiated"],
                "model_weights_read": payload["model_weights_read"],
                "policy_inference_run": payload["policy_inference_run"],
                "hardware_accessed": payload["hardware_accessed"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _require_pinned_python() -> None:
    if Path(sys.executable).resolve() != PINNED_PYTHON.resolve():
        raise ValueError(
            "PI0.5 fixture execution requires external/leLab/.venv/bin/python"
        )


def _resolve_exact_file(path: Path, *, expected: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved != expected.resolve() or not resolved.is_file():
        raise ValueError(f"Pinned {label} path is missing or changed")
    return resolved


def _resolve_exact_directory(path: Path, *, expected: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved != expected.resolve() or not resolved.is_dir():
        raise ValueError(f"Pinned {label} path is missing or changed")
    return resolved


def _resolve_output(path: Path) -> Path:
    unresolved = path if path.is_absolute() else REPO_ROOT / path
    expected = REPO_ROOT / DEFAULT_OUTPUT
    if unresolved.absolute() != expected.absolute():
        raise ValueError(f"Output path is not canonical: {DEFAULT_OUTPUT}")
    current = REPO_ROOT.resolve()
    for part in DEFAULT_OUTPUT.parent.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("PI0.5 fixture output parent is aliased")
    if not current.is_dir():
        raise ValueError("PI0.5 fixture output parent is missing")
    return unresolved


if __name__ == "__main__":
    raise SystemExit(main())

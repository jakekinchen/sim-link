#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def sign(payload: dict) -> dict:
    result = copy.deepcopy(payload)
    result.pop("identity_sha256", None)
    result["identity_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    expected = json.loads(args.preflight.read_text())

    source_archive = root / "inputs/sim-link-471b758.tar.gz"
    if sha(source_archive) != expected["source_archive_sha256"]:
        raise SystemExit("source archive hash mismatch")

    model_root = root / "inputs/pi05_base"
    for row in expected["model"]["files"]:
        path = model_root / row["path"]
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or sha(path) != row["sha256"]:
            raise SystemExit(f"model byte mismatch: {row['path']}")

    tokenizer_root = root / "huggingface/hub" / f"models--google--paligemma-3b-pt-224/snapshots/{expected['tokenizer']['revision']}"
    for row in expected["tokenizer"]["files"]:
        path = tokenizer_root / row["path"]
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or sha(path) != row["sha256"]:
            raise SystemExit(f"tokenizer byte mismatch: {row['path']}")

    dataset_root = root / "inputs/r0_dataset"
    manifest_path = root / "inputs/lerobot_dataset_manifest.json"
    w2_receipt_path = root / "inputs/W2_RUN_RECEIPT.json"
    if sha(w2_receipt_path) != expected["dataset"]["w2_run_receipt_file_sha256"]:
        raise SystemExit("W2 run receipt file hash mismatch")
    w2_receipt = json.loads(w2_receipt_path.read_text())
    if w2_receipt.get("identity_sha256") != expected["dataset"]["w2_run_receipt_identity_sha256"]:
        raise SystemExit("W2 run receipt identity mismatch")
    for key in ("mixture_identity_sha256", "mixture_file_sha256", "statistics_identity_sha256", "statistics_file_sha256"):
        if w2_receipt["observed"].get(key) != expected["dataset"][key]:
            raise SystemExit(f"W2 R0 binding mismatch: {key}")
    if sha(manifest_path) != expected["dataset"]["manifest_file_sha256"]:
        raise SystemExit("R0 manifest file hash mismatch")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("identity_sha256") != expected["dataset"]["manifest_identity_sha256"]:
        raise SystemExit("R0 manifest identity mismatch")
    info = json.loads((dataset_root / "meta/info.json").read_text())
    if info.get("total_episodes") != 129 or info.get("total_frames") != 31366:
        raise SystemExit("R0 cardinality mismatch")

    tree = expected["dataset"]["raw_byte_tree"]
    dataset_bytes = 0
    for row in tree["files"]:
        path = dataset_root / row["path"]
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or sha(path) != row["sha256"]:
            raise SystemExit(f"R0 dataset byte mismatch: {row['path']}")
        dataset_bytes += row["size_bytes"]
    if len(tree["files"]) != tree["file_count"] or dataset_bytes != tree["size_bytes"]:
        raise SystemExit("R0 dataset tree cardinality mismatch")
    expected_paths = sorted(row["path"] for row in tree["files"])
    observed_paths = sorted(str(path.relative_to(dataset_root)) for path in dataset_root.rglob("*") if path.is_file())
    if observed_paths != expected_paths:
        raise SystemExit("R0 dataset file set mismatch")
    observed_tree = {"file_count": tree["file_count"], "files": tree["files"], "size_bytes": dataset_bytes}
    tree_identity = hashlib.sha256(canonical_bytes(observed_tree)).hexdigest()
    if tree_identity != expected["dataset"]["dataset_tree_identity_sha256"]:
        raise SystemExit("R0 dataset tree identity mismatch")

    patch = root / "sim-link/scripts/robot_lab/patches/pi05_gripper_loss_weight.patch"
    lock = root / "deps/lerobot/uv.lock"
    pyproject = root / "deps/lerobot/pyproject.toml"
    mjcf = root / "deps/SO-ARM100/Simulation/SO101/so101_new_calib.xml"
    checks = {
        "lerobot_patch_sha256": sha(patch),
        "lerobot_uv_lock_sha256": sha(lock),
        "lerobot_pyproject_sha256": sha(pyproject),
        "active_mjcf_sha256": sha(mjcf),
    }
    for key, observed in checks.items():
        if observed != expected["stack"][key]:
            raise SystemExit(f"stack mismatch: {key}")

    training_output = root / "outputs/training"
    evaluation_output = root / "outputs/evaluations"
    if training_output.exists() or evaluation_output.exists():
        raise SystemExit("output path is not empty/absent")

    versions = {name: importlib.metadata.version(name) for name in [
        "lerobot", "torch", "torchvision", "transformers", "datasets", "numpy", "Pillow", "pyarrow", "mujoco", "peft"
    ]}
    gpu = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], text=True
    ).strip()
    memory_matches = re.findall(r"([0-9]+)\s*MiB", gpu)
    if "A100" not in gpu or len(memory_matches) != 1 or int(memory_matches[0]) < 80000:
        raise SystemExit(f"unexpected GPU: {gpu}")

    receipt = sign({
        "schema_version": "sim_link.f1_pi05_remote_preflight.v1",
        "checked_at": datetime.now().astimezone().isoformat(),
        "status": "pass",
        "source_commit": expected["source_commit"],
        "dataset_manifest_identity_sha256": manifest["identity_sha256"],
        "dataset_episode_count": info["total_episodes"],
        "dataset_frame_count": info["total_frames"],
        "dataset_file_count": tree["file_count"],
        "dataset_size_bytes": dataset_bytes,
        "dataset_tree_identity_sha256": tree_identity,
        "model_revision": expected["model"]["revision"],
        "model_weights_sha256": expected["model"]["files"][1]["sha256"],
        "stack_checks": checks,
        "package_versions": versions,
        "gpu": gpu,
        "training_output_absent": True,
        "evaluation_output_absent": True,
        "output_paths_verified_empty_before_model_action": True,
        "hardware_accessed": False,
        "camera_accessed": False,
        "serial_accessed": False,
        "physical_motion": False,
    })
    out = root / "receipts/REMOTE_PREFLIGHT.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(receipt["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

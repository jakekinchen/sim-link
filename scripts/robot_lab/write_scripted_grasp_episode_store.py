#!/usr/bin/env python3
"""Write or verify immutable T17.5b scripted-grasp episode artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.experience_compiler import (  # noqa: E402
    OUTPUT_NAMES as COMPILER_OUTPUT_NAMES,
    verify_compilation,
)
from scenesmith.robot_lab.experience_window_index import (  # noqa: E402
    OUTPUT_NAMES as WINDOW_OUTPUT_NAMES,
    compile_window_index,
    verify_window_index,
    write_window_index,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    COMPILE_OUTPUT_DIR,
    MANIFEST_PATH,
    WINDOW_OUTPUT_DIR,
    compile_episode_store,
    default_store_root,
    generate_store,
    verify_episode_store,
)


STORE_ROOT = default_store_root()


def _all_outputs_exist() -> bool:
    return all((COMPILE_OUTPUT_DIR / name).is_file() for name in COMPILER_OUTPUT_NAMES) and all(
        (WINDOW_OUTPUT_DIR / name).is_file() for name in WINDOW_OUTPUT_NAMES
    )


def _manifest_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compare_outputs(expected_dir: Path, stored_dir: Path, names: tuple[str, ...]) -> None:
    for name in names:
        if (expected_dir / name).read_bytes() != (stored_dir / name).read_bytes():
            raise ValueError(f"T17.5b compiler output drifted: {name}")


def _write() -> dict:
    if MANIFEST_PATH.exists() or _all_outputs_exist():
        raise ValueError("T17.5b artifacts already exist; use --verify")
    if any((COMPILE_OUTPUT_DIR / name).exists() for name in COMPILER_OUTPUT_NAMES) or any(
        (WINDOW_OUTPUT_DIR / name).exists() for name in WINDOW_OUTPUT_NAMES
    ):
        raise ValueError("T17.5b derived output is incomplete; refuse to overwrite")

    manifest = generate_store(STORE_ROOT)
    verify_episode_store(manifest, STORE_ROOT)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPILE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    WINDOW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="scenesmith-t17-5b-", dir=MANIFEST_PATH.parent
    ) as directory:
        temporary = Path(directory)
        temporary_manifest = temporary / MANIFEST_PATH.name
        temporary_output = temporary / "compile"
        dump_canonical_json(temporary_manifest, manifest)
        compile_episode_store(
            manifest,
            STORE_ROOT,
            temporary_output,
            manifest_file_sha256=_manifest_file_sha256(temporary_manifest),
        )
        temporary_window = temporary / "window"
        write_window_index(compile_window_index(temporary_output), temporary_window)
        verify_window_index(temporary_window, temporary_output)
        os.replace(temporary_manifest, MANIFEST_PATH)
        for name in COMPILER_OUTPUT_NAMES:
            os.replace(temporary_output / name, COMPILE_OUTPUT_DIR / name)
        for name in WINDOW_OUTPUT_NAMES:
            os.replace(temporary_window / name, WINDOW_OUTPUT_DIR / name)
    stored = load_strict_json(MANIFEST_PATH)
    verify_episode_store(stored, STORE_ROOT)
    verify_compilation(COMPILE_OUTPUT_DIR)
    verify_window_index(WINDOW_OUTPUT_DIR, COMPILE_OUTPUT_DIR)
    return stored


def _verify() -> dict:
    if not MANIFEST_PATH.is_file() or not _all_outputs_exist():
        raise ValueError("T17.5b episode artifacts are incomplete")
    stored = load_strict_json(MANIFEST_PATH)
    verify_episode_store(stored, STORE_ROOT)
    with tempfile.TemporaryDirectory(prefix="scenesmith-t17-5b-verify-") as directory:
        temporary = Path(directory)
        regenerated = generate_store(temporary / "raw_store")
        if canonical_json_bytes(regenerated) != canonical_json_bytes(stored):
            raise ValueError("T17.5b signed episode-store manifest drifted")
        temporary_output = temporary / "compile"
        compile_episode_store(
            regenerated,
            temporary / "raw_store",
            temporary_output,
            manifest_file_sha256=_manifest_file_sha256(MANIFEST_PATH),
        )
        temporary_window = temporary / "window"
        write_window_index(compile_window_index(temporary_output), temporary_window)
        verify_window_index(temporary_window, temporary_output)
        _compare_outputs(temporary_output, COMPILE_OUTPUT_DIR, COMPILER_OUTPUT_NAMES)
        _compare_outputs(temporary_window, WINDOW_OUTPUT_DIR, WINDOW_OUTPUT_NAMES)
    verify_compilation(COMPILE_OUTPUT_DIR)
    verify_window_index(WINDOW_OUTPUT_DIR, COMPILE_OUTPUT_DIR)
    return stored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument(
        "--rewrite",
        action="store_true",
        help="Rejected: raw episode artifacts are append-only and immutable.",
    )
    args = parser.parse_args()
    if args.rewrite:
        raise ValueError("T17.5b raw episode artifacts are immutable; write a new task view")
    manifest = _verify() if args.verify else _write()
    status = "verified" if args.verify else "written"
    print(
        json.dumps(
            {
                "status": status,
                "schema_version": manifest["schema_version"],
                "configured_episode_count": manifest["configured_episode_count"],
                "realized_episode_count": manifest["realized_episode_count"],
                "runtime_failure_count": manifest["runtime_failure_count"],
                "seed_zero_strict_success": next(
                    entry["outcome"]["strict_success"]
                    for entry in manifest["episodes"]
                    if entry["seed"] == 0
                ),
                "training_eligible": manifest["training_eligible"],
                "simulation_training_ready": manifest["simulation_training_ready"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

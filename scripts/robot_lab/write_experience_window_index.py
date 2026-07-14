#!/usr/bin/env python3
"""Write or verify deterministic T17.5 unpadded action-window outputs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.experience_window_index import (  # noqa: E402
    OUTPUT_NAMES,
    compile_window_index,
    verify_window_index,
    write_window_index,
)


SOURCE_DIR = REPO_ROOT / "configurations/robot_lab/t17_4_compile"
OUTPUT_DIR = REPO_ROOT / "configurations/robot_lab/t17_5_window_index"


def _all_outputs_exist() -> bool:
    return all((OUTPUT_DIR / name).is_file() for name in OUTPUT_NAMES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument(
        "--rewrite",
        action="store_true",
        help="Regenerate the tracked outputs after an intentional source dependency change.",
    )
    args = parser.parse_args()

    if args.verify:
        if not _all_outputs_exist():
            raise ValueError("T17.5 window-index outputs are incomplete")
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-") as temp_dir:
            result = compile_window_index(SOURCE_DIR)
            write_window_index(result, Path(temp_dir))
            for name in OUTPUT_NAMES:
                if (Path(temp_dir) / name).read_bytes() != (OUTPUT_DIR / name).read_bytes():
                    raise ValueError(f"T17.5 window-index output drifted: {name}")
        verify_window_index(OUTPUT_DIR, SOURCE_DIR)
        manifest = json.loads((OUTPUT_DIR / "window_manifest.json").read_text())
        status = "verified"
    elif args.rewrite:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="scenesmith-window-", dir=OUTPUT_DIR.parent
        ) as temp_dir:
            temporary_output = Path(temp_dir)
            result = compile_window_index(SOURCE_DIR)
            write_window_index(result, temporary_output)
            verify_window_index(temporary_output, SOURCE_DIR)
            for name in OUTPUT_NAMES:
                os.replace(temporary_output / name, OUTPUT_DIR / name)
        verify_window_index(OUTPUT_DIR, SOURCE_DIR)
        manifest = json.loads((OUTPUT_DIR / "window_manifest.json").read_text())
        status = "rewritten"
    else:
        if any((OUTPUT_DIR / name).exists() for name in OUTPUT_NAMES):
            raise ValueError("T17.5 window-index output exists; use --verify")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        result = compile_window_index(SOURCE_DIR)
        write_window_index(result, OUTPUT_DIR)
        verify_window_index(OUTPUT_DIR, SOURCE_DIR)
        manifest = json.loads((OUTPUT_DIR / "window_manifest.json").read_text())
        status = "written"

    print(
        json.dumps(
            {
                "status": status,
                "schema_version": manifest["schema_version"],
                "source_compiler_manifest_sha256": manifest[
                    "source_compiler_manifest_sha256"
                ],
                "source_segment_count": manifest["source_segment_count"],
                "horizons": manifest["horizons"],
                "window_count": manifest["window_count"],
                "window_count_by_horizon": manifest["window_count_by_horizon"],
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

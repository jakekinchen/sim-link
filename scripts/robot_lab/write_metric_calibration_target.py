#!/usr/bin/env python3
"""Write or verify the T19.2 metric checkerboard PDF and signed spec."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.metric_calibration_target import (
    PDF_PATH,
    SPEC_PATH,
    build_metric_checkerboard_pdf_bytes,
    build_metric_checkerboard_spec,
    verify_metric_checkerboard_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    pdf_path = REPO_ROOT / PDF_PATH
    spec_path = REPO_ROOT / SPEC_PATH
    if args.verify:
        spec = load_strict_json(spec_path)
        verify_metric_checkerboard_artifacts(spec, repo_root=REPO_ROOT)
        status = "verified"
    else:
        if pdf_path.exists() or spec_path.exists():
            raise ValueError("Metric target artifacts exist; use --verify")
        pdf_bytes = build_metric_checkerboard_pdf_bytes()
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(pdf_bytes)
        spec = build_metric_checkerboard_spec(repo_root=REPO_ROOT)
        dump_canonical_json(spec_path, spec)
        verify_metric_checkerboard_artifacts(spec, repo_root=REPO_ROOT)
        status = "written"
    print(json.dumps({"status": status, "spec_identity_sha256": spec["identity_sha256"], "pdf_sha256": spec["pdf"]["sha256"], "square_size_mm": spec["checkerboard"]["square_size_mm"], "inner_corners": [spec["checkerboard"]["inner_corners_columns"], spec["checkerboard"]["inner_corners_rows"]]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

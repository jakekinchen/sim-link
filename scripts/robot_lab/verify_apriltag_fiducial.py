#!/usr/bin/env python3
"""Detect the expected AprilTag in a rendered SceneSmith camera image."""

from __future__ import annotations

import argparse
import json

from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--family", default="tag36h11")
    parser.add_argument("--tag-id", type=int, default=0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    try:
        import numpy as np
        from PIL import Image
        from robotpy_apriltag import AprilTagDetector
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Install detector proof dependencies with: "
            "python -m pip install robotpy-apriltag pillow numpy"
        ) from exc

    pixels = np.asarray(Image.open(args.image).convert("L"), dtype=np.uint8)
    detector = AprilTagDetector()
    if not detector.addFamily(args.family):
        raise SystemExit(f"AprilTag detector does not support family {args.family!r}")
    config = detector.getConfig()
    config.quadDecimate = 1.0
    detector.setConfig(config)
    detections = detector.detect(pixels)
    rows = [
        {
            "family": item.getFamily(),
            "tag_id": item.getId(),
            "hamming": item.getHamming(),
            "decision_margin": round(float(item.getDecisionMargin()), 6),
            "center_px": [round(float(item.getCenter().x), 3), round(float(item.getCenter().y), 3)],
        }
        for item in detections
    ]
    expected = any(
        item["family"] == args.family and item["tag_id"] == args.tag_id
        for item in rows
    )
    report = {
        "schema_version": "scenesmith.apriltag_detection_proof.v1",
        "status": "pass" if expected else "fail",
        "image": str(args.image),
        "image_size": [int(pixels.shape[1]), int(pixels.shape[0])],
        "expected": {"family": args.family, "tag_id": args.tag_id},
        "detector": {"quad_decimate": 1.0},
        "detections": rows,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())

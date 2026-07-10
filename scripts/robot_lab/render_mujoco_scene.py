#!/usr/bin/env python3
"""Render a generated SceneSmith robot-lab MuJoCo scene to PNG."""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, required=True, help="Generated MuJoCo XML.")
    parser.add_argument(
        "--camera",
        default="free_side",
        help="MuJoCo camera name, or free_side for a generated overview camera.",
    )
    parser.add_argument("--output-png", type=Path, required=True, help="PNG output path.")
    parser.add_argument("--output-json", type=Path, help="Optional render proof JSON path.")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=800)
    args = parser.parse_args()

    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "mujoco is not installed in this Python environment; run from .mujoco_venv"
        ) from exc

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    for _ in range(240):
        mujoco.mj_step(model, data)

    renderer = mujoco.Renderer(model, height=args.height, width=args.width)
    if args.camera == "free_side":
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = [0.18, 0.0, 0.34]
        camera.distance = 1.0
        camera.azimuth = -125
        camera.elevation = -23
        renderer.update_scene(data, camera=camera)
    else:
        renderer.update_scene(data, camera=args.camera)
    pixels = renderer.render()
    renderer.close()

    args.output_png.parent.mkdir(parents=True, exist_ok=True)
    _write_png(args.output_png, pixels)

    geom_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_GEOM, model.ngeom)
    mesh_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_MESH, model.nmesh)
    camera_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_CAMERA, model.ncam)
    summary = {
        "status": "pass",
        "xml": str(args.xml),
        "camera": args.camera,
        "camera_names": camera_names,
        "output_png": str(args.output_png),
        "width": args.width,
        "height": args.height,
        "ngeom": int(model.ngeom),
        "nmesh": int(model.nmesh),
        "mesh_names": mesh_names,
        "real_so101_meshes_present": all(
            name in mesh_names
            for name in [
                "base_so101_v2",
                "upper_arm_so101_v1",
                "under_arm_so101_v1",
                "wrist_roll_follower_so101_v1",
                "moving_jaw_so101_v1",
            ]
        ),
        "requested_camera_exists": args.camera == "free_side" or args.camera in camera_names,
        "sample_geom_names": geom_names[:40],
    }
    summary["status"] = (
        "pass"
        if summary["real_so101_meshes_present"] and summary["requested_camera_exists"]
        else "fail"
    )
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


def _object_names(mujoco, model, obj_type, count: int) -> list[str]:
    return [
        name
        for index in range(int(count))
        if (name := mujoco.mj_id2name(model, obj_type, index))
    ]


def _write_png(path: Path, rgb) -> None:
    height, width, channels = rgb.shape
    if channels != 3:
        raise ValueError(f"Expected RGB pixels, got shape {rgb.shape}")
    raw_rows = []
    for row in rgb:
        raw_rows.append(b"\x00" + row.tobytes())
    payload = zlib.compress(b"".join(raw_rows), level=9)
    png = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _chunk(b"IDAT", payload),
            _chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png)


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


if __name__ == "__main__":
    raise SystemExit(main())

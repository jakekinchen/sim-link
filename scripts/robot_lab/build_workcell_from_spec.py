#!/usr/bin/env python3
"""Build a declared workcell arrangement into a MuJoCo scene with previews.

Front door for "specify a simulation arrangement and it builds it": one
compact JSON spec (cubes, trays, task prompt) becomes a compiled MuJoCo
workcell under `outputs/robot_lab/workcells/<scene_id>/` with a physics
settle-stability check, rendered side/overhead preview PNGs, and a hash
manifest.

The result is a labelled simulation fixture only. It grants no metric,
calibration, training, transfer, or promotion authority, and it opens no
camera, robot, or network path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib

from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import load_strict_json  # noqa: E402
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (  # noqa: E402
    apply_explicit_pad_proxy_contact_model,
)
from scenesmith.robot_lab.mujoco_export import (  # noqa: E402
    prepare_mujoco_so101_assets,
    render_mujoco_xml,
)
from scenesmith.robot_lab.workcell_spec_intake import (  # noqa: E402
    scene_from_arrangement_spec,
)

PREVIEW_CAMERAS = ("cam0_side", "cam1_overhead")
PREVIEW_SIZE = 768
SETTLE_STEPS = 240
STABILITY_TOLERANCE_M = 0.005


def _write_png(path: Path, pixels: np.ndarray) -> None:
    height, width, _ = pixels.shape
    raw = b"".join(
        b"\x00" + pixels[row].astype(np.uint8).tobytes() for row in range(height)
    )
    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True, help="Arrangement JSON.")
    parser.add_argument("--output-root", type=Path, default=None)
    args = parser.parse_args()

    import mujoco

    payload = load_strict_json(args.spec)
    scene = scene_from_arrangement_spec(payload)
    output = args.output_root or (
        REPO_ROOT / "outputs/robot_lab/workcells" / scene.scene_id
    )
    output.mkdir(parents=True, exist_ok=True)

    robot_xml = prepare_mujoco_so101_assets(output, scene.robot.base_position_m)
    apply_explicit_pad_proxy_contact_model(robot_xml)
    scene_xml = output / "scene.xml"
    scene_xml.write_text(render_mujoco_xml(scene), encoding="utf-8")

    model = mujoco.MjModel.from_xml_path(str(scene_xml))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    cube_bodies = {}
    for cube in scene.cubes:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, cube.name)
        if body_id < 0:
            raise SystemExit(f"Cube body {cube.name!r} missing from compiled scene")
        cube_bodies[cube.name] = body_id
    initial = {name: data.xpos[body].copy() for name, body in cube_bodies.items()}
    for _ in range(SETTLE_STEPS):
        mujoco.mj_step(model, data)
    stability = {}
    for name, body in cube_bodies.items():
        displacement = float(np.linalg.norm(data.xpos[body] - initial[name]))
        stability[name] = {
            "settle_displacement_m": displacement,
            "stable": displacement <= STABILITY_TOLERANCE_M,
        }

    model.vis.global_.offwidth = max(model.vis.global_.offwidth, PREVIEW_SIZE)
    model.vis.global_.offheight = max(model.vis.global_.offheight, PREVIEW_SIZE)
    renderer = mujoco.Renderer(model, height=PREVIEW_SIZE, width=PREVIEW_SIZE)
    previews = {}
    for camera in PREVIEW_CAMERAS:
        if mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera) < 0:
            continue
        renderer.update_scene(data, camera=camera)
        preview_path = output / f"preview_{camera}.png"
        _write_png(preview_path, renderer.render())
        previews[camera] = str(preview_path)
    renderer.close()

    manifest = {
        "schema_version": "scenesmith.workcell_build_manifest.v1",
        "authority": "labelled simulation fixture only; no metric, training, or promotion authority",
        "spec_path": str(args.spec),
        "spec_sha256": hashlib.sha256(args.spec.read_bytes()).hexdigest(),
        "scene_id": scene.scene_id,
        "task_prompt": scene.policy.task,
        "scene_xml": str(scene_xml),
        "scene_xml_sha256": hashlib.sha256(scene_xml.read_bytes()).hexdigest(),
        "cube_count": len(scene.cubes),
        "tray_count": len(scene.trays),
        "settle_steps": SETTLE_STEPS,
        "stability_tolerance_m": STABILITY_TOLERANCE_M,
        "cube_stability": stability,
        "all_cubes_stable": all(entry["stable"] for entry in stability.values()),
        "previews": previews,
    }
    manifest_path = output / "build_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "scene_id": scene.scene_id,
                "scene_xml": str(scene_xml),
                "all_cubes_stable": manifest["all_cubes_stable"],
                "previews": list(previews.values()),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

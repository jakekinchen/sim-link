#!/usr/bin/env python3
"""Render a signed closed-loop trace as a side-by-side policy/expert MP4.

Kinematic playback of signed T20.32 or T20.36 complete-trace artifacts:
each frame poses the deterministic anchor-grasp scene at the recorded
candidate joint positions and anchor position, renders a diagnostic side view
plus the scene's top camera, and tiles them beside the exact recorded expert
top-camera observation for the same frame index. Frames are piped to ffmpeg
as one MP4 so a human can watch what the policy actually did next to what the
expert actually saw.

This is diagnostic visualization only. It re-renders recorded evidence,
invents no dynamics (anchor orientation is held at its initial value), runs
no policy, optimizer, or physics stepping, touches no hardware or authority
state, and writes only under `outputs/robot_lab/rollout_mirror/`.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import subprocess
import sys
import tempfile

from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.experience_records import JOINT_NAMES  # noqa: E402
from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (  # noqa: E402
    apply_explicit_pad_proxy_contact_model,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import (  # noqa: E402
    OBJECT_ID,
    _bind_anchor_geometry,
    _scene,
)
from scenesmith.robot_lab.mujoco_export import (  # noqa: E402
    prepare_mujoco_so101_assets,
    render_mujoco_xml,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    BASE_ANCHOR_POSITION_M,
    EPISODE_SPECS,
    default_store_root,
)
from scenesmith.robot_lab.t20_32_closed_loop_divergence import (  # noqa: E402
    verify_trace_payload as verify_t20_32_trace,
    verify_threshold_contract,
)
from scenesmith.robot_lab.t20_36_bounded_corrected_coverage import (  # noqa: E402
    THRESHOLD_PATH,
    TRACE_SCHEMA_VERSION as T20_36_TRACE_SCHEMA_VERSION,
    verify_trace as verify_t20_36_trace,
)

PANEL_SIZE = 512
TEXT_BAR_HEIGHT = 56
CAPTION_HEIGHT = 28
SIDE_CAMERA = "cam0_side"
OVERHEAD_CAMERA = "cam1_overhead"


def _load_trace(path: Path) -> dict:
    payload = load_strict_json(path)
    verify_signed_payload(payload, label="rollout mirror source trace")
    threshold = load_strict_json(REPO_ROOT / THRESHOLD_PATH)
    verify_threshold_contract(threshold)
    schema = payload.get("schema_version")
    if schema == "scenesmith.t20_32_closed_loop_trace.v1":
        verify_t20_32_trace(payload, threshold=threshold)
    elif schema == T20_36_TRACE_SCHEMA_VERSION:
        verify_t20_36_trace(payload, threshold=threshold)
    else:
        raise SystemExit(f"Unsupported trace schema: {payload.get('schema_version')}")
    return payload


def _source_episode_frames(seed: int) -> list[dict]:
    store = default_store_root()
    for candidate in sorted(store.glob("*.json")):
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        spec = payload.get("episode_spec", {})
        if spec.get("seed") == seed:
            frames = sorted(payload["frames"], key=lambda f: f["frame_index"])
            return frames
    raise SystemExit(f"No scripted source episode with seed {seed} in {store}")


def _decode_observation_png(frame: dict, view: str):
    from PIL import Image

    record = frame["observations"][view]
    raw = base64.b64decode(record["png_base64"])
    return Image.open(io.BytesIO(raw)).convert("RGB")


def _initial_anchor_position(seed: int) -> tuple[float, float, float]:
    spec = next((item for item in EPISODE_SPECS if item["seed"] == seed), None)
    if spec is None:
        raise SystemExit(f"Seed {seed} is not in the fixed episode design")
    offset_x, offset_y = spec["planar_offset_m"]
    return (
        BASE_ANCHOR_POSITION_M[0] + offset_x,
        BASE_ANCHOR_POSITION_M[1] + offset_y,
        BASE_ANCHOR_POSITION_M[2],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True, help="Signed trace JSON.")
    parser.add_argument(
        "--output-mp4",
        type=Path,
        default=None,
        help="Output MP4 (default outputs/robot_lab/rollout_mirror/<trace stem>.mp4).",
    )
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()

    import mujoco
    from PIL import Image, ImageDraw

    trace = _load_trace(args.trace)
    rows = sorted(trace["comparisons"], key=lambda r: r["frame_index"])
    if args.max_frames is not None:
        rows = rows[: args.max_frames]
    seed = int(trace["seed"])
    adapter = trace.get("adapter_id", "candidate")
    source_frames = _source_episode_frames(seed)

    output = args.output_mp4 or (
        REPO_ROOT / "outputs/robot_lab/rollout_mirror" / f"{args.trace.stem}.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="scenesmith-rollout-mirror-") as directory:
        root = Path(directory)
        scene = _scene(initial_position_m=_initial_anchor_position(seed))
        robot_xml = prepare_mujoco_so101_assets(root, scene.robot.base_position_m)
        apply_explicit_pad_proxy_contact_model(robot_xml)
        scene_xml = root / "scene.xml"
        scene_xml.write_text(render_mujoco_xml(scene), encoding="utf-8")
        _bind_anchor_geometry(scene_xml)

        model = mujoco.MjModel.from_xml_path(str(scene_xml))
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)

        joint_addresses = []
        for name in JOINT_NAMES:
            joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
            if joint_id < 0:
                raise SystemExit(f"Robot joint {name!r} missing from compiled scene")
            joint_addresses.append(int(model.jnt_qposadr[joint_id]))

        anchor_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, OBJECT_ID)
        if anchor_body < 0:
            raise SystemExit(f"Anchor body {OBJECT_ID!r} missing from compiled scene")
        anchor_joint = int(model.body_jntadr[anchor_body])
        anchor_qpos = int(model.jnt_qposadr[anchor_joint])
        anchor_quat = np.array(data.qpos[anchor_qpos + 3 : anchor_qpos + 7])

        policy_cameras = [
            name
            for name in (SIDE_CAMERA, OVERHEAD_CAMERA)
            if mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, name) >= 0
        ]
        if not policy_cameras:
            raise SystemExit("Scene exposes neither side nor overhead camera")
        model.vis.global_.offwidth = max(model.vis.global_.offwidth, PANEL_SIZE)
        model.vis.global_.offheight = max(model.vis.global_.offheight, PANEL_SIZE)
        renderer = mujoco.Renderer(model, height=PANEL_SIZE, width=PANEL_SIZE)

        panels = len(policy_cameras) + 1
        frame_width = PANEL_SIZE * panels
        frame_height = TEXT_BAR_HEIGHT + PANEL_SIZE + CAPTION_HEIGHT
        command = [
            args.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pixel_format",
            "rgb24",
            "-video_size",
            f"{frame_width}x{frame_height}",
            "-framerate",
            str(args.fps),
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
        encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
        assert encoder.stdin is not None

        base_z = float(rows[0]["candidate_anchor_position_m"][2])
        caption_by_camera = {
            SIDE_CAMERA: "policy side cam (re-render)",
            OVERHEAD_CAMERA: "policy overhead cam (re-render)",
        }
        captions = [caption_by_camera[name] for name in policy_cameras]
        captions.append("expert top cam (recorded)")

        def pose(row: dict) -> None:
            for address, value in zip(joint_addresses, row["candidate_qpos_rad"]):
                data.qpos[address] = value
            position = row["candidate_anchor_position_m"]
            data.qpos[anchor_qpos : anchor_qpos + 3] = position
            data.qpos[anchor_qpos + 3 : anchor_qpos + 7] = anchor_quat
            mujoco.mj_forward(model, data)

        for row in rows:
            pose(row)
            views = []
            for camera_name in policy_cameras:
                renderer.update_scene(data, camera=camera_name)
                views.append(renderer.render().copy())
            index = int(row["frame_index"])
            source_frame = source_frames[min(index, len(source_frames) - 1)]
            expert = _decode_observation_png(source_frame, "top").resize(
                (PANEL_SIZE, PANEL_SIZE), Image.NEAREST
            )
            views.append(np.asarray(expert))

            canvas = Image.new("RGB", (frame_width, frame_height), (16, 16, 20))
            for column, view in enumerate(views):
                canvas.paste(
                    Image.fromarray(view), (column * PANEL_SIZE, TEXT_BAR_HEIGHT)
                )
            draw = ImageDraw.Draw(canvas)
            lift_mm = (float(row["candidate_anchor_position_m"][2]) - base_z) * 1000.0
            header = (
                f"{adapter}  seed {seed} ({trace.get('seed_role', 'unknown')})   "
                f"frame {index + 1}/{len(rows)}   phase {row['phase']}   "
                f"strict_contact {row['candidate_strict_contact']}   "
                f"anchor lift {lift_mm:+.2f} mm"
            )
            draw.text((12, 10), header, fill=(235, 235, 235))
            draw.text(
                (12, 30),
                "kinematic playback of signed trace evidence - diagnostic only",
                fill=(150, 150, 150),
            )
            for column, caption in enumerate(captions):
                draw.text(
                    (column * PANEL_SIZE + 12, TEXT_BAR_HEIGHT + PANEL_SIZE + 6),
                    caption,
                    fill=(200, 200, 200),
                )
            encoder.stdin.write(np.asarray(canvas).tobytes())

        renderer.close()
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise SystemExit("ffmpeg failed while encoding the mirror video")

    manifest = sign_payload({
        "schema_version": "scenesmith.rollout_mirror_render.v1",
        "purpose": "diagnostic visualization of signed trace evidence; no authority",
        "trace_path": str(args.trace),
        "trace_identity_sha256": trace.get("identity_sha256"),
        "adapter_id": adapter,
        "seed": seed,
        "seed_role": trace.get("seed_role"),
        "frame_count": len(rows),
        "panels": captions,
        "anchor_orientation": "held at initial value (position-only playback)",
        "output_mp4": str(output),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "output_bytes": output.stat().st_size,
    })
    manifest_path = output.with_suffix(".manifest.json")
    dump_canonical_json(manifest_path, manifest)
    print(output, len(rows), manifest["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

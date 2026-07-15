"""SceneSmith Studio server v0.

Read-only artifact index over the live sim-link checkout plus two
no-authority actions (workcell build, mirror render) that shell out to the
existing CLIs. The repository stays the source of truth: this server renders
signed artifacts and never re-signs, relabels, or mutates them.

Run:
    uvicorn main:app --port 8321 --reload
Env:
    SIM_LINK_DATA_ROOT  live checkout (default /Users/kelly/Developer/sim-link)
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

DATA_ROOT = Path(
    os.environ.get("SIM_LINK_DATA_ROOT", "/Users/kelly/Developer/sim-link")
).resolve()
LEDGER = DATA_ROOT / "docs/autonomous-workflow/experience-compiler-twin-task-ledger.md"
PROJECT_STATE = DATA_ROOT / "docs/autonomous-workflow/project_state.json"
EXPERT_STORE = DATA_ROOT / "outputs/robot_lab/t17_5b_raw_store"
TRACE_STORE = DATA_ROOT / "outputs/robot_lab/t20_32_closed_loop_divergence"
MIRROR_STORE = DATA_ROOT / "outputs/robot_lab/rollout_mirror"
WORKCELL_STORE = DATA_ROOT / "outputs/robot_lab/workcells"
GATE_STORE = DATA_ROOT / "configurations/robot_lab"
REVIEWER_STORE = DATA_ROOT / "docs/reviewer-messages"
BRIEF_STORE = DATA_ROOT / "docs/briefs"
MEDIA_WHITELIST = (MIRROR_STORE, WORKCELL_STORE)
BUILDER_CLI = DATA_ROOT / "scripts/robot_lab/build_workcell_from_spec.py"
MIRROR_CLI = DATA_ROOT / "scripts/robot_lab/render_rollout_mirror.py"
VENV_PYTHON = DATA_ROOT / ".mujoco_venv/bin/python"

app = FastAPI(title="SceneSmith Studio", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger_front_matter() -> dict[str, str]:
    text = LEDGER.read_text(encoding="utf-8")
    match = re.search(r"```text\n(.*?)```", text, re.DOTALL)
    fields: dict[str, str] = {}
    if match:
        for line in match.group(1).splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
    return fields


@app.get("/api/status")
def status() -> dict[str, Any]:
    state = _read_json(PROJECT_STATE)
    reviewers = sorted(REVIEWER_STORE.glob("*.md"))[-5:]
    briefs = sorted(BRIEF_STORE.glob("*.md"))[-5:]
    return {
        "data_root": str(DATA_ROOT),
        "run_window": state.get("run_window"),
        "current_task": state.get("current_task"),
        "current_milestone": state.get("current_milestone"),
        "latest_verified_boundary": state.get(
            "latest_verified_task_implementation_boundary"
        ),
        "ledger": _ledger_front_matter(),
        "recent_reviewer_decisions": [item.name for item in reversed(reviewers)],
        "recent_briefs": [item.name for item in reversed(briefs)],
    }


def _mirror_for(stem: str) -> str | None:
    candidate = MIRROR_STORE / f"{stem}.mp4"
    if candidate.exists():
        return str(candidate.relative_to(DATA_ROOT))
    return None


def _expert_episodes() -> list[dict[str, Any]]:
    episodes = []
    for path in sorted(EXPERT_STORE.glob("*.json")):
        try:
            payload = _read_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        spec = payload.get("episode_spec", {})
        outcome = payload.get("outcome", {})
        episodes.append(
            {
                "id": f"expert/{path.stem}",
                "source": "expert",
                "seed": spec.get("seed"),
                "frame_count": len(payload.get("frames", [])),
                "outcome": {
                    key: outcome.get(key)
                    for key in ("strict_success", "result", "grade")
                    if key in outcome
                },
                "artifact": str(path.relative_to(DATA_ROOT)),
                "mirror_video": None,
            }
        )
    return episodes


def _policy_episodes() -> list[dict[str, Any]]:
    episodes = []
    if not TRACE_STORE.exists():
        return episodes
    for path in sorted(TRACE_STORE.glob("*.json")):
        try:
            payload = _read_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        closed = payload.get("closed_loop", {})
        episodes.append(
            {
                "id": f"trace/{path.stem}",
                "source": "policy_trace",
                "adapter_id": payload.get("adapter_id"),
                "seed": payload.get("seed"),
                "seed_role": payload.get("seed_role"),
                "frame_count": closed.get("frame_count"),
                "strict_success": payload.get(
                    "training_seed_reproduction_strict_success"
                ),
                "maximum_anchor_lift_m": closed.get("maximum_anchor_lift_m"),
                "identity_sha256": payload.get("identity_sha256"),
                "artifact": str(path.relative_to(DATA_ROOT)),
                "mirror_video": _mirror_for(path.stem),
            }
        )
    return episodes


@app.get("/api/episodes")
def episodes() -> dict[str, Any]:
    items = _expert_episodes() + _policy_episodes()
    return {"count": len(items), "episodes": items}


def _resolve_episode(episode_id: str) -> tuple[str, Path]:
    kind, _, stem = episode_id.partition("/")
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", stem or ""):
        raise HTTPException(400, "Malformed episode id")
    root = {"expert": EXPERT_STORE, "trace": TRACE_STORE}.get(kind)
    if root is None:
        raise HTTPException(404, f"Unknown episode kind {kind!r}")
    path = root / f"{stem}.json"
    if not path.exists():
        raise HTTPException(404, "Episode not found")
    return kind, path


# NOTE: registered before episode_detail — the detail route's {episode_id:path}
# converter is greedy and would otherwise swallow /frame/{index}/{view} URLs.
@app.get("/api/episodes/{episode_id:path}/frame/{index}/{view}")
def episode_frame(episode_id: str, index: int, view: str) -> Response:
    kind, path = _resolve_episode(episode_id)
    if kind != "expert" or view not in {"top", "wrist"}:
        raise HTTPException(404, "Frame images exist only for expert episodes")
    frames = _read_json(path).get("frames", [])
    if not 0 <= index < len(frames):
        raise HTTPException(404, "Frame index out of range")
    record = frames[index].get("observations", {}).get(view)
    if not record or record.get("encoding") != "png":
        raise HTTPException(404, "No PNG observation for this view")
    return Response(
        content=base64.b64decode(record["png_base64"]), media_type="image/png"
    )


@app.get("/api/episodes/{episode_id:path}")
def episode_detail(episode_id: str) -> dict[str, Any]:
    kind, path = _resolve_episode(episode_id)
    payload = _read_json(path)
    if kind == "expert":
        frames = payload.get("frames", [])
        timeline = [
            {
                "frame_index": frame.get("frame_index"),
                "task_phase": frame.get("task_phase"),
                "control_mode": frame.get("control_mode"),
            }
            for frame in frames
        ]
        return {
            "id": episode_id,
            "source": "expert",
            "episode_spec": payload.get("episode_spec"),
            "outcome": payload.get("outcome"),
            "frame_count": len(frames),
            "timeline": timeline,
            "camera_views": ["top", "wrist"],
        }
    rows = payload.get("comparisons", [])
    timeline = [
        {
            "frame_index": row.get("frame_index"),
            "phase": row.get("phase"),
            "candidate_strict_contact": row.get("candidate_strict_contact"),
            "anchor_z_m": (row.get("candidate_anchor_position_m") or [None] * 3)[2],
        }
        for row in rows
    ]
    detail = {key: value for key, value in payload.items() if key != "comparisons"}
    detail.update(
        {
            "id": episode_id,
            "source": "policy_trace",
            "timeline": timeline,
            "mirror_video": _mirror_for(path.stem),
        }
    )
    return detail


@app.get("/api/workcells")
def workcells() -> dict[str, Any]:
    cells = []
    if WORKCELL_STORE.exists():
        for manifest in sorted(WORKCELL_STORE.glob("*/build_manifest.json")):
            try:
                payload = _read_json(manifest)
            except (json.JSONDecodeError, OSError):
                continue
            payload["previews"] = {
                camera: str(Path(preview).resolve().relative_to(DATA_ROOT))
                for camera, preview in payload.get("previews", {}).items()
            }
            cells.append(payload)
    return {"count": len(cells), "workcells": cells}


@app.get("/api/tasks")
def tasks() -> dict[str, Any]:
    gates = []
    for path in sorted(GATE_STORE.glob("t20_*result*.json")):
        try:
            payload = _read_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        summary = {
            key: payload[key]
            for key in (
                "schema_version",
                "decision",
                "gate_b_one_batch_memorization_passed",
                "final_to_baseline_objective_ratio",
                "strict_success_count",
                "held_out_seed_count",
                "optimizer_update_count",
            )
            if key in payload
        }
        summary["artifact"] = str(path.relative_to(DATA_ROOT))
        gates.append(summary)
    return {"count": len(gates), "result_gates": gates}


@app.get("/api/media")
def media(path: str) -> FileResponse:
    resolved = (DATA_ROOT / path).resolve()
    if not any(
        resolved.is_relative_to(allowed) for allowed in MEDIA_WHITELIST
    ) or not resolved.is_file():
        raise HTTPException(404, "Not servable")
    return FileResponse(resolved)


@app.post("/api/actions/build-workcell")
def build_workcell(spec: dict[str, Any]) -> dict[str, Any]:
    scene_id = str(spec.get("scene_id", ""))
    if not re.fullmatch(r"[A-Za-z0-9_\-]{1,80}", scene_id):
        raise HTTPException(400, "scene_id must be a short slug")
    drafts = WORKCELL_STORE / "_drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    spec_path = drafts / f"{scene_id}.json"
    spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    result = subprocess.run(
        [str(VENV_PYTHON), str(BUILDER_CLI), "--spec", str(spec_path)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=DATA_ROOT,
    )
    if result.returncode != 0:
        raise HTTPException(422, result.stderr.strip()[-2000:])
    manifest = WORKCELL_STORE / scene_id / "build_manifest.json"
    return _read_json(manifest)


@app.post("/api/actions/render-mirror")
def render_mirror(body: dict[str, Any]) -> dict[str, Any]:
    trace = str(body.get("trace", ""))
    resolved = (DATA_ROOT / trace).resolve()
    if not resolved.is_relative_to(TRACE_STORE) or not resolved.is_file():
        raise HTTPException(400, "trace must be a t20_32 trace path")
    result = subprocess.run(
        [str(VENV_PYTHON), str(MIRROR_CLI), "--trace", str(resolved)],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=DATA_ROOT,
    )
    if result.returncode != 0:
        raise HTTPException(422, result.stderr.strip()[-2000:])
    return {"mirror_video": _mirror_for(resolved.stem)}

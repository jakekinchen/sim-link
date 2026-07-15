"""Shared SceneSmith Studio artifact registry and no-authority actions.

Both the FastAPI app and stdio MCP server call this service. It reads signed
artifacts from the configured sim-link checkout and exposes only the two
existing no-authority writes: workcell fixture builds and mirror renders.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess

from pathlib import Path
from typing import Any


DOCUMENT_FILENAME = re.compile(r"[0-9]{3}-[A-Za-z0-9][A-Za-z0-9_-]{0,180}\.md")


class StudioServiceError(Exception):
    """Expected request failure with an HTTP-compatible status and detail."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class StudioService:
    """Repository-backed registry shared by REST and MCP transports."""

    def __init__(self, data_root: str | Path | None = None) -> None:
        configured_root = data_root or os.environ.get(
            "SIM_LINK_DATA_ROOT", "/Users/kelly/Developer/sim-link"
        )
        self.data_root = Path(configured_root).resolve()
        self.ledger_path = (
            self.data_root
            / "docs/autonomous-workflow/experience-compiler-twin-task-ledger.md"
        )
        self.project_state_path = (
            self.data_root / "docs/autonomous-workflow/project_state.json"
        )
        self.expert_store = self.data_root / "outputs/robot_lab/t17_5b_raw_store"
        self.trace_store = (
            self.data_root / "outputs/robot_lab/t20_32_closed_loop_divergence"
        )
        self.mirror_store = self.data_root / "outputs/robot_lab/rollout_mirror"
        self.workcell_store = self.data_root / "outputs/robot_lab/workcells"
        self.gate_store = self.data_root / "configurations/robot_lab"
        self.reviewer_store = self.data_root / "docs/reviewer-messages"
        self.brief_store = self.data_root / "docs/briefs"
        self.media_whitelist = (self.mirror_store, self.workcell_store)
        self.builder_cli = (
            self.data_root / "scripts/robot_lab/build_workcell_from_spec.py"
        )
        self.mirror_cli = (
            self.data_root / "scripts/robot_lab/render_rollout_mirror.py"
        )
        self.venv_python = self.data_root / ".mujoco_venv/bin/python"

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _ledger_front_matter(self) -> dict[str, str]:
        text = self.ledger_path.read_text(encoding="utf-8")
        match = re.search(r"```text\n(.*?)```", text, re.DOTALL)
        fields: dict[str, str] = {}
        if match:
            for line in match.group(1).splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    fields[key.strip()] = value.strip()
        return fields

    def status(self) -> dict[str, Any]:
        state = self._read_json(self.project_state_path)
        reviewers = sorted(self.reviewer_store.glob("*.md"))[-5:]
        briefs = sorted(self.brief_store.glob("*.md"))[-5:]
        return {
            "data_root": str(self.data_root),
            "run_window": state.get("run_window"),
            "current_task": state.get("current_task"),
            "current_milestone": state.get("current_milestone"),
            "latest_verified_boundary": state.get(
                "latest_verified_task_implementation_boundary"
            ),
            "ledger": self._ledger_front_matter(),
            "recent_reviewer_decisions": [
                item.name for item in reversed(reviewers)
            ],
            "recent_briefs": [item.name for item in reversed(briefs)],
        }

    def _mirror_for(self, stem: str) -> str | None:
        candidate = self.mirror_store / f"{stem}.mp4"
        if candidate.exists():
            return str(candidate.relative_to(self.data_root))
        return None

    def _expert_episodes(self) -> list[dict[str, Any]]:
        episodes = []
        for path in sorted(self.expert_store.glob("*.json")):
            try:
                payload = self._read_json(path)
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
                    "artifact": str(path.relative_to(self.data_root)),
                    "mirror_video": None,
                }
            )
        return episodes

    def _policy_episodes(self) -> list[dict[str, Any]]:
        episodes = []
        if not self.trace_store.exists():
            return episodes
        for path in sorted(self.trace_store.glob("*.json")):
            try:
                payload = self._read_json(path)
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
                    "artifact": str(path.relative_to(self.data_root)),
                    "mirror_video": self._mirror_for(path.stem),
                }
            )
        return episodes

    def episodes(self) -> dict[str, Any]:
        items = self._expert_episodes() + self._policy_episodes()
        return {"count": len(items), "episodes": items}

    def _resolve_episode(self, episode_id: str) -> tuple[str, Path]:
        kind, _, stem = episode_id.partition("/")
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", stem or ""):
            raise StudioServiceError(400, "Malformed episode id")
        root = {"expert": self.expert_store, "trace": self.trace_store}.get(kind)
        if root is None:
            raise StudioServiceError(404, f"Unknown episode kind {kind!r}")
        path = root / f"{stem}.json"
        if not path.exists():
            raise StudioServiceError(404, "Episode not found")
        return kind, path

    def episode_frame(
        self, episode_id: str, index: int, view: str
    ) -> bytes:
        kind, path = self._resolve_episode(episode_id)
        if kind != "expert" or view not in {"top", "wrist"}:
            raise StudioServiceError(
                404, "Frame images exist only for expert episodes"
            )
        frames = self._read_json(path).get("frames", [])
        if not 0 <= index < len(frames):
            raise StudioServiceError(404, "Frame index out of range")
        record = frames[index].get("observations", {}).get(view)
        if not record or record.get("encoding") != "png":
            raise StudioServiceError(404, "No PNG observation for this view")
        return base64.b64decode(record["png_base64"])

    def episode_detail(self, episode_id: str) -> dict[str, Any]:
        kind, path = self._resolve_episode(episode_id)
        payload = self._read_json(path)
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
                "anchor_z_m": (
                    row.get("candidate_anchor_position_m") or [None] * 3
                )[2],
            }
            for row in rows
        ]
        detail = {
            key: value for key, value in payload.items() if key != "comparisons"
        }
        detail.update(
            {
                "id": episode_id,
                "source": "policy_trace",
                "timeline": timeline,
                "mirror_video": self._mirror_for(path.stem),
            }
        )
        return detail

    def workcells(self) -> dict[str, Any]:
        cells = []
        if self.workcell_store.exists():
            for manifest in sorted(
                self.workcell_store.glob("*/build_manifest.json")
            ):
                try:
                    payload = self._read_json(manifest)
                except (json.JSONDecodeError, OSError):
                    continue
                payload["previews"] = {
                    camera: str(
                        Path(preview).resolve().relative_to(self.data_root)
                    )
                    for camera, preview in payload.get("previews", {}).items()
                }
                cells.append(payload)
        return {"count": len(cells), "workcells": cells}

    def tasks(self) -> dict[str, Any]:
        gates = []
        for path in sorted(self.gate_store.glob("t20_*result*.json")):
            try:
                payload = self._read_json(path)
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
            summary["artifact"] = str(path.relative_to(self.data_root))
            gates.append(summary)
        return {"count": len(gates), "result_gates": gates}

    def document(self, kind: str, filename: str) -> dict[str, str]:
        store = {
            "briefs": self.brief_store,
            "reviewer-messages": self.reviewer_store,
        }.get(kind)
        if store is None:
            raise StudioServiceError(404, "Unknown document kind")
        if not DOCUMENT_FILENAME.fullmatch(filename):
            raise StudioServiceError(400, "Malformed document filename")
        document_path = store / filename
        if not document_path.is_file():
            raise StudioServiceError(404, "Document not found")
        return {
            "kind": kind,
            "filename": filename,
            "content": document_path.read_text(encoding="utf-8"),
        }

    def media_path(self, path: str) -> Path:
        resolved = (self.data_root / path).resolve()
        if not any(
            resolved.is_relative_to(allowed) for allowed in self.media_whitelist
        ) or not resolved.is_file():
            raise StudioServiceError(404, "Not servable")
        return resolved

    def build_workcell(self, spec: dict[str, Any]) -> dict[str, Any]:
        scene_id = str(spec.get("scene_id", ""))
        if not re.fullmatch(r"[A-Za-z0-9_\-]{1,80}", scene_id):
            raise StudioServiceError(400, "scene_id must be a short slug")
        drafts = self.workcell_store / "_drafts"
        drafts.mkdir(parents=True, exist_ok=True)
        spec_path = drafts / f"{scene_id}.json"
        spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        result = subprocess.run(
            [str(self.venv_python), str(self.builder_cli), "--spec", str(spec_path)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=self.data_root,
        )
        if result.returncode != 0:
            raise StudioServiceError(422, result.stderr.strip()[-2000:])
        manifest = self.workcell_store / scene_id / "build_manifest.json"
        return self._read_json(manifest)

    def render_mirror(self, body: dict[str, Any]) -> dict[str, Any]:
        trace = str(body.get("trace", ""))
        resolved = (self.data_root / trace).resolve()
        if not resolved.is_relative_to(self.trace_store) or not resolved.is_file():
            raise StudioServiceError(400, "trace must be a t20_32 trace path")
        result = subprocess.run(
            [str(self.venv_python), str(self.mirror_cli), "--trace", str(resolved)],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=self.data_root,
        )
        if result.returncode != 0:
            raise StudioServiceError(422, result.stderr.strip()[-2000:])
        return {"mirror_video": self._mirror_for(resolved.stem)}


service = StudioService()

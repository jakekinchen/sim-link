"""Shared SceneSmith Studio artifact registry and no-authority actions.

Both the FastAPI app and stdio MCP server call this service. It reads signed
artifacts from the configured sim-link checkout and exposes only the two
existing no-authority writes: workcell fixture builds and mirror renders.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess

from pathlib import Path
from typing import Any


DOCUMENT_FILENAME = re.compile(r"[0-9]{3}-[A-Za-z0-9][A-Za-z0-9_-]{0,180}\.md")
SHA256_HEX = re.compile(r"[0-9a-f]{64}")


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
        self.robot_artifacts = {
            "live_observation": self.gate_store
            / "pi05_live_readonly_observation.redacted.json",
            "census_contract": self.gate_store
            / "pi05_readonly_servo_census_contract.fixture.json",
            "calibration_profile": self.gate_store / "pi05_calibration_profile.json",
        }
        self.robot_schemas = {
            "live_observation": "scenesmith.live_readonly_observation_manifest.v5",
            "census_contract": "scenesmith.readonly_servo_census_contract.v3",
            "calibration_profile": "scenesmith.calibration_profile.v1",
        }
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

    def _robot_artifact(self, name: str) -> tuple[dict[str, Any], dict[str, str]]:
        path = self.robot_artifacts[name]
        resolved = path.resolve()
        if not resolved.is_relative_to(
            self.gate_store.resolve()
        ) or not resolved.is_file():
            raise StudioServiceError(
                503, f"Required robot artifact unavailable: {path.name}"
            )
        try:
            raw = resolved.read_bytes()
            payload = json.loads(raw)
        except (json.JSONDecodeError, OSError) as error:
            raise StudioServiceError(
                503, f"Required robot artifact unreadable: {path.name}"
            ) from error
        if not isinstance(payload, dict):
            raise StudioServiceError(
                503, f"Required robot artifact malformed: {path.name}"
            )
        if payload.get("schema_version") != self.robot_schemas[name]:
            raise StudioServiceError(
                503, f"Required robot artifact schema mismatch: {path.name}"
            )
        identity_sha256 = payload.get("identity_sha256")
        if not isinstance(identity_sha256, str) or not SHA256_HEX.fullmatch(
            identity_sha256
        ):
            raise StudioServiceError(
                503, f"Required robot artifact identity malformed: {path.name}"
            )
        source = {
            "artifact": str(resolved.relative_to(self.data_root)),
            "artifact_sha256": hashlib.sha256(raw).hexdigest(),
            "identity_sha256": identity_sha256,
            "schema_version": str(payload.get("schema_version", "")),
        }
        return payload, source

    def robot(self) -> dict[str, Any]:
        """Render a fixed, privacy-safe robot evidence projection without device access."""

        observation, observation_source = self._robot_artifact("live_observation")
        census_contract, census_source = self._robot_artifact("census_contract")
        calibration, calibration_source = self._robot_artifact("calibration_profile")
        expected_servos = census_contract.get("expected_servos", [])
        forbidden_operations = census_contract.get("forbidden_operations", [])
        accepted_live_manifest = calibration.get("accepted_live_manifest")
        if not isinstance(accepted_live_manifest, dict) or (
            accepted_live_manifest.get("file_sha256")
            != observation_source["artifact_sha256"]
            or accepted_live_manifest.get("identity_sha256")
            != observation_source["identity_sha256"]
        ):
            raise StudioServiceError(
                503, "Calibration profile does not bind the current live observation"
            )

        cameras = []
        for camera in observation.get("cameras", []):
            if not isinstance(camera, dict):
                continue
            mode = camera.get("input_mode")
            cameras.append(
                {
                    "stable_identity_sha256": camera.get("stable_camera_identity_sha256"),
                    "capture_identity_sha256": camera.get("capture_camera_identity_sha256"),
                    "input_mode": mode if isinstance(mode, dict) else {},
                    "frame_count": len(camera.get("frames", []))
                    if isinstance(camera.get("frames"), list)
                    else 0,
                }
            )

        servos = []
        for servo in observation.get("servo_identity", []):
            if isinstance(servo, dict):
                servos.append(
                    {
                        key: servo.get(key)
                        for key in (
                            "servo_id",
                            "joint_name",
                            "model",
                            "model_number",
                            "firmware_version",
                        )
                    }
                )

        joints = []
        for joint in calibration.get("joints", []):
            if not isinstance(joint, dict):
                continue
            normalization = joint.get("normalization")
            joints.append(
                {
                    key: joint.get(key)
                    for key in (
                        "servo_id",
                        "joint_name",
                        "model",
                        "firmware_version",
                        "drive_mode",
                        "homing_offset",
                        "range_min",
                        "range_max",
                    )
                }
                | {
                    "normalization_mode": normalization.get("mode")
                    if isinstance(normalization, dict)
                    else None
                }
            )

        observed_servo_ids = {servo.get("servo_id") for servo in servos}
        calibrated_servo_ids = {joint.get("servo_id") for joint in joints}
        if (
            calibration.get("joint_count") != len(joints)
            or observed_servo_ids != calibrated_servo_ids
        ):
            raise StudioServiceError(
                503, "Calibration profile and observed servo census disagree"
            )

        proof_labels = observation.get("proof_labels")
        privacy = observation.get("privacy")
        camera_operation_counts = observation.get("camera_operation_counts")
        operation_counts = observation.get("operation_counts")
        normalization_contract = calibration.get("normalization_contract")
        authority_not_granted = calibration.get("authority_not_granted")

        return {
            "mode": "signed_artifacts_read_only",
            "registration": {
                "enabled": False,
                "reason": "requires a separately reviewed owner-present permit slice.",
            },
            "discovery": observation_source
            | {
                "manifest_name": observation.get("manifest_name"),
                "session_id": observation.get("session_id"),
                "evidence_mode": observation.get("evidence_mode"),
                "qualification_scope": observation.get("qualification_scope"),
                "proof_labels": proof_labels if isinstance(proof_labels, list) else [],
                "discovery_stability": observation.get("discovery_stability"),
                "hardware_opened": observation.get("hardware_opened"),
                "physical_follower_commanded": observation.get(
                    "physical_follower_commanded"
                ),
                "pre_open_identity_sha256": observation.get(
                    "pre_open_discovery_identity_sha256"
                ),
                "post_close_identity_sha256": observation.get(
                    "post_close_discovery_identity_sha256"
                ),
                "privacy": privacy if isinstance(privacy, dict) else {},
                "camera_operation_counts": camera_operation_counts
                if isinstance(camera_operation_counts, dict)
                else {},
                "cameras": cameras,
            },
            "census": observation_source
            | {
                "session_id": observation.get("session_id"),
                "proof_labels": proof_labels if isinstance(proof_labels, list) else [],
                "servos": servos,
                "operation_counts": operation_counts
                if isinstance(operation_counts, dict)
                else {},
                "contract": census_source
                | {
                    "contract_name": census_contract.get("contract_name"),
                    "proof_label": census_contract.get("proof_label"),
                    "qualification_scope": census_contract.get("qualification_scope"),
                    "expected_servo_count": len(expected_servos)
                    if isinstance(expected_servos, list)
                    else 0,
                    "forbidden_operations": forbidden_operations
                    if isinstance(forbidden_operations, list)
                    else [],
                },
            },
            "calibration": calibration_source
            | {
                "profile_name": calibration.get("profile_name"),
                "evidence_mode": calibration.get("evidence_mode"),
                "qualification_scope": calibration.get("qualification_scope"),
                "joint_count": calibration.get("joint_count"),
                "joints": joints,
                "normalization_contract": normalization_contract
                if isinstance(normalization_contract, dict)
                else {},
                "accepted_live_manifest": accepted_live_manifest,
                "hardware_accessed": calibration.get("hardware_accessed"),
                "physical_follower_commanded": calibration.get(
                    "physical_follower_commanded"
                ),
                "motion_authority_granted": calibration.get("motion_authority_granted"),
                "training_authority_granted": calibration.get(
                    "training_authority_granted"
                ),
                "authority_not_granted": authority_not_granted
                if isinstance(authority_not_granted, list)
                else [],
            },
        }

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

#!/usr/bin/env python3
"""Verify a SceneSmith randomized intervention batch and its temporal artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json

from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-summary", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--expected-episodes", type=int)
    args = parser.parse_args()

    batch = json.loads(args.batch_summary.read_text(encoding="utf-8"))
    summary_paths = [Path(path) for path in batch.get("episode_summaries", [])]
    checks: dict[str, bool] = {
        "batch_status_pass": batch.get("status") == "pass",
        "has_episode_summaries": bool(summary_paths),
        "episode_count_matches": (
            args.expected_episodes is None or len(summary_paths) == args.expected_episodes
        ),
    }
    reports = []
    for summary_path in summary_paths:
        reports.append(_verify_episode(summary_path))
    checks["all_episode_checks_pass"] = bool(reports) and all(
        all(report["checks"].values()) for report in reports
    )
    payload = {
        "schema_version": "scenesmith.intervention_batch_verification.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "batch_summary": str(args.batch_summary),
        "checks": checks,
        "episodes": reports,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


def _verify_episode(summary_path: Path) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    episode_dir = summary_path.parent
    trajectory_path = Path(summary["artifacts"]["trajectory"])
    frames = json.loads(trajectory_path.read_text(encoding="utf-8"))["frames"]
    image_paths = []
    frame_contract = True
    for index, frame in enumerate(frames):
        images = frame.get("observation", {}).get("images", {})
        paths = [episode_dir / images.get(role, "missing") for role in ("base", "wrist", "overhead")]
        image_paths.extend(paths)
        frame_contract = frame_contract and all(
            (
                frame.get("frame_index") == index,
                len(frame.get("observation", {}).get("state", [])) == 6,
                len(frame.get("policy_action", [])) == 6,
                len(frame.get("executed_action", [])) == 6,
                len(frame.get("transition", {}).get("next_state", [])) == 6,
                frame.get("action_source") in {"policy", "human_leader"},
            )
        )
    existing_images = [path for path in image_paths if path.is_file()]
    hashes = {_sha256(path) for path in existing_images}
    manifest = json.loads(Path(summary["randomization_manifest"]).read_text(encoding="utf-8"))
    intervention_rows = _read_jsonl(Path(summary["artifacts"]["intervention_frames"]))
    checks = {
        "schema_v2": summary.get("schema_version") == "scenesmith.intervention_episode.v2",
        "status_pass": summary.get("status") == "pass",
        "final_score_success": bool(summary.get("final_score", {}).get("success")),
        "control_step_arbitration": bool(
            summary.get("intervention", {}).get("control_step_arbitration")
        ),
        "synchronized_observations": bool(
            summary.get("proof_scope", {}).get("synchronized_observations")
        ),
        "pre_action_alignment": summary.get("proof_scope", {}).get(
            "observation_action_alignment"
        )
        == "pre_action_observation_to_executed_action",
        "frame_count_matches": len(frames) == summary.get("observation_frames") and bool(frames),
        "frame_contract_complete": frame_contract,
        "all_images_exist": len(existing_images) == len(frames) * 3,
        "temporal_images_are_distinct": len(hashes) == len(existing_images),
        "intervention_rows_present": bool(intervention_rows),
        "takeover_transition_present": any(
            row.get("intervention_event") == "takeover_started" for row in intervention_rows
        ),
        "follower_never_commanded": summary.get("intervention", {}).get(
            "physical_follower_commanded"
        )
        is False,
        "mujoco_randomization_applied": manifest.get("mujoco_applied", {}).get("status")
        == "applied",
        "proof_scope_is_explicit": bool(summary.get("proof_scope", {}).get("object_motion_modes")),
    }
    return {
        "summary": str(summary_path),
        "seed": summary.get("seed"),
        "checks": checks,
        "frames": len(frames),
        "images": len(existing_images),
        "unique_image_hashes": len(hashes),
        "intervention_frames": len(intervention_rows),
        "object_motion_modes": summary.get("proof_scope", {}).get("object_motion_modes"),
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

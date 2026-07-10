#!/usr/bin/env python3
"""Verify the expected-failure neural contact-physics intervention smoke."""

from __future__ import annotations

import argparse
import json

from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-summary", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    summary = json.loads(args.episode_summary.read_text(encoding="utf-8"))
    frames = json.loads(Path(summary["artifacts"]["trajectory"]).read_text(encoding="utf-8"))[
        "frames"
    ]
    policy_frames = [
        frame for frame in frames if frame.get("object_motion_mode") == "contact_physics_neural_policy"
    ]
    checks = {
        "task_failure_is_reported": summary.get("status") == "fail",
        "failure_detector_fired": summary.get("failure_reason")
        in {"neural_policy_stalled", "neural_policy_timeout"},
        "persistent_pi05_runtime": summary.get("policy_runtime", {}).get("kind")
        == "persistent_lerobot_http"
        and summary.get("policy_runtime", {}).get("server_status", {}).get("policy_type")
        == "pi05",
        "mps_runtime": summary.get("policy_runtime", {}).get("server_status", {}).get("device")
        == "mps",
        "neural_actions_applied": bool(policy_frames)
        and summary.get("proof_scope", {}).get("neural_policy_actions_applied_to_simulation")
        is True,
        "no_scripted_object_motion": summary.get("proof_scope", {}).get("scripted_object_motion")
        is False,
        "policy_frames_are_synchronized": all(
            len(frame.get("observation", {}).get("state", [])) == 6
            and len(frame.get("executed_action", [])) == 6
            and len(frame.get("transition", {}).get("next_state", [])) == 6
            for frame in policy_frames
        ),
        "follower_never_commanded": summary.get("intervention", {}).get(
            "physical_follower_commanded"
        )
        is False
        and summary.get("policy_runtime", {}).get("physical_follower_commanded") is False,
        "contact_success_not_fabricated": summary.get("intervention", {}).get(
            "contact_physics_verified"
        )
        is False,
    }
    payload = {
        "schema_version": "scenesmith.neural_policy_smoke_verification.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "episode_summary": str(args.episode_summary),
        "checks": checks,
        "policy_frames": len(policy_frames),
        "failure_reason": summary.get("failure_reason"),
        "last_policy_action": summary.get("policy_runtime", {}).get("last_action"),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

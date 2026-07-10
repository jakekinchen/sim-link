#!/usr/bin/env python3
"""Send synchronized SceneSmith observations to the local policy service."""

from __future__ import annotations

import argparse
import json

from pathlib import Path
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8833")
    parser.add_argument("--episode-summary", type=Path, required=True)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--requests", type=int, default=2)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    summary = json.loads(args.episode_summary.read_text(encoding="utf-8"))
    frames = json.loads(Path(summary["artifacts"]["trajectory"]).read_text(encoding="utf-8"))[
        "frames"
    ]
    frame = frames[args.frame_index]
    images = {
        role: str((args.episode_summary.parent / relative).resolve())
        for role, relative in frame["observation"]["images"].items()
    }
    _post(args.url, "/reset", {})
    actions = [
        _post(
            args.url,
            "/action",
            {
                "images": images,
                "state": frame["observation"]["state"],
                "task": summary["task"],
            },
        )
        for _ in range(args.requests)
    ]
    checks = {
        "all_requests_pass": all(action.get("ok") for action in actions),
        "all_actions_have_six_mujoco_targets": all(
            len(action.get("action_mujoco", [])) == 6 for action in actions
        ),
        "mps_policy": all(action.get("device") == "mps" for action in actions),
        "pi05_policy": all(action.get("policy_type") == "pi05" for action in actions),
        "follower_never_commanded": all(
            action.get("physical_follower_commanded") is False for action in actions
        ),
    }
    payload = {
        "schema_version": "scenesmith.local_policy_server_probe.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "url": args.url,
        "episode_summary": str(args.episode_summary),
        "frame_index": args.frame_index,
        "checks": checks,
        "actions": actions,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


def _post(base_url: str, path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())

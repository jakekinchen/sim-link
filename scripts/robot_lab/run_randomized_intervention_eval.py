#!/usr/bin/env python3
"""Run randomized SceneSmith SO-101 intervention episodes."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenesmith.robot_lab import build_so101_desk_sort_scene, scene_from_dict
from scenesmith.robot_lab.intervention_supervisor import (
    EpisodeRunConfig,
    run_domain_randomized_intervention_episode,
    run_neural_policy_intervention_episode,
)


DEFAULT_DESCRIPTION = (
    "Set up an SO-101 arm on a desk in a simulation room with two colored trays, "
    "one red and one blue, plus a set of red and blue cubes. The robot should sort "
    "each cube into the tray with the matching color."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-json", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument(
        "--correction-source",
        choices=("none", "simulated_leader", "studio_leader", "physical_leader"),
        default="simulated_leader",
    )
    parser.add_argument("--force-failure", action="store_true")
    parser.add_argument(
        "--policy-source",
        choices=("scripted", "http"),
        default="scripted",
    )
    parser.add_argument("--policy-url", default="http://127.0.0.1:8833")
    parser.add_argument("--max-policy-steps", type=int, default=20)
    parser.add_argument("--leader-port")
    parser.add_argument("--leader-config")
    parser.add_argument("--studio-url", default="http://127.0.0.1:8790")
    parser.add_argument("--intervention-control", type=Path)
    parser.add_argument("--control-hz", type=int, default=10)
    parser.add_argument("--steps-per-waypoint", type=int, default=3)
    parser.add_argument("--observation-width", type=int, default=224)
    parser.add_argument("--observation-height", type=int, default=224)
    parser.add_argument(
        "--grasp-assist-mode",
        choices=(
            "none",
            "policy_gripper",
            "contact_reflex",
            "policy_gripper_tray_release",
            "policy_gripper_tray_transfer",
        ),
        default="policy_gripper",
    )
    parser.add_argument("--contact-reflex-max-hold-steps", type=int, default=300)
    parser.add_argument("--precontact-stall-steps", type=int, default=240)
    parser.add_argument("--precontact-min-progress-m", type=float, default=0.005)
    parser.add_argument("--precontact-contact-distance-m", type=float, default=0.05)
    parser.add_argument("--deadman-timeout", type=float, default=0.55)
    parser.add_argument("--intervention-wait-timeout", type=float, default=20.0)
    parser.add_argument("--intervention-run-timeout", type=float, default=45.0)
    parser.add_argument("--realtime", action="store_true")
    args = parser.parse_args()

    if args.episodes <= 0:
        parser.error("--episodes must be positive")
    if args.contact_reflex_max_hold_steps <= 0:
        parser.error("--contact-reflex-max-hold-steps must be positive")
    if args.precontact_stall_steps <= 0:
        parser.error("--precontact-stall-steps must be positive")
    if (
        args.correction_source not in {"none", "simulated_leader"}
        and args.intervention_control is None
    ):
        parser.error(f"{args.correction_source} requires --intervention-control")
    if args.policy_source == "http" and args.correction_source == "simulated_leader":
        parser.error("HTTP neural policy mode requires studio_leader or physical_leader correction")

    if args.scene_json:
        scene = scene_from_dict(json.loads(args.scene_json.read_text(encoding="utf-8")))
    else:
        scene = build_so101_desk_sort_scene(DEFAULT_DESCRIPTION)

    summaries = []
    run_config = EpisodeRunConfig(
        control_hz=args.control_hz,
        scripted_steps_per_waypoint=args.steps_per_waypoint,
        observation_width=args.observation_width,
        observation_height=args.observation_height,
        deadman_timeout_s=args.deadman_timeout,
        intervention_wait_timeout_s=args.intervention_wait_timeout,
        intervention_run_timeout_s=args.intervention_run_timeout,
        grasp_assist_mode=args.grasp_assist_mode,
        contact_reflex_max_hold_steps=args.contact_reflex_max_hold_steps,
        precontact_stall_steps=args.precontact_stall_steps,
        precontact_min_progress_m=args.precontact_min_progress_m,
        precontact_contact_distance_m=args.precontact_contact_distance_m,
        realtime=(
            args.realtime
            or args.correction_source in {"studio_leader", "physical_leader"}
        ),
    )
    for index in range(args.episodes):
        episode_seed = args.seed + index
        episode_dir = args.output_dir / f"randomized-episode-{episode_seed}"
        common = {
            "output_dir": episode_dir,
            "seed": episode_seed,
            "correction_source": args.correction_source,
            "leader_port": args.leader_port,
            "leader_config": args.leader_config,
            "studio_url": args.studio_url,
            "intervention_control_path": args.intervention_control,
            "progress_path": episode_dir / "intervention_progress.json",
            "run_config": run_config,
        }
        if args.policy_source == "http":
            summary = run_neural_policy_intervention_episode(
                scene,
                policy_url=args.policy_url,
                max_policy_steps=args.max_policy_steps,
                **common,
            )
        else:
            summary = run_domain_randomized_intervention_episode(
                scene,
                force_failure=args.force_failure,
                **common,
            )
        summaries.append(summary)

    batch_summary = {
        "schema_version": "scenesmith.intervention_batch.v1",
        "status": "pass" if all(item["status"] == "pass" for item in summaries) else "fail",
        "episodes": len(summaries),
        "seed_start": args.seed,
        "correction_source": args.correction_source,
        "force_failure": args.force_failure,
        "policy_source": args.policy_source,
        "policy_url": args.policy_url if args.policy_source == "http" else None,
        "control_hz": args.control_hz,
        "intervention_control": str(args.intervention_control) if args.intervention_control else None,
        "episode_summaries": [
            item["artifacts"]["summary"]
            for item in summaries
        ],
        "results": summaries,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    batch_path = args.output_dir / "intervention_batch_summary.json"
    batch_path.write_text(
        json.dumps(batch_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(batch_summary, indent=2, sort_keys=True))
    return 0 if batch_summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

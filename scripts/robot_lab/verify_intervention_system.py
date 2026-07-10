#!/usr/bin/env python3
"""Audit the complete SceneSmith SO-101 intervention system from current evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys

from pathlib import Path
from typing import Any
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs/robot_lab/so101_desk_cube_sort"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path(
            "outputs/robot_lab/so101_desk_cube_sort/completion-audit/"
            "intervention-system-completion.json"
        ),
    )
    parser.add_argument("--action-url", default="http://127.0.0.1:8822")
    parser.add_argument("--policy-url", default="http://127.0.0.1:8833")
    args = parser.parse_args()

    root = (REPO_ROOT / args.output_root).resolve()
    evidence_paths = {
        "scene": root / "scene.json",
        "fiducial_report": root / "fiducials/apriltag_calibration_report.json",
        "fiducial_detection": root / "completion-audit/apriltag-detection-proof.json",
        "batch": root / "intervention-proof/intervention_batch_verification.json",
        "leader_sample": root / "intervention-proof/studio-leader-readonly-sample.json",
        "leader_control": root
        / "intervention-proof/studio-leader-control-smoke/run/randomized-episode-4200/"
        "intervention_episode_summary.json",
        "dataset_all": root
        / "datasets/intervention-proof/scenesmith_intervention_export_summary.json",
        "dataset_intervention": root
        / "datasets/intervention-only-proof/scenesmith_intervention_export_summary.json",
        "browser_scripted": root
        / "action-server-intervention-proof-final/action-server-proof.json",
        "browser_neural": root / "action-server-neural-proof/action-server-proof.json",
        "policy_probe": root / "intervention-proof/local-policy-server-probe.json",
    }
    missing = [str(path) for path in evidence_paths.values() if not path.is_file()]
    payloads = {
        name: _read_json(path)
        for name, path in evidence_paths.items()
        if path.is_file()
    }

    tests = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.unit.test_robot_lab_scene_builder",
            "tests.unit.test_robot_lab_intervention",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    action_status = _fetch_json(f"{args.action_url.rstrip('/')}/api/status")
    policy_status = _fetch_json(f"{args.policy_url.rstrip('/')}/status")

    scene = payloads.get("scene", {})
    fiducial_report = payloads.get("fiducial_report", {})
    fiducial_detection = payloads.get("fiducial_detection", {})
    batch = payloads.get("batch", {})
    leader_sample = payloads.get("leader_sample", {})
    leader_control = payloads.get("leader_control", {})
    dataset_all = payloads.get("dataset_all", {})
    dataset_intervention = payloads.get("dataset_intervention", {})
    browser_scripted = payloads.get("browser_scripted", {})
    browser_neural = payloads.get("browser_neural", {})
    policy_probe = payloads.get("policy_probe", {})

    detections = fiducial_detection.get("detections", [])
    tag = next(
        (
            item
            for item in detections
            if item.get("family") == "tag36h11" and item.get("tag_id") == 0
        ),
        {},
    )
    calibration_tag = (fiducial_report.get("fiducials") or [{}])[0]
    scene_tag = (scene.get("fiducials") or [{}])[0]
    batch_episodes = batch.get("episodes", [])
    scripted_result = browser_scripted.get("result", {})
    neural_result = browser_neural.get("result", {})
    leader_safety = leader_sample.get("safety_report", {})
    control_intervention = leader_control.get("intervention", {})
    control_safety = control_intervention.get("safety_report", {})

    requirements = {
        "apriltag_fiducial": _requirement(
            fiducial_detection.get("status") == "pass"
            and tag.get("hamming") == 0
            and calibration_tag.get("grid_size") == 10
            and calibration_tag.get("grid_encoding") == "1=black,0=white"
            and scene_tag.get("family") == "tag36h11"
            and scene_tag.get("tag_id") == 0,
            {
                "family": tag.get("family"),
                "tag_id": tag.get("tag_id"),
                "hamming": tag.get("hamming"),
                "decision_margin": tag.get("decision_margin"),
                "grid_size": calibration_tag.get("grid_size"),
            },
        ),
        "randomized_mujoco_episodes": _requirement(
            batch.get("status") == "pass"
            and len(batch_episodes) == 3
            and all(
                episode.get("checks", {}).get("mujoco_randomization_applied")
                and episode.get("checks", {}).get("synchronized_observations")
                and episode.get("checks", {}).get("all_images_exist")
                for episode in batch_episodes
            ),
            {
                "episodes": len(batch_episodes),
                "seeds": [item.get("seed") for item in batch_episodes],
                "frames": sum(int(item.get("frames", 0)) for item in batch_episodes),
                "unique_images": sum(
                    int(item.get("unique_image_hashes", 0)) for item in batch_episodes
                ),
            },
        ),
        "leader_arm_correction_bridge": _requirement(
            leader_sample.get("status") == "pass"
            and len(leader_sample.get("samples", [])) >= 5
            and leader_safety.get("hardware_opened_by_scenesmith") is False
            and leader_safety.get("motor_register_writes") == 0
            and control_intervention.get("frames", 0) > 0
            and control_intervention.get("source") == "studio_leader"
            and control_safety.get("physical_follower_commanded") is False,
            {
                "readonly_samples": len(leader_sample.get("samples", [])),
                "control_frames": control_intervention.get("frames"),
                "source": control_intervention.get("source"),
                "contact_success_claimed": control_intervention.get(
                    "contact_physics_verified"
                ),
            },
        ),
        "intervention_dataset_export": _requirement(
            dataset_all.get("status") == "pass"
            and dataset_all.get("num_episodes") == 3
            and dataset_all.get("num_frames") == 180
            and dataset_all.get("verified", {}).get("num_frames") == 180
            and dataset_intervention.get("status") == "pass"
            and dataset_intervention.get("num_episodes") == 3
            and dataset_intervention.get("num_frames") == 36
            and dataset_intervention.get("num_intervention_frames") == 36
            and dataset_intervention.get("verified", {}).get("num_frames") == 36,
            {
                "all_frames": dataset_all.get("num_frames"),
                "all_intervention_frames": dataset_all.get("num_intervention_frames"),
                "intervention_only_frames": dataset_intervention.get("num_frames"),
                "episodes": dataset_intervention.get("num_episodes"),
            },
        ),
        "action_server_ui_hooks": _requirement(
            browser_scripted.get("status") == "pass"
            and browser_neural.get("status") == "pass"
            and not browser_scripted.get("console_errors")
            and not browser_neural.get("console_errors")
            and scripted_result.get("interventionControlPresent") is True
            and scripted_result.get("policySourceControlPresent") is True
            and neural_result.get("policyRuntimeKind") == "persistent_lerobot_http"
            and neural_result.get("policyDevice") == "mps"
            and neural_result.get("neuralActionsApplied") is True
            and neural_result.get("scriptedObjectMotion") is False,
            {
                "scripted_status": browser_scripted.get("status"),
                "neural_status": browser_neural.get("status"),
                "neural_task_outcome": neural_result.get("episodeStatus"),
                "neural_failure_reason": neural_result.get("failureReason"),
                "camera_thumbnails": neural_result.get("cameraThumbnailCount"),
            },
        ),
        "documentation": _requirement(
            all(
                path.is_file() and path.stat().st_size > 0
                for path in (
                    REPO_ROOT / "docs/so101-domain-randomized-interventions.md",
                    REPO_ROOT / "docs/so101-lelab-scenesmith-bridge.md",
                    REPO_ROOT / "GOAL.md",
                )
            ),
            {
                "paths": [
                    "docs/so101-domain-randomized-interventions.md",
                    "docs/so101-lelab-scenesmith-bridge.md",
                    "GOAL.md",
                ]
            },
        ),
        "tests": _requirement(
            tests.returncode == 0,
            {
                "returncode": tests.returncode,
                "summary": _last_nonempty_lines(tests.stdout + "\n" + tests.stderr, 6),
            },
        ),
        "proof_artifacts": _requirement(not missing, {"missing": missing}),
        "physical_follower_exclusion": _requirement(
            leader_sample.get("physical_follower_commanded") is False
            and control_intervention.get("physical_follower_commanded") is False
            and scripted_result.get("physicalFollowerCommanded") is False
            and neural_result.get("physicalFollowerCommanded") is False
            and policy_probe.get("checks", {}).get("follower_never_commanded") is True
            and policy_status.get("physical_follower_commanded") is False,
            {"commanded": False},
        ),
        "live_services": _requirement(
            action_status.get("ok") is True
            and action_status.get("randomized_intervention", {}).get(
                "control_step_arbitration"
            )
            is True
            and policy_status.get("ok") is True
            and policy_status.get("ready") is True
            and policy_status.get("device") == "mps",
            {
                "action_url": args.action_url,
                "policy_url": args.policy_url,
                "policy_device": policy_status.get("device"),
            },
        ),
    }

    report = {
        "schema_version": "scenesmith.intervention_system_completion.v1",
        "status": (
            "pass"
            if all(item["status"] == "pass" for item in requirements.values())
            else "fail"
        ),
        "requirements": requirements,
        "evidence": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in evidence_paths.items()
            if path.is_file()
        },
        "proof_boundaries": {
            "scripted_batch": "pipeline acceptance only; scripted object motion",
            "neural_policy": (
                "real PI0.5 MPS contact-physics actions; current checkpoint stalls"
            ),
            "studio_leader": (
                "read-only leader and simulated joint-control proof; no completed contact grasp"
            ),
            "physical_follower_commanded": False,
        },
    }
    output_path = (REPO_ROOT / args.output_json).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _requirement(passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"status": "pass" if passed else "fail", "evidence": evidence}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch_json(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=5.0) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _last_nonempty_lines(value: str, count: int) -> list[str]:
    return [line for line in value.splitlines() if line.strip()][-count:]


if __name__ == "__main__":
    raise SystemExit(main())

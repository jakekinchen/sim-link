#!/usr/bin/env python3
"""Materialize immutable T20.18 branch episodes with branch-rendered observations."""

from __future__ import annotations

import hashlib
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.robot_lab.run_t20_18_state_fork_recovery import _run_branch
from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.t20_18_state_fork_recovery import (
    verify_recovery_episode_package_gate,
    verify_recovery_gate,
)


SOURCE_GATE = Path("configurations/robot_lab/t20_18_state_fork_recovery_gate.json")
PACKAGE_ROOT = Path("outputs/robot_lab/t20_18_recovery_episode_package")
GATE_PATH = Path("configurations/robot_lab/t20_18_recovery_episode_package_gate.json")
_FALSE_FIELDS = (
    "optimizer_training",
    "dataset_mixture_frozen",
    "simulation_training_ready",
    "simulation_policy_accepted",
    "physical_transfer_ready",
    "promotion_eligible",
    "physical_actuation",
    "external_compute_started",
    "brev_compute_started",
)


def main() -> int:
    source_gate = load_strict_json(REPO_ROOT / SOURCE_GATE)
    recovery = verify_recovery_gate(source_gate, repo_root=REPO_ROOT)
    package_root = REPO_ROOT / PACKAGE_ROOT
    gate_path = REPO_ROOT / GATE_PATH
    if package_root.exists() or gate_path.exists():
        raise FileExistsError("T20.18 recovery episode package already exists")
    package_root.mkdir(parents=True, exist_ok=False)
    parents = {row["parent_snapshot_id"]: row for row in recovery["parents"]}
    entries = []
    total_frames = total_images = 0
    outcomes: Counter[str] = Counter()
    for branch in recovery["branches"]:
        parent = parents[branch["parent_snapshot_id"]]
        image_root = package_root / "images" / branch["branch_id"]
        trace = _run_branch(
            parent,
            branch["perturbation"],
            branch["measured_actions"],
            capture_dir=image_root,
            include_frames=True,
        )
        if trace["frame_records_sha256"] != branch["trace_summary"]["frame_records_sha256"]:
            raise ValueError("T20.18 episode replay core trace drifted")
        if trace["final_integration_state_sha256"] != branch["trace_summary"]["final_integration_state_sha256"]:
            raise ValueError("T20.18 episode replay final state drifted")
        if trace["observed_result"] != branch["observed_result"]:
            raise ValueError("T20.18 episode replay result drifted")
        episode = sign_payload(
            {
                "schema_version": "scenesmith.t20_18_recovery_episode.v1",
                "task_id": "T20.18",
                "branch_id": branch["branch_id"],
                "parent_snapshot_id": branch["parent_snapshot_id"],
                "phase_role": branch["phase_role"],
                "generation_reason": branch["generation_reason"],
                "perturbation": branch["perturbation"],
                "action_provenance": branch["action_provenance"],
                "action_source_record_ids": branch["action_source_record_ids"],
                "measured_actions": branch["measured_actions"],
                "actions_padded": False,
                "actions_inferred": False,
                "frame_count": trace["frame_count"],
                "episode_frame_records_sha256": trace["episode_frame_records_sha256"],
                "frames": trace["frames"],
                "observed_result": branch["observed_result"],
                "outcome_class": branch["outcome_class"],
                "recovery_training_candidate": True,
                **{field: False for field in _FALSE_FIELDS},
            }
        )
        episode_path = package_root / "episodes" / f"{branch['branch_id']}.json"
        dump_canonical_json(episode_path, episode)
        image_count = sum(len(frame["actor_observation_images"]) for frame in trace["frames"])
        entries.append(
            {
                "branch_id": branch["branch_id"],
                "path": episode_path.relative_to(REPO_ROOT).as_posix(),
                "file_sha256": _sha_file(episode_path),
                "identity_sha256": episode["identity_sha256"],
                "frame_count": trace["frame_count"],
                "image_count": image_count,
                "outcome_class": branch["outcome_class"],
            }
        )
        total_frames += trace["frame_count"]
        total_images += image_count
        outcomes[branch["outcome_class"]] += 1
    source_artifact = REPO_ROOT / source_gate["artifact_path"]
    package = sign_payload(
        {
            "schema_version": "scenesmith.t20_18_recovery_episode_package.v1",
            "task_id": "T20.18",
            "source_recovery_artifact": {
                "path": source_artifact.relative_to(REPO_ROOT).as_posix(),
                "file_sha256": _sha_file(source_artifact),
                "identity_sha256": recovery["identity_sha256"],
            },
            "episode_count": len(entries),
            "frame_count": total_frames,
            "image_count": total_images,
            "outcome_class_counts": dict(sorted(outcomes.items())),
            "episodes": entries,
            "actions_padded": False,
            "actions_inferred": False,
            "recovery_training_candidate": True,
            **{field: False for field in _FALSE_FIELDS},
        }
    )
    manifest_path = package_root / "manifest.json"
    dump_canonical_json(manifest_path, package)
    gate = sign_payload(
        {
            "schema_version": "scenesmith.t20_18_recovery_episode_package_gate.v1",
            "task_id": "T20.18",
            "package_manifest_path": manifest_path.relative_to(REPO_ROOT).as_posix(),
            "package_manifest_file_sha256": _sha_file(manifest_path),
            "package_manifest_identity_sha256": package["identity_sha256"],
            "episode_count": len(entries),
            "frame_count": total_frames,
            "image_count": total_images,
            "outcome_class_counts": dict(sorted(outcomes.items())),
            "actions_padded": False,
            "actions_inferred": False,
            "recovery_training_candidate": True,
            **{field: False for field in _FALSE_FIELDS},
            "authority_granted": ["t20_18_recovery_episode_package_generated"],
            "authority_not_granted": [
                "optimizer_training",
                "dataset_mixture_frozen",
                "simulation_training_ready",
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )
    dump_canonical_json(gate_path, gate)
    verify_recovery_episode_package_gate(gate, repo_root=REPO_ROOT)
    print(package["identity_sha256"], gate["identity_sha256"], total_frames, total_images)
    return 0


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

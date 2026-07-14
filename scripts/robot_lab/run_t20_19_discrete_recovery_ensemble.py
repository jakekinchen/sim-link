#!/usr/bin/env python3
"""Run the fixed T20.19 same-seed discrete recovery-controller ensemble."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.robot_lab.run_t20_18_state_fork_recovery import _run_branch
from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.t20_18_state_fork_recovery import (
    verify_recovery_episode_package_gate,
    verify_recovery_gate,
)
from scenesmith.robot_lab.t20_19_discrete_recovery_ensemble import (
    build_cell_manifest,
    build_scorecard,
    transform_actions,
    verify_cell_manifest,
    verify_scorecard,
)


SOURCE_BRANCH_ID = "35790636312237b8b067a56ba5979e571b970845c309bedf2ab559106bc276d0"
RECOVERY_GATE_PATH = Path("configurations/robot_lab/t20_18_state_fork_recovery_gate.json")
PACKAGE_GATE_PATH = Path("configurations/robot_lab/t20_18_recovery_episode_package_gate.json")
CELL_MANIFEST_PATH = Path("configurations/robot_lab/t20_19_discrete_recovery_cells.json")
EVIDENCE_PATH = Path("outputs/robot_lab/t20_19_discrete_recovery_ensemble.json")
GATE_PATH = Path("configurations/robot_lab/t20_19_discrete_recovery_scorecard_gate.json")
_FALSE_FIELDS = (
    "posterior_calibrated",
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
    for path in (CELL_MANIFEST_PATH, EVIDENCE_PATH, GATE_PATH):
        if (REPO_ROOT / path).exists():
            raise FileExistsError(f"T20.19 immutable output already exists: {path}")
    recovery_gate = load_strict_json(REPO_ROOT / RECOVERY_GATE_PATH)
    package_gate = load_strict_json(REPO_ROOT / PACKAGE_GATE_PATH)
    recovery = verify_recovery_gate(recovery_gate, repo_root=REPO_ROOT)
    package = verify_recovery_episode_package_gate(package_gate, repo_root=REPO_ROOT)
    branch = next((row for row in recovery["branches"] if row["branch_id"] == SOURCE_BRANCH_ID), None)
    if branch is None or branch["outcome_class"] != "recovery":
        raise ValueError("T20.19 source recovery branch is absent or not strict-success")
    parent = next(
        row for row in recovery["parents"] if row["parent_snapshot_id"] == branch["parent_snapshot_id"]
    )
    manifest = build_cell_manifest(
        recovery_manifest_identity_sha256=recovery["identity_sha256"],
        recovery_package_identity_sha256=package["identity_sha256"],
        source_branch_id=SOURCE_BRANCH_ID,
    )
    dump_canonical_json(REPO_ROOT / CELL_MANIFEST_PATH, manifest)
    results = []
    evidence_rows = []
    for cell in manifest["cells"]:
        actions, provenance = transform_actions(
            branch["measured_actions"], cell, parent["applied_action"]
        )
        object_delta = [0.0, 0.0, 0.0]
        friction = 1.0
        if cell["factor"] == "cube_x_offset_m":
            object_delta[0] = float(cell["value"])
        elif cell["factor"] == "cube_y_offset_m":
            object_delta[1] = float(cell["value"])
        elif cell["factor"] == "object_friction_multiplier":
            friction = float(cell["value"])
        first = _run_branch(
            parent,
            branch["perturbation"],
            actions,
            object_position_delta_m=object_delta,
            object_friction_multiplier=friction,
        )
        second = _run_branch(
            parent,
            branch["perturbation"],
            actions,
            object_position_delta_m=object_delta,
            object_friction_multiplier=friction,
        )
        first_sha = _sha(first)
        second_sha = _sha(second)
        result = {
            "cell_id": cell["cell_id"],
            "first_trace_sha256": first_sha,
            "second_trace_sha256": second_sha,
            "simulation_semantic_strict_success": first["observed_result"][
                "simulation_semantic_strict_success"
            ],
            "strict_contact_frame_count": first["observed_result"][
                "strict_contact_frame_count"
            ],
            "maximum_anchor_lift_m": first["observed_result"]["maximum_anchor_lift_m"],
            "terminal_outcome": first["terminal_outcome"],
        }
        results.append(result)
        evidence_rows.append(
            {
                "cell": cell,
                "controller_action_provenance": provenance,
                "controller_action_count": len(actions),
                "controller_actions_sha256": _sha(actions),
                "object_position_delta_m": object_delta,
                "object_friction_multiplier": friction,
                "first_trace_sha256": first_sha,
                "second_trace_sha256": second_sha,
                "trace": first,
            }
        )
    scorecard = build_scorecard(manifest, results)
    evidence = sign_payload(
        {
            "schema_version": "scenesmith.t20_19_discrete_recovery_evidence.v1",
            "task_id": "T20.19",
            "cell_manifest_identity_sha256": manifest["identity_sha256"],
            "source_recovery_manifest_identity_sha256": recovery["identity_sha256"],
            "source_recovery_package_identity_sha256": package["identity_sha256"],
            "source_branch_id": SOURCE_BRANCH_ID,
            "seed": 6,
            "cell_count": len(evidence_rows),
            "cells": evidence_rows,
            "scorecard_identity_sha256": scorecard["identity_sha256"],
            **{field: False for field in _FALSE_FIELDS},
        }
    )
    evidence_path = REPO_ROOT / EVIDENCE_PATH
    dump_canonical_json(evidence_path, evidence)
    gate = sign_payload(
        {
            "schema_version": "scenesmith.t20_19_discrete_recovery_scorecard_gate.v1",
            "task_id": "T20.19",
            "cell_manifest_ref": {
                "path": CELL_MANIFEST_PATH.as_posix(),
                "file_sha256": _sha_file(REPO_ROOT / CELL_MANIFEST_PATH),
                "identity_sha256": manifest["identity_sha256"],
            },
            "evidence_ref": {
                "path": EVIDENCE_PATH.as_posix(),
                "file_sha256": _sha_file(evidence_path),
                "identity_sha256": evidence["identity_sha256"],
            },
            "scorecard": scorecard,
            **{field: False for field in _FALSE_FIELDS},
            "authority_granted": ["t20_19_discrete_recovery_ensemble_verified"],
            "authority_not_granted": [
                "posterior_calibrated",
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
    dump_canonical_json(REPO_ROOT / GATE_PATH, gate)
    _verify_gate(gate)
    print(
        manifest["identity_sha256"],
        evidence["identity_sha256"],
        gate["identity_sha256"],
        scorecard["success_count"],
        scorecard["worst_cell_id"],
    )
    return 0


def _verify_gate(gate: dict[str, Any]) -> None:
    from scenesmith.robot_lab.artifact_contract import verify_signed_payload

    verify_signed_payload(gate, label="T20.19 ensemble gate")
    manifest = load_strict_json(REPO_ROOT / gate["cell_manifest_ref"]["path"])
    evidence = load_strict_json(REPO_ROOT / gate["evidence_ref"]["path"])
    verify_cell_manifest(manifest)
    verify_signed_payload(evidence, label="T20.19 ensemble evidence")
    verify_scorecard(gate["scorecard"], manifest)
    if _sha_file(REPO_ROOT / gate["cell_manifest_ref"]["path"]) != gate["cell_manifest_ref"]["file_sha256"]:
        raise ValueError("T20.19 cell manifest bytes drifted")
    if _sha_file(REPO_ROOT / gate["evidence_ref"]["path"]) != gate["evidence_ref"]["file_sha256"]:
        raise ValueError("T20.19 evidence bytes drifted")
    if evidence["scorecard_identity_sha256"] != gate["scorecard"]["identity_sha256"]:
        raise ValueError("T20.19 scorecard evidence binding drifted")
    for field in _FALSE_FIELDS:
        if gate.get(field) is not False or evidence.get(field) is not False:
            raise ValueError(f"T20.19 ensemble authority flag drifted: {field}")
    if len(evidence["cells"]) != manifest["cell_count"]:
        raise ValueError("T20.19 ensemble evidence cell count drifted")
    for cell, result in zip(evidence["cells"], gate["scorecard"]["results"], strict=True):
        if cell["cell"]["cell_id"] != result["cell_id"]:
            raise ValueError("T20.19 ensemble evidence order drifted")
        if cell["first_trace_sha256"] != cell["second_trace_sha256"]:
            raise ValueError("T20.19 ensemble replay drifted")
        if _sha(cell["trace"]) != cell["first_trace_sha256"]:
            raise ValueError("T20.19 ensemble trace bytes drifted")


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

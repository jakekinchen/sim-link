"""Tracked retention and fresh-checkout rescore contract for T20.36m."""

from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import JOINT_NAMES
from scenesmith.robot_lab.t20_36m_tensor_reproduction import (
    EXPECTED_ACTION_HASHES,
    INFERENCE_SEEDS,
    RESULT_PATH,
    TARGET_HORIZON,
    _matrix,
    load_verified_sources,
    score_action_tensor,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKED_TENSOR_PATH = Path(
    "configurations/robot_lab/t20_36m_decoded_action_tensors.json"
)
RETENTION_RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_36m_tensor_retention_receipt.json"
)
SCHEMA_VERSION = "scenesmith.t20_36m_tensor_retention_receipt.v1"
EXPECTED_TENSOR_IDENTITY = (
    "45a3369d3944b0c7090cc86e571006f0701a7a29d7db37b9e536a3034f62392c"
)
EXPECTED_TENSOR_FILE_SHA256 = (
    "51ce27da27f255a154da2e90872f593f0e6847e17b089677016272eef21bbc90"
)
EXPECTED_RESULT_IDENTITY = (
    "4f101f38c87c2a7d8d64aab8956a0da41d036019f8df697ed2d7c6863bbd9532"
)


def build_retention_receipt(
    *,
    tensor_artifact: dict[str, Any],
    result: dict[str, Any],
    frozen_gate: dict[str, Any],
    target: list[list[float]],
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    root = Path(repo_root)
    verify_signed_payload(tensor_artifact, label="T20.36m tracked tensor artifact")
    verify_signed_payload(result, label="T20.36m tracked result")
    verify_signed_payload(frozen_gate, label="T20.36m frozen gate")
    target_matrix = _matrix(target, label="retained target tensor")
    target_sha256 = hashlib.sha256(canonical_json_bytes(target_matrix)).hexdigest()
    if (
        tensor_artifact.get("schema_version")
        != "scenesmith.t20_36m_decoded_action_tensors.v1"
        or tensor_artifact.get("identity_sha256") != EXPECTED_TENSOR_IDENTITY
        or result.get("identity_sha256") != EXPECTED_RESULT_IDENTITY
        or result.get("tensor_artifact_identity_sha256") != EXPECTED_TENSOR_IDENTITY
        or tensor_artifact.get("target_action_sha256") != target_sha256
        or tensor_artifact.get("shape_per_tensor")
        != [TARGET_HORIZON, len(JOINT_NAMES)]
        or tensor_artifact.get("tensor_count") != 10
        or tensor_artifact.get("all_expected_hashes_reproduced") is not True
        or tensor_artifact.get("all_repeats_bit_identical") is not True
    ):
        raise ValueError("T20.36m tracked tensor lineage drifted")
    thresholds = frozen_gate["amended_gate_b_conjunction"][
        "phase_joint_maximum_error_rad"
    ]
    score_summary = []
    rows = tensor_artifact.get("rows")
    if not isinstance(rows, list) or len(rows) != len(INFERENCE_SEEDS):
        raise ValueError("T20.36m tracked tensor seed coverage drifted")
    for index, (seed, expected_hash, row) in enumerate(
        zip(INFERENCE_SEEDS, EXPECTED_ACTION_HASHES, rows, strict=True)
    ):
        first = _matrix(row.get("first"), label="tracked first tensor")
        second = _matrix(row.get("second"), label="tracked second tensor")
        first_hash = hashlib.sha256(canonical_json_bytes(first)).hexdigest()
        second_hash = hashlib.sha256(canonical_json_bytes(second)).hexdigest()
        if (
            row.get("seed_index") != index
            or row.get("inference_seed") != seed
            or first_hash != expected_hash
            or second_hash != expected_hash
            or first != second
        ):
            raise ValueError("T20.36m tracked tensor hash or repeat drifted")
        score = score_action_tensor(
            tensor=first,
            target=target_matrix,
            thresholds=thresholds,
        )
        score_summary.append(
            {
                "seed_index": index,
                "inference_seed": seed,
                "action_chunk_sha256": first_hash,
                "passed": score["passed"],
                "maximum_absolute_error_rad": score[
                    "maximum_absolute_error_rad"
                ],
                "maximum_threshold_ratio": score["maximum_threshold_ratio"],
                "violation_count": score["violation_count"],
            }
        )
    total = sum(row["violation_count"] for row in score_summary)
    if (
        score_summary != result.get("score_summary")
        or total != result.get("total_violation_count")
        or any(row["passed"] for row in score_summary)
        or result.get("amended_gate_b_passed") is not False
    ):
        raise ValueError("T20.36m tracked tensor rescore drifted")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.36m",
            "tracked_tensor_ref": artifact_ref(
                path=TRACKED_TENSOR_PATH,
                payload=tensor_artifact,
                repo_root=root,
            ),
            "tracked_result_ref": artifact_ref(
                path=RESULT_PATH,
                payload=result,
                repo_root=root,
            ),
            "frozen_gate_identity_sha256": frozen_gate["identity_sha256"],
            "target_action_sha256": target_sha256,
            "target_action": target_matrix,
            "rescored_seed_summary": score_summary,
            "rescored_total_violation_count": total,
            "amended_gate_b_passed": False,
            "exact_existing_bytes_preserved": True,
            "model_reconstructed": False,
            "model_inference_rerun": False,
            "score_changed": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "gate_c_authorized": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def write_retention_receipt(
    *, target: list[list[float]], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    tensor = load_strict_json(root / TRACKED_TENSOR_PATH)
    result = load_strict_json(root / RESULT_PATH)
    receipt = build_retention_receipt(
        tensor_artifact=tensor,
        result=result,
        frozen_gate=sources["frozen_gate"],
        target=target,
        repo_root=root,
    )
    dump_canonical_json(root / RETENTION_RECEIPT_PATH, receipt)
    return receipt


def verify_retention_receipt(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    tensor = load_strict_json(root / TRACKED_TENSOR_PATH)
    result = load_strict_json(root / RESULT_PATH)
    receipt = load_strict_json(root / RETENTION_RECEIPT_PATH)
    verify_signed_payload(receipt, label="T20.36m tensor retention receipt")
    if receipt.get("tracked_tensor_ref", {}).get("file_sha256") != EXPECTED_TENSOR_FILE_SHA256:
        raise ValueError("T20.36m tracked tensor bytes drifted")
    expected = build_retention_receipt(
        tensor_artifact=tensor,
        result=result,
        frozen_gate=sources["frozen_gate"],
        target=receipt.get("target_action"),
        repo_root=root,
    )
    if receipt != expected:
        raise ValueError("T20.36m tensor retention receipt drifted")
    return receipt

"""One-use fixed-manifest runner for T20.42/R0 dataset construction."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.experience_compiler import (
    compile_projections,
    verify_compilation,
    write_compilation,
)
from scenesmith.robot_lab.experience_records import (
    CONTRACT_PATH,
    validate_frame_records,
    validate_raw_rollout_record,
)
from scenesmith.robot_lab.experience_window_index import (
    compile_window_index,
    verify_window_index,
    write_window_index,
)
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes
from scenesmith.robot_lab.lerobot_native_episode_manifest import (
    build_lerobot_episode_manifest,
    verify_lerobot_episode_manifest,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    NORMALIZATION_PATH,
    generate_bounded_episode_payload,
    validate_bounded_episode_spec,
)
from scenesmith.robot_lab.t20_17_clean_base_preflight import (
    IMAGE_KEYS,
    JOINT_NAMES,
    _dataset_frame,
    _features,
)
from scenesmith.robot_lab.t20_23_recovery_augmented_preflight import (
    DATASET_MANIFEST_PATH as BASE_DATASET_MANIFEST_PATH,
    DATASET_REPO_ID as BASE_DATASET_REPO_ID,
    DATASET_ROOT as BASE_DATASET_ROOT,
    verify_preflight_sources as verify_base_dataset,
)
from scenesmith.robot_lab.t20_42a_r0_generation_authority import (
    ATTEMPT_PATH,
    BRANCH,
    COMPILER_ROOT,
    LEROBOT_DATASET_ROOT,
    MIXTURE_MANIFEST_PATH,
    OUTPUT_PATHS,
    PERMIT_PATH,
    RAW_STORE_ROOT,
    RESULT_PATH,
    RETENTION_RECEIPT_PATH,
    RUN_ROOT,
    STATISTICS_PATH,
    WINDOW_ROOT,
    build_attempt_marker,
    load_verified_sources,
    verify_permit,
    write_attempt_marker,
)
from scenesmith.robot_lab.t20_42b_r0_materialization import (
    IMPLEMENTATION_SCOPED_PATHS,
    verify_materialized_authority,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_SCHEMA_VERSION = "scenesmith.t20_42_r0_episode_store.v1"
STATISTICS_SCHEMA_VERSION = "scenesmith.t20_42_r0_mean_std_statistics.v1"
MIXTURE_SCHEMA_VERSION = "scenesmith.t20_42_r0_dataset_mixture_manifest.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_42_r0_generation_result.v1"
RETENTION_SCHEMA_VERSION = "scenesmith.t20_42_r0_retention_receipt.v1"
PRE_RUN_ACCEPTANCE_SCHEMA_VERSION = "scenesmith.t20_42b_r0_pre_run_acceptance.v1"
DATASET_REPO_ID = "scenesmith/t20-42-r0-anchor-grasp-train"
DATASET_LABEL = "t20_42/r0_constructed_anchor_grasp_train"
STORE_MANIFEST_PATH = RAW_STORE_ROOT / "store_manifest.json"
DATASET_MANIFEST_PATH = RUN_ROOT / "lerobot_dataset_manifest.json"
PRE_RUN_ACCEPTANCE_PATH = Path(
    "configurations/robot_lab/t20_42b_r0_pre_run_acceptance.json"
)
PRE_RUN_REVIEW_PATH = Path(
    "docs/reviewer-messages/289-accept-t20-42b-r0-pre-run-authority.md"
)
MINIMUM_NEW_TRAINING_SUCCESSES = 64
PROHIBITED_RESULT_FIELDS = (
    "simulation_training_ready",
    "simulation_policy_accepted",
    "model_loaded",
    "model_inference",
    "optimizer_created",
    "optimizer_training",
    "learned_policy_rollout",
    "gate_c_executed",
    "hardware_accessed",
    "camera_accessed",
    "serial_accessed",
    "physical_motion",
    "physical_actuation",
    "network_accessed",
    "external_compute_started",
    "brev_compute_started",
    "physical_transfer_ready",
    "promotion_eligible",
    "r1_activated",
)


def candidate_sequence(
    *, construction_spec: dict[str, Any], permit: dict[str, Any]
) -> list[dict[str, Any]]:
    construction = construction_spec.get("construction")
    if not isinstance(construction, dict):
        raise ValueError("T20.42 R0 construction candidates are missing")
    rows = [
        *construction.get("training_candidates", []),
        *construction.get("fresh_held_out_candidates", []),
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("T20.42 R0 candidate rows are invalid")
    by_id = {row.get("candidate_id"): row for row in rows}
    if len(by_id) != 128 or None in by_id:
        raise ValueError("T20.42 R0 candidate identity set drifted")
    ordered_ids = [
        *permit.get("training_candidate_ids", []),
        *permit.get("fresh_held_out_candidate_ids", []),
    ]
    plan = construction_spec.get("generation_plan", {})
    expected_ids = [
        *plan.get("training_candidate_ids", []),
        *plan.get("fresh_held_out_candidate_ids", []),
    ]
    if len(ordered_ids) != 128 or len(set(ordered_ids)) != 128:
        raise ValueError("T20.42 R0 permit candidate order drifted")
    if ordered_ids != expected_ids:
        raise ValueError("T20.42 R0 permit order drifted from construction plan")
    try:
        ordered = [dict(by_id[identifier]) for identifier in ordered_ids]
    except KeyError as error:
        raise ValueError("T20.42 R0 permit contains an unknown candidate") from error
    if [row["split_role"] for row in ordered[:119]] != ["training_candidate"] * 119 or [
        row["split_role"] for row in ordered[119:]
    ] != ["evaluation_only_fresh_pose_band"] * 9:
        raise ValueError("T20.42 R0 candidate split order drifted")
    for row in ordered:
        validate_bounded_episode_spec(_generation_spec(row))
        if (
            row.get("initial_joint_delta_rad") != [0.0] * 6
            or row.get("physics_parameter_randomization") is not False
            or row.get("unassisted") is not True
            or row.get("strict_v2_required") is not True
        ):
            raise ValueError("T20.42 R0 candidate authority widened")
    return ordered


def build_store_manifest(
    *,
    outcomes: list[dict[str, Any]],
    construction_spec: dict[str, Any],
    permit: dict[str, Any],
) -> dict[str, Any]:
    expected = candidate_sequence(construction_spec=construction_spec, permit=permit)
    expected_ids = [row["candidate_id"] for row in expected]
    if (
        not isinstance(outcomes, list)
        or [row.get("candidate_id") for row in outcomes] != expected_ids
    ):
        raise ValueError("T20.42 R0 outcome order drifted")
    for outcome, candidate in zip(outcomes, expected, strict=True):
        if (
            outcome.get("split_role") != candidate["split_role"]
            or outcome.get("generation_spec") != _generation_spec(candidate)
            or outcome.get("runtime_status") not in {"completed", "runtime_failure"}
            or not isinstance(outcome.get("strict_success"), bool)
        ):
            raise ValueError("T20.42 R0 outcome semantics drifted")
        if outcome["runtime_status"] == "runtime_failure" and (
            outcome["strict_success"] is not False
            or not isinstance(outcome.get("error"), str)
        ):
            raise ValueError("T20.42 R0 runtime failure semantics drifted")
    training_successes = [
        row["candidate_id"]
        for row in outcomes
        if row.get("split_role") == "training_candidate"
        and row.get("strict_success") is True
        and row.get("runtime_status") == "completed"
    ]
    fresh_successes = [
        row["candidate_id"]
        for row in outcomes
        if row.get("split_role") == "evaluation_only_fresh_pose_band"
        and row.get("strict_success") is True
        and row.get("runtime_status") == "completed"
    ]
    payload = {
        "schema_version": STORE_SCHEMA_VERSION,
        "task_id": "T20.42",
        "scope": "one_use_fixed_r0_scripted_expert_episode_store",
        "construction_spec_identity_sha256": construction_spec["identity_sha256"],
        "generation_permit_identity_sha256": permit["identity_sha256"],
        "store_root": RAW_STORE_ROOT.as_posix(),
        "configured_candidate_count": 128,
        "training_candidate_count": 119,
        "fresh_held_out_candidate_count": 9,
        "outcomes": outcomes,
        "completed_episode_count": sum(
            row.get("runtime_status") == "completed" for row in outcomes
        ),
        "runtime_failure_count": sum(
            row.get("runtime_status") == "runtime_failure" for row in outcomes
        ),
        "strict_failure_count": sum(
            row.get("runtime_status") == "completed"
            and row.get("strict_success") is False
            for row in outcomes
        ),
        "admitted_training_candidate_ids": training_successes,
        "new_training_strict_success_count": len(training_successes),
        "fresh_held_out_strict_success_candidate_ids": fresh_successes,
        "fresh_held_out_training_rows": 0,
        "existing_held_out_seeds_referenced_without_regeneration": [6, 7],
        "retry_authorized": False,
        "adaptive_manifest_extension_authorized": False,
        "raw_bytes_rewritten": False,
        **_false_result_fields(),
    }
    return sign_payload(payload)


def verify_store_manifest(
    payload: dict[str, Any],
    *,
    construction_spec: dict[str, Any],
    permit: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.42 R0 episode store")
    outcomes = payload.get("outcomes")
    if not isinstance(outcomes, list):
        raise ValueError("T20.42 R0 store outcomes are missing")
    root = Path(repo_root).resolve()
    contract = load_strict_json(root / CONTRACT_PATH)
    expected_rows = candidate_sequence(
        construction_spec=construction_spec,
        permit=permit,
    )
    for outcome, candidate in zip(outcomes, expected_rows, strict=True):
        if (
            outcome.get("candidate_id") != candidate["candidate_id"]
            or outcome.get("split_role") != candidate["split_role"]
            or outcome.get("generation_spec") != _generation_spec(candidate)
            or outcome.get("runtime_status") not in {"completed", "runtime_failure"}
        ):
            raise ValueError("T20.42 R0 outcome/candidate binding drifted")
        if outcome["runtime_status"] == "runtime_failure":
            if outcome.get("strict_success") is not False or not isinstance(
                outcome.get("error"), str
            ):
                raise ValueError("T20.42 R0 runtime failure accounting drifted")
            continue
        relative = outcome.get("relative_path")
        if not isinstance(relative, str) or Path(relative).name != relative:
            raise ValueError("T20.42 R0 episode relative path is unsafe")
        episode_path = root / RAW_STORE_ROOT / relative
        if not episode_path.is_file() or episode_path.is_symlink():
            raise ValueError("T20.42 R0 episode payload is absent or aliased")
        if _sha_file(episode_path) != outcome.get("episode_file_sha256"):
            raise ValueError("T20.42 R0 episode file hash drifted")
        episode = load_strict_json(episode_path)
        if episode.get("episode_spec") != _generation_spec(candidate):
            raise ValueError("T20.42 R0 episode specification drifted")
        raw = episode.get("raw_rollout")
        validate_raw_rollout_record(raw, contract["source_grasp_artifact_ref"])
        validate_frame_records(episode.get("frames"), raw)
        validate_rendered_keyframes(episode.get("rendered_keyframes"))
        if (
            raw.get("record_identity_sha256")
            != outcome.get("raw_rollout_record_identity_sha256")
            or len(episode.get("frames", [])) != outcome.get("frame_count")
            or episode.get("outcome") != outcome.get("outcome")
            or episode.get("outcome", {}).get("strict_success")
            is not outcome.get("strict_success")
        ):
            raise ValueError("T20.42 R0 episode outcome linkage drifted")
    expected = build_store_manifest(
        outcomes=outcomes,
        construction_spec=construction_spec,
        permit=permit,
    )
    if payload != expected:
        raise ValueError("T20.42 R0 episode store manifest drifted")


def build_statistics_artifact(
    *,
    dataset_stats: dict[str, Any],
    dataset_manifest_ref: dict[str, Any],
    training_episode_count: int,
    training_frame_count: int,
    excluded_candidate_ids: list[str],
) -> dict[str, Any]:
    features = {}
    for key in ("observation.state", "action"):
        source = dataset_stats.get(key)
        if not isinstance(source, dict):
            raise ValueError(f"T20.42 R0 dataset statistics lack {key}")
        values = {}
        for name in ("mean", "std", "count"):
            values[name] = _finite_json_value(source.get(name), label=f"{key} {name}")
        if len(values["mean"]) != 6 or len(values["std"]) != 6:
            raise ValueError(f"T20.42 R0 {key} MEAN_STD dimension drifted")
        if any(value <= 0.0 for value in values["std"]):
            raise ValueError(f"T20.42 R0 {key} standard deviation is nonpositive")
        features[key] = values
    payload = {
        "schema_version": STATISTICS_SCHEMA_VERSION,
        "task_id": "T20.42",
        "normalization": "MEAN_STD",
        "statistics_source": "package_lerobot_dataset_training_rows_only",
        "dataset_manifest_ref": dict(dataset_manifest_ref),
        "training_episode_count": _positive_int(
            training_episode_count, label="training episode count"
        ),
        "training_frame_count": _positive_int(
            training_frame_count, label="training frame count"
        ),
        "features": features,
        "joint_names": list(JOINT_NAMES),
        "excluded_fresh_held_out_candidate_ids": list(excluded_candidate_ids),
        "existing_held_out_seeds_excluded": [6, 7],
        "held_out_values_contributed_to_fit": False,
        **_false_result_fields(),
    }
    return sign_payload(payload)


def build_pre_run_acceptance(
    *, authority_commit: str, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    if (
        not isinstance(authority_commit, str)
        or len(authority_commit) != 40
        or any(character not in "0123456789abcdef" for character in authority_commit)
    ):
        raise ValueError("T20.42b authority commit must be full lowercase hex")
    authority = verify_materialized_authority(repo_root=root)
    reviewer_path = root / PRE_RUN_REVIEW_PATH
    if not reviewer_path.is_file() or reviewer_path.is_symlink():
        raise ValueError("T20.42b pre-run reviewer decision is absent or aliased")
    reviewer_bytes = reviewer_path.read_bytes()
    permit = authority[PERMIT_PATH.as_posix()]
    return sign_payload(
        {
            "schema_version": PRE_RUN_ACCEPTANCE_SCHEMA_VERSION,
            "task_id": "T20.42b",
            "decision": "ACCEPT_ONE_FIXED_T20_42_R0_ATTEMPT",
            "reviewer_decision_id": "289",
            "reviewer_decision_ref": {
                "path": PRE_RUN_REVIEW_PATH.as_posix(),
                "file_sha256": hashlib.sha256(reviewer_bytes).hexdigest(),
                "size_bytes": len(reviewer_bytes),
            },
            "authority_commit": authority_commit,
            "reviewed_implementation_commit": permit["required_source_commit"],
            "generation_permit_identity_sha256": permit["identity_sha256"],
            "authority_artifact_identities": {
                path: payload["identity_sha256"] for path, payload in authority.items()
            },
            "branch": BRANCH,
            "authorized_attempt_count": 1,
            "training_candidate_count": 119,
            "fresh_held_out_candidate_count": 9,
            "valid_from": permit["valid_from"],
            "valid_until": permit["valid_until"],
            "attempt_marker_exists_at_review": False,
            "all_generation_outputs_absent_at_review": True,
            "retry_authorized": False,
            **_false_result_fields(),
        }
    )


def verify_pre_run_acceptance(
    payload: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    require_head_preserved: bool = False,
) -> None:
    root = Path(repo_root).resolve()
    verify_signed_payload(payload, label="T20.42b R0 pre-run acceptance")
    expected = build_pre_run_acceptance(
        authority_commit=payload.get("authority_commit"), repo_root=root
    )
    if payload != expected:
        raise ValueError("T20.42b R0 pre-run acceptance drifted")
    authority_commit = payload["authority_commit"]
    for path in (
        "configurations/robot_lab/t20_42a_r0_owner_authorization.json",
        "configurations/robot_lab/t20_42a_r0_generation_authority_request.json",
        "configurations/robot_lab/t20_42a_r0_generation_authority_decision.json",
        "configurations/robot_lab/t20_42a_r0_generation_runtime_preflight.json",
        "configurations/robot_lab/t20_42a_r0_generation_permit.json",
    ):
        committed = subprocess.run(
            ["git", "-C", str(root), "show", f"{authority_commit}:{path}"],
            capture_output=True,
            check=True,
        ).stdout
        if committed != (root / path).read_bytes():
            raise ValueError(f"T20.42b authority bytes drifted after commit: {path}")
    if require_head_preserved:
        head = _git(root, "rev-parse", "HEAD")
        ancestor = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "merge-base",
                "--is-ancestor",
                authority_commit,
                head,
            ],
            check=False,
        )
        if ancestor.returncode != 0:
            raise ValueError("T20.42b authority commit is not an ancestor of HEAD")
        for path in (PRE_RUN_REVIEW_PATH, PRE_RUN_ACCEPTANCE_PATH):
            committed = subprocess.run(
                ["git", "-C", str(root), "show", f"{head}:{path.as_posix()}"],
                capture_output=True,
                check=True,
            ).stdout
            if committed != (root / path).read_bytes():
                raise ValueError(
                    f"T20.42b pre-run acceptance is not preserved at HEAD: {path}"
                )


def write_pre_run_acceptance(
    *, authority_commit: str, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    payload = build_pre_run_acceptance(
        authority_commit=authority_commit, repo_root=root
    )
    _exclusive_json(root / PRE_RUN_ACCEPTANCE_PATH, payload)
    verify_pre_run_acceptance(payload, repo_root=root)
    return payload


def run_fixed_manifest(
    *,
    started_at: str,
    repo_root: Path = REPO_ROOT,
    episode_generator: Callable[[dict[str, Any]], dict[str, Any]] = (
        generate_bounded_episode_payload
    ),
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    authority = verify_materialized_authority(repo_root=root)
    sources = load_verified_sources(repo_root=root)
    owner = authority["configurations/robot_lab/t20_42a_r0_owner_authorization.json"]
    request = authority[
        "configurations/robot_lab/t20_42a_r0_generation_authority_request.json"
    ]
    decision = authority[
        "configurations/robot_lab/t20_42a_r0_generation_authority_decision.json"
    ]
    preflight = authority[
        "configurations/robot_lab/t20_42a_r0_generation_runtime_preflight.json"
    ]
    permit = authority[PERMIT_PATH.as_posix()]
    acceptance = load_strict_json(root / PRE_RUN_ACCEPTANCE_PATH)
    verify_pre_run_acceptance(acceptance, repo_root=root, require_head_preserved=True)
    verify_permit(
        permit,
        sources=sources,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_preflight=preflight,
    )
    _require_active_time(started_at, owner=owner)
    _require_execution_boundary(root, permit=permit)
    marker = build_attempt_marker(
        permit=permit,
        source_commit=permit["required_source_commit"],
        started_at=started_at,
    )
    write_attempt_marker(marker, permit=permit, repo_root=root)
    RAW_STORE_ROOT_ABSOLUTE = root / RAW_STORE_ROOT
    RAW_STORE_ROOT_ABSOLUTE.mkdir(parents=True, exist_ok=False)
    candidates = candidate_sequence(
        construction_spec=sources["construction_spec"],
        permit=permit,
    )
    outcomes = []
    for candidate in candidates:
        generation_spec = _generation_spec(candidate)
        try:
            episode = episode_generator(generation_spec)
            outcome = _write_episode(
                episode,
                candidate=candidate,
                store_root=RAW_STORE_ROOT_ABSOLUTE,
            )
        except (RuntimeError, ValueError) as error:
            outcome = {
                "candidate_id": candidate["candidate_id"],
                "split_role": candidate["split_role"],
                "generation_spec": generation_spec,
                "runtime_status": "runtime_failure",
                "strict_success": False,
                "error": str(error),
            }
        outcomes.append(outcome)
    store = build_store_manifest(
        outcomes=outcomes,
        construction_spec=sources["construction_spec"],
        permit=permit,
    )
    _exclusive_json(root / STORE_MANIFEST_PATH, store)
    verify_store_manifest(
        store,
        construction_spec=sources["construction_spec"],
        permit=permit,
        repo_root=root,
    )
    compiler, windows = _compile_store(root, store=store)
    success_count = store["new_training_strict_success_count"]
    if success_count < MINIMUM_NEW_TRAINING_SUCCESSES:
        return _write_terminal_negative(
            root,
            marker=marker,
            permit=permit,
            store=store,
            compiler=compiler,
            windows=windows,
        )
    return _materialize_success(
        root,
        marker=marker,
        permit=permit,
        store=store,
        compiler=compiler,
        windows=windows,
    )


def verify_r0_outputs(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    authority = verify_materialized_authority(repo_root=root)
    sources = load_verified_sources(repo_root=root)
    permit = authority[PERMIT_PATH.as_posix()]
    acceptance = load_strict_json(root / PRE_RUN_ACCEPTANCE_PATH)
    verify_pre_run_acceptance(acceptance, repo_root=root, require_head_preserved=True)
    marker = load_strict_json(root / ATTEMPT_PATH)
    from scenesmith.robot_lab.t20_42a_r0_generation_authority import (
        verify_attempt_marker,
    )

    verify_attempt_marker(marker, permit=permit)
    store = load_strict_json(root / STORE_MANIFEST_PATH)
    verify_store_manifest(
        store,
        construction_spec=sources["construction_spec"],
        permit=permit,
        repo_root=root,
    )
    verify_compilation(root / COMPILER_ROOT)
    verify_window_index(root / WINDOW_ROOT, root / COMPILER_ROOT)
    compiler = {
        "manifest": load_strict_json(root / COMPILER_ROOT / "compiler_manifest.json")
    }
    windows = {
        "manifest": load_strict_json(root / WINDOW_ROOT / "window_manifest.json")
    }
    statistics = load_strict_json(root / STATISTICS_PATH)
    mixture = load_strict_json(root / MIXTURE_MANIFEST_PATH)
    result = load_strict_json(root / RESULT_PATH)
    retention = load_strict_json(root / RETENTION_RECEIPT_PATH)
    for label, payload in (
        ("statistics", statistics),
        ("mixture", mixture),
        ("result", result),
        ("retention", retention),
    ):
        verify_signed_payload(payload, label=f"T20.42 R0 {label}")
        for field in PROHIBITED_RESULT_FIELDS:
            if payload.get(field) is not False:
                raise ValueError(f"T20.42 R0 {label} authority escalated: {field}")
    if store["new_training_strict_success_count"] >= MINIMUM_NEW_TRAINING_SUCCESSES:
        base = verify_base_dataset(repo_root=root)
        from lerobot.datasets import LeRobotDataset

        loaded = LeRobotDataset(
            DATASET_REPO_ID,
            root=root / LEROBOT_DATASET_ROOT,
            return_uint8=True,
        )
        native = load_strict_json(root / DATASET_MANIFEST_PATH)
        annotations = _dataset_annotations(
            base_manifest=base["dataset_manifest"], store=store
        )
        verify_lerobot_episode_manifest(
            native,
            loaded,
            dataset_label=DATASET_LABEL,
            episode_annotations=annotations,
        )
        expected_statistics = build_statistics_artifact(
            dataset_stats=loaded.meta.stats,
            dataset_manifest_ref=artifact_ref(
                path=DATASET_MANIFEST_PATH, payload=native, repo_root=root
            ),
            training_episode_count=loaded.meta.total_episodes,
            training_frame_count=loaded.meta.total_frames,
            excluded_candidate_ids=permit["fresh_held_out_candidate_ids"],
        )
        expected_mixture = _build_mixture(
            root,
            store=store,
            base_manifest=base["dataset_manifest"],
            native_manifest=native,
            statistics=statistics,
        )
        status = "verified_success"
    else:
        if (root / LEROBOT_DATASET_ROOT).exists() or (
            root / DATASET_MANIFEST_PATH
        ).exists():
            raise ValueError("T20.42 R0 negative result materialized a dataset")
        expected_statistics, expected_mixture = _build_negative_artifacts(store)
        native = None
        status = "verified_terminal_negative_insufficient_successes"
    if statistics != expected_statistics or mixture != expected_mixture:
        raise ValueError("T20.42 R0 statistics or mixture drifted")
    expected_result = _build_result(
        root,
        status=status,
        marker=marker,
        permit=permit,
        store=store,
        compiler=compiler,
        windows=windows,
        mixture=mixture,
        statistics=statistics,
        native_manifest=native,
    )
    if result != expected_result:
        raise ValueError("T20.42 R0 result drifted")
    expected_retention = _build_retention(root, result=result)
    if retention != expected_retention:
        raise ValueError("T20.42 R0 retention receipt drifted")
    return {
        "result": result,
        "mixture": mixture,
        "statistics": statistics,
        "retention": retention,
        "store": store,
    }


def _compile_store(
    root: Path, *, store: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = load_strict_json(root / CONTRACT_PATH)
    normalization = load_strict_json(root / NORMALIZATION_PATH)
    projections = []
    for row in store["outcomes"]:
        if row["runtime_status"] != "completed":
            continue
        episode = load_strict_json(root / RAW_STORE_ROOT / row["relative_path"])
        projections.append(
            {"raw_rollout": episode["raw_rollout"], "frames": episode["frames"]}
        )
    if not projections:
        raise ValueError("T20.42 R0 has no completed episode to compile")
    result = compile_projections(
        projections,
        source_experience_identity=contract["identity_sha256"],
        source_normalization_identity=normalization["identity_sha256"],
        source_episode_store_manifest_sha256=_sha_file(root / STORE_MANIFEST_PATH),
    )
    compiler = write_compilation(result, root / COMPILER_ROOT)
    verify_compilation(root / COMPILER_ROOT)
    window_result = compile_window_index(root / COMPILER_ROOT)
    windows = write_window_index(window_result, root / WINDOW_ROOT)
    verify_window_index(root / WINDOW_ROOT, root / COMPILER_ROOT)
    return compiler, windows


def _materialize_success(
    root: Path,
    *,
    marker: dict[str, Any],
    permit: dict[str, Any],
    store: dict[str, Any],
    compiler: dict[str, Any],
    windows: dict[str, Any],
) -> dict[str, Any]:
    base = verify_base_dataset(repo_root=root)
    from lerobot.datasets import LeRobotDataset

    target = LeRobotDataset.create(
        repo_id=DATASET_REPO_ID,
        fps=30,
        root=root / LEROBOT_DATASET_ROOT,
        robot_type="so101_follower",
        features=_features(),
        use_videos=False,
        image_writer_processes=0,
        image_writer_threads=0,
    )
    annotations = []
    base_dataset = LeRobotDataset(
        BASE_DATASET_REPO_ID,
        root=root / BASE_DATASET_ROOT,
        return_uint8=True,
    )
    base_manifest = base["dataset_manifest"]
    for episode in base_dataset.meta.episodes:
        episode_index = int(episode["episode_index"])
        for index in range(
            int(episode["dataset_from_index"]), int(episode["dataset_to_index"])
        ):
            target.add_frame(_copy_base_frame(base_dataset[index]))
        target.save_episode(parallel_encoding=False)
        source = base_manifest["episodes"][episode_index]
        annotations.append(
            {
                "episode_index": episode_index,
                "raw_rollout_identity_sha256": source["raw_rollout_identity_sha256"],
                "eligible": True,
                "quarantine_reason": None,
            }
        )
    admitted = set(store["admitted_training_candidate_ids"])
    for row in store["outcomes"]:
        if row["candidate_id"] not in admitted:
            continue
        episode = load_strict_json(root / RAW_STORE_ROOT / row["relative_path"])
        for frame in episode["frames"]:
            target.add_frame(_dataset_frame(frame))
        target.save_episode(parallel_encoding=False)
        annotations.append(
            {
                "episode_index": len(annotations),
                "raw_rollout_identity_sha256": row[
                    "raw_rollout_record_identity_sha256"
                ],
                "eligible": True,
                "quarantine_reason": None,
            }
        )
    expected_annotations = _dataset_annotations(
        base_manifest=base_manifest, store=store
    )
    if annotations != expected_annotations:
        raise ValueError("T20.42 R0 dataset annotation order drifted")
    target.finalize()
    loaded = LeRobotDataset(
        DATASET_REPO_ID,
        root=root / LEROBOT_DATASET_ROOT,
        return_uint8=True,
    )
    native_manifest = build_lerobot_episode_manifest(
        loaded,
        dataset_label=DATASET_LABEL,
        episode_annotations=annotations,
    )
    _exclusive_json(root / DATASET_MANIFEST_PATH, native_manifest)
    verify_lerobot_episode_manifest(
        native_manifest,
        loaded,
        dataset_label=DATASET_LABEL,
        episode_annotations=annotations,
    )
    native_ref = artifact_ref(
        path=DATASET_MANIFEST_PATH,
        payload=native_manifest,
        repo_root=root,
    )
    statistics = build_statistics_artifact(
        dataset_stats=loaded.meta.stats,
        dataset_manifest_ref=native_ref,
        training_episode_count=loaded.meta.total_episodes,
        training_frame_count=loaded.meta.total_frames,
        excluded_candidate_ids=permit["fresh_held_out_candidate_ids"],
    )
    _exclusive_json(root / STATISTICS_PATH, statistics)
    mixture = _build_mixture(
        root,
        store=store,
        base_manifest=base_manifest,
        native_manifest=native_manifest,
        statistics=statistics,
    )
    _exclusive_json(root / MIXTURE_MANIFEST_PATH, mixture)
    result = _build_result(
        root,
        status="verified_success",
        marker=marker,
        permit=permit,
        store=store,
        compiler=compiler,
        windows=windows,
        mixture=mixture,
        statistics=statistics,
        native_manifest=native_manifest,
    )
    _exclusive_json(root / RESULT_PATH, result)
    retention = _build_retention(root, result=result)
    _exclusive_json(root / RETENTION_RECEIPT_PATH, retention)
    return {
        "result": result,
        "mixture": mixture,
        "statistics": statistics,
        "retention": retention,
    }


def _write_terminal_negative(
    root: Path,
    *,
    marker: dict[str, Any],
    permit: dict[str, Any],
    store: dict[str, Any],
    compiler: dict[str, Any],
    windows: dict[str, Any],
) -> dict[str, Any]:
    statistics, mixture = _build_negative_artifacts(store)
    _exclusive_json(root / STATISTICS_PATH, statistics)
    _exclusive_json(root / MIXTURE_MANIFEST_PATH, mixture)
    result = _build_result(
        root,
        status="verified_terminal_negative_insufficient_successes",
        marker=marker,
        permit=permit,
        store=store,
        compiler=compiler,
        windows=windows,
        mixture=mixture,
        statistics=statistics,
        native_manifest=None,
    )
    _exclusive_json(root / RESULT_PATH, result)
    retention = _build_retention(root, result=result)
    _exclusive_json(root / RETENTION_RECEIPT_PATH, retention)
    return {
        "result": result,
        "mixture": mixture,
        "statistics": statistics,
        "retention": retention,
    }


def _build_negative_artifacts(
    store: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    statistics = sign_payload(
        {
            "schema_version": STATISTICS_SCHEMA_VERSION,
            "task_id": "T20.42",
            "normalization": "MEAN_STD",
            "materialized": False,
            "reason": "minimum_new_training_strict_successes_not_reached",
            "new_training_strict_success_count": store[
                "new_training_strict_success_count"
            ],
            "required_count": MINIMUM_NEW_TRAINING_SUCCESSES,
            "held_out_values_contributed_to_fit": False,
            **_false_result_fields(),
        }
    )
    mixture = sign_payload(
        {
            "schema_version": MIXTURE_SCHEMA_VERSION,
            "task_id": "T20.42",
            "materialized": False,
            "reason": "minimum_new_training_strict_successes_not_reached",
            "base_episode_count": 10,
            "new_training_strict_success_count": store[
                "new_training_strict_success_count"
            ],
            "fresh_held_out_training_rows": 0,
            **_false_result_fields(),
        }
    )
    return statistics, mixture


def _build_mixture(
    root: Path,
    *,
    store: dict[str, Any],
    base_manifest: dict[str, Any],
    native_manifest: dict[str, Any],
    statistics: dict[str, Any],
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": MIXTURE_SCHEMA_VERSION,
            "task_id": "T20.42",
            "materialized": True,
            "base_dataset_manifest_ref": artifact_ref(
                path=BASE_DATASET_MANIFEST_PATH,
                payload=base_manifest,
                repo_root=root,
            ),
            "r0_episode_store_ref": artifact_ref(
                path=STORE_MANIFEST_PATH,
                payload=store,
                repo_root=root,
            ),
            "r0_lerobot_dataset_manifest_ref": artifact_ref(
                path=DATASET_MANIFEST_PATH,
                payload=native_manifest,
                repo_root=root,
            ),
            "statistics_ref": _prospective_ref(STATISTICS_PATH, statistics),
            "base_episode_count": 10,
            "base_included_exactly_once": True,
            "base_raw_rollout_identities": [
                row["raw_rollout_identity_sha256"] for row in base_manifest["episodes"]
            ],
            "new_training_candidate_ids": store["admitted_training_candidate_ids"],
            "new_training_strict_success_count": store[
                "new_training_strict_success_count"
            ],
            "fresh_held_out_candidate_ids": [
                row["candidate_id"]
                for row in store["outcomes"]
                if row["split_role"] == "evaluation_only_fresh_pose_band"
            ],
            "fresh_held_out_training_rows": 0,
            "existing_held_out_seeds": [6, 7],
            "existing_held_out_training_rows": 0,
            "normalization": "MEAN_STD",
            "statistics_source": "frozen_training_split_only",
            "dataset_repo_id": DATASET_REPO_ID,
            "dataset_root": LEROBOT_DATASET_ROOT.as_posix(),
            "training_episode_count": native_manifest["episode_count"],
            "training_frame_count": native_manifest["dataset"]["total_frames"],
            **_false_result_fields(),
        }
    )


def _build_result(
    root: Path,
    *,
    status: str,
    marker: dict[str, Any],
    permit: dict[str, Any],
    store: dict[str, Any],
    compiler: dict[str, Any],
    windows: dict[str, Any],
    mixture: dict[str, Any],
    statistics: dict[str, Any],
    native_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": "T20.42",
        "status": status,
        "attempt_marker_identity_sha256": marker["identity_sha256"],
        "generation_permit_identity_sha256": permit["identity_sha256"],
        "episode_store_ref": artifact_ref(
            path=STORE_MANIFEST_PATH, payload=store, repo_root=root
        ),
        "compiler_manifest_file_sha256": _sha_file(
            root / COMPILER_ROOT / "compiler_manifest.json"
        ),
        "window_manifest_file_sha256": _sha_file(
            root / WINDOW_ROOT / "window_manifest.json"
        ),
        "compiler_frame_count": compiler["manifest"]["frame_count"],
        "compiler_segment_count": compiler["manifest"]["segment_count"],
        "window_count": windows["manifest"]["window_count"],
        "configured_candidate_count": 128,
        "completed_episode_count": store["completed_episode_count"],
        "runtime_failure_count": store["runtime_failure_count"],
        "strict_failure_count": store["strict_failure_count"],
        "new_training_strict_success_count": store["new_training_strict_success_count"],
        "fresh_held_out_strict_success_count": len(
            store["fresh_held_out_strict_success_candidate_ids"]
        ),
        "minimum_new_training_strict_successes": MINIMUM_NEW_TRAINING_SUCCESSES,
        "dataset_materialized": native_manifest is not None,
        "dataset_manifest_ref": (
            artifact_ref(
                path=DATASET_MANIFEST_PATH,
                payload=native_manifest,
                repo_root=root,
            )
            if native_manifest is not None
            else None
        ),
        "mixture_manifest_ref": _prospective_ref(MIXTURE_MANIFEST_PATH, mixture),
        "statistics_ref": _prospective_ref(STATISTICS_PATH, statistics),
        "attempt_count": 1,
        "retry_authorized": False,
        **_false_result_fields(),
    }
    return sign_payload(payload)


def _build_retention(root: Path, *, result: dict[str, Any]) -> dict[str, Any]:
    trees = {}
    for label, path in (
        ("raw_store", RAW_STORE_ROOT),
        ("compiler", COMPILER_ROOT),
        ("windows", WINDOW_ROOT),
        ("lerobot_dataset", LEROBOT_DATASET_ROOT),
    ):
        absolute = root / path
        trees[label] = _tree_identity(absolute) if absolute.exists() else None
    return sign_payload(
        {
            "schema_version": RETENTION_SCHEMA_VERSION,
            "task_id": "T20.42",
            "result_ref": _prospective_ref(RESULT_PATH, result),
            "local_output_trees": trees,
            "large_outputs_tracked_in_git": False,
            "compact_evidence_tracked_in_git": True,
            "raw_outputs_rewritten": False,
            **_false_result_fields(),
        }
    )


def _write_episode(
    episode: dict[str, Any], *, candidate: dict[str, Any], store_root: Path
) -> dict[str, Any]:
    if episode.get("episode_spec") != _generation_spec(candidate):
        raise ValueError("T20.42 R0 generated episode spec drifted")
    data = json.dumps(episode, indent=2, sort_keys=True, allow_nan=False) + "\n"
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    relative = f"{digest}.json"
    _exclusive_text(store_root / relative, data)
    outcome = episode.get("outcome")
    if not isinstance(outcome, dict) or not isinstance(
        outcome.get("strict_success"), bool
    ):
        raise ValueError("T20.42 R0 generated outcome is invalid")
    return {
        "candidate_id": candidate["candidate_id"],
        "split_role": candidate["split_role"],
        "generation_spec": _generation_spec(candidate),
        "runtime_status": "completed",
        "strict_success": outcome["strict_success"],
        "relative_path": relative,
        "episode_file_sha256": digest,
        "raw_rollout_record_identity_sha256": episode["raw_rollout"][
            "record_identity_sha256"
        ],
        "frame_count": len(episode["frames"]),
        "outcome": outcome,
    }


def _copy_base_frame(sample: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    frame = {
        "task": sample["task"],
        "observation.state": sample["observation.state"]
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32),
        "action": sample["action"].detach().cpu().numpy().astype(np.float32),
    }
    for key in IMAGE_KEYS.values():
        image = sample[key].detach().cpu().numpy()
        if image.shape != (3, 256, 256):
            raise ValueError("T20.42 R0 base image shape drifted")
        frame[key] = (
            np.rint(image.transpose(1, 2, 0) * 255.0).clip(0, 255).astype(np.uint8)
        )
    return frame


def _dataset_annotations(
    *, base_manifest: dict[str, Any], store: dict[str, Any]
) -> list[dict[str, Any]]:
    annotations = [
        {
            "episode_index": index,
            "raw_rollout_identity_sha256": row["raw_rollout_identity_sha256"],
            "eligible": True,
            "quarantine_reason": None,
        }
        for index, row in enumerate(base_manifest["episodes"])
    ]
    admitted = set(store["admitted_training_candidate_ids"])
    for row in store["outcomes"]:
        if row["candidate_id"] not in admitted:
            continue
        annotations.append(
            {
                "episode_index": len(annotations),
                "raw_rollout_identity_sha256": row[
                    "raw_rollout_record_identity_sha256"
                ],
                "eligible": True,
                "quarantine_reason": None,
            }
        )
    return annotations


def _require_execution_boundary(root: Path, *, permit: dict[str, Any]) -> None:
    head = _git(root, "rev-parse", "HEAD")
    required = permit["required_source_commit"]
    if _git(root, "branch", "--show-current") != BRANCH:
        raise ValueError("T20.42 R0 execution branch drifted")
    source_ancestor = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", required, head],
        check=False,
    )
    if source_ancestor.returncode != 0:
        raise ValueError("T20.42 R0 reviewed source is not an ancestor of HEAD")
    origin_ancestor = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "merge-base",
            "--is-ancestor",
            head,
            f"refs/remotes/origin/{BRANCH}",
        ],
        check=False,
    )
    if origin_ancestor.returncode != 0:
        raise ValueError("T20.42 R0 execution HEAD is absent from origin")
    scoped_diff = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--quiet",
            required,
            head,
            "--",
            *[path.as_posix() for path in IMPLEMENTATION_SCOPED_PATHS],
        ],
        check=False,
    )
    if scoped_diff.returncode != 0:
        raise ValueError("T20.42 R0 reviewed implementation changed after authority")
    dirty = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *[path.as_posix() for path in IMPLEMENTATION_SCOPED_PATHS],
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        raise ValueError("T20.42 R0 scoped implementation tree is dirty")
    for path in OUTPUT_PATHS:
        if os.path.lexists(root / path) or _path_or_parent_symlink(root, path):
            raise FileExistsError(
                f"T20.42 R0 output path is present or aliased: {path}"
            )


def _require_active_time(value: str, *, owner: dict[str, Any]) -> None:
    now = datetime.fromisoformat(value)
    start = datetime.fromisoformat(owner["valid_from"])
    stop = datetime.fromisoformat(owner["valid_until"])
    if now.tzinfo is None or now.utcoffset() is None or now < start or now > stop:
        raise ValueError("T20.42 R0 owner authority is inactive")


def _generation_spec(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": candidate["seed"],
        "planar_offset_m": list(candidate["planar_offset_m"]),
        "yaw_offset_rad": candidate["yaw_offset_rad"],
    }


def _tree_identity(root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.is_symlink():
            raise ValueError(f"T20.42 R0 retained tree contains alias: {path}")
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha_file(path),
            }
        )
    return {
        "root": root.relative_to(REPO_ROOT).as_posix(),
        "file_count": len(files),
        "size_bytes": sum(row["size_bytes"] for row in files),
        "identity_sha256": hashlib.sha256(canonical_json_bytes(files)).hexdigest(),
        "files": files,
    }


def _prospective_ref(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    data = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(data).hexdigest(),
    }


def _finite_json_value(value: Any, *, label: str) -> Any:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, list):
        return [_finite_json_value(item, label=label) for item in value]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.42 R0 {label} contains a non-number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.42 R0 {label} contains a non-finite number")
    return number


def _positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"T20.42 R0 {label} must be positive")
    return value


def _false_result_fields() -> dict[str, bool]:
    return {field: False for field in PROHIBITED_RESULT_FIELDS}


def _exclusive_json(path: Path, payload: dict[str, Any]) -> None:
    _exclusive_text(
        path,
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )


def _exclusive_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _path_or_parent_symlink(root: Path, relative: Path) -> bool:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False

"""Fail-closed contracts for T20.36f ACT decode localization."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (
    ATTEMPT_PATH as SOURCE_ATTEMPT_PATH,
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
    EXPECTED_DEPENDENCY_VERSIONS,
    RESULT_PATH as SOURCE_RESULT_PATH,
    RUN_SUMMARY_PATH as SOURCE_RUN_SUMMARY_PATH,
    RUNTIME_PREFLIGHT_PATH as SOURCE_RUNTIME_PREFLIGHT_PATH,
    TRAINING_PERMIT_PATH as SOURCE_TRAINING_PERMIT_PATH,
    load_verified_spec,
    verify_attempt_marker as verify_source_attempt,
    verify_result as verify_source_result,
    verify_run_summary as verify_source_run,
    verify_runtime_preflight as verify_source_runtime,
    verify_training_permit as verify_source_permit,
)
from scenesmith.robot_lab.t20_36e_simulation_training_authority import (
    verify_authority as verify_source_authority,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36f_act_decode_localization_preflight.json"
)
INFERENCE_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36f_act_decode_localization_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36f_act_decode_localization_result.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_36f_act_decode_localization_run_001")
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
RUNTIME_SCHEMA_VERSION = "scenesmith.t20_36f_act_decode_localization_preflight.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_36f_act_decode_localization_permit.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36f_act_decode_localization_attempt.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36f_act_decode_localization_result.v1"
TASK_ID = "T20.36f"
EXPECTED_SOURCE_RESULT_IDENTITY = (
    "2ea2c2460527ee863275da11a008aa2b75832f08040daf4fd64459c9520769c6"
)
EXPECTED_SOURCE_RUN_IDENTITY = (
    "9911e51c45dad591691502a47d6ea3baa871ca6c3e3b6b549f81bc2af4423478"
)
EXPECTED_CHECKPOINT_IDENTITY = (
    "01b5713472ae6113ea55b265cbeb02042f3be2b473178a366a6b996e1b75dd21"
)
EXPECTED_FINAL_EVALUATION_IDENTITY = (
    "16d868b0d75163e64534983617c0d505410fb002d23c61dd3ca352567fc5a48a"
)
EXPECTED_FINAL_ACTION_HASH = (
    "ecaa2e4ccd5c34bcac5ecebfaed00e3a421b710c066f73b155f393773fd721e0"
)
EXPECTED_FINAL_OBJECTIVE = 0.07610613852739334
EXPECTED_CHECKPOINT_TREE = [
    {
        "path": "config.json",
        "sha256": "a54498c853555b9e51a4efe9ac8d67d72dc650b4a11ca01979c27068cf0e646a",
        "size_bytes": 1684,
    },
    {
        "path": "model.safetensors",
        "sha256": "336c32951ee327b8ff23d7e2f2b8601127c8efe1480263b9f0cb00e1ebc2ea6c",
        "size_bytes": 45251096,
    },
]
JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]
TIME_REGIONS = [
    {"label": "steps_0_9", "start": 0, "stop": 10},
    {"label": "steps_10_19", "start": 10, "stop": 20},
    {"label": "steps_20_29", "start": 20, "stop": 30},
    {"label": "steps_30_39", "start": 30, "stop": 40},
    {"label": "steps_40_49", "start": 40, "stop": 50},
]
PHYSICAL_THRESHOLD_RAD = 0.05
OBJECTIVE_TOLERANCE = 1e-7
DIRECT_QUEUE_TOLERANCE = 1e-7
MINIMUM_FREE_DISK_BYTES = 2 * 1024 * 1024 * 1024


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = load_verified_spec(repo_root=root)
    source_authority = verify_source_authority(repo_root=root)
    authority_identity = source_authority["decision"]["identity_sha256"]
    runtime = load_strict_json(root / SOURCE_RUNTIME_PREFLIGHT_PATH)
    verify_source_runtime(
        runtime, spec=spec, authority_identity=authority_identity
    )
    permit = load_strict_json(root / SOURCE_TRAINING_PERMIT_PATH)
    verify_source_permit(
        permit,
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime,
    )
    attempt = load_strict_json(root / SOURCE_ATTEMPT_PATH)
    verify_source_attempt(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
    )
    run = load_strict_json(root / SOURCE_RUN_SUMMARY_PATH)
    verify_source_run(
        run,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
        attempt=attempt,
    )
    result = load_strict_json(root / SOURCE_RESULT_PATH)
    verify_source_result(result, spec=spec, run=run)
    if (
        run["identity_sha256"] != EXPECTED_SOURCE_RUN_IDENTITY
        or result["identity_sha256"] != EXPECTED_SOURCE_RESULT_IDENTITY
        or run["checkpoint_identity_sha256"] != EXPECTED_CHECKPOINT_IDENTITY
        or run["checkpoint_tree"] != EXPECTED_CHECKPOINT_TREE
        or run["evaluations"][-1]["identity_sha256"]
        != EXPECTED_FINAL_EVALUATION_IDENTITY
        or run["evaluations"][-1]["repetitions"][0]["action_chunk_sha256"]
        != EXPECTED_FINAL_ACTION_HASH
        or run["evaluations"][-1]["supervised_objective_mean"]
        != EXPECTED_FINAL_OBJECTIVE
    ):
        raise ValueError("T20.36f frozen source identity drifted")
    return {
        "spec": spec,
        "source_authority": source_authority,
        "source_runtime": runtime,
        "source_permit": permit,
        "source_attempt": attempt,
        "source_run": run,
        "source_result": result,
    }


def build_runtime_preflight(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    python_major_minor: list[int],
    dependency_versions: dict[str, str],
    mps_available: bool,
    lerobot_stack_identity_sha256: str,
    checkpoint_tree: list[dict[str, Any]],
    free_disk_bytes: int,
    source_commit: str,
    remote_source_commit: str,
    attempt_exists: bool,
    result_exists: bool,
) -> dict[str, Any]:
    _verify_sources(sources)
    _sha(authority_identity, "authority identity")
    _sha(lerobot_stack_identity_sha256, "LeRobot stack identity")
    _commit(source_commit, "source commit")
    _commit(remote_source_commit, "remote source commit")
    if (
        python_major_minor != [3, 12]
        or dependency_versions != EXPECTED_DEPENDENCY_VERSIONS
        or mps_available is not True
        or checkpoint_tree != EXPECTED_CHECKPOINT_TREE
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < MINIMUM_FREE_DISK_BYTES
        or source_commit != remote_source_commit
        or attempt_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.36f runtime preflight failed closed")
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "source_result_identity_sha256": EXPECTED_SOURCE_RESULT_IDENTITY,
            "source_run_identity_sha256": EXPECTED_SOURCE_RUN_IDENTITY,
            "source_checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
            "authority_decision_identity_sha256": authority_identity,
            "python_major_minor": python_major_minor,
            "dependency_versions": dict(dependency_versions),
            "mps_available": True,
            "lerobot_stack_identity_sha256": lerobot_stack_identity_sha256,
            "checkpoint_tree": checkpoint_tree,
            "checkpoint_bytes_hashed": True,
            "checkpoint_tensor_read": False,
            "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
            "free_disk_bytes": free_disk_bytes,
            "source_commit": source_commit,
            "remote_source_commit": remote_source_commit,
            "remote_source_commit_matches": True,
            "attempt_exists": False,
            "result_exists": False,
            "network_accessed": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
) -> None:
    verify_signed_payload(payload, label="T20.36f runtime preflight")
    expected = build_runtime_preflight(
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=payload.get("python_major_minor"),
        dependency_versions=payload.get("dependency_versions"),
        mps_available=payload.get("mps_available"),
        lerobot_stack_identity_sha256=payload.get(
            "lerobot_stack_identity_sha256"
        ),
        checkpoint_tree=payload.get("checkpoint_tree"),
        free_disk_bytes=payload.get("free_disk_bytes"),
        source_commit=payload.get("source_commit"),
        remote_source_commit=payload.get("remote_source_commit"),
        attempt_exists=payload.get("attempt_exists"),
        result_exists=payload.get("result_exists"),
    )
    if payload != expected:
        raise ValueError("T20.36f runtime preflight drifted")


def build_inference_permit(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    verify_runtime_preflight(
        runtime_preflight,
        sources=sources,
        authority_identity=authority_identity,
    )
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "source_result_identity_sha256": EXPECTED_SOURCE_RESULT_IDENTITY,
            "source_checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime_preflight[
                "identity_sha256"
            ],
            "required_source_commit": runtime_preflight["source_commit"],
            "authorized_attempt_count": 1,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "attempt_marker_path": str(ATTEMPT_PATH),
            "marker_must_precede_checkpoint_tensor_read": True,
            "local_execution_eligible_after_remote_preservation": True,
            "optimizer_created": False,
            "optimizer_training": False,
            "training_retry": False,
            "policy_track_selected": False,
            "smolvla_entry_authorized": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_inference_permit(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36f inference permit")
    expected = build_inference_permit(
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36f inference permit drifted")


def build_attempt_marker(
    *, permit: dict[str, Any], authority_identity: str, source_commit: str
) -> dict[str, Any]:
    verify_signed_payload(permit, label="T20.36f inference permit")
    _sha(authority_identity, "authority identity")
    _commit(source_commit, "attempt source commit")
    if (
        permit.get("authority_decision_identity_sha256") != authority_identity
        or permit.get("authorized_attempt_count") != 1
        or permit.get("authorized_actions")
        != ["simulation_model_load", "simulation_model_inference"]
        or permit.get("marker_must_precede_checkpoint_tensor_read") is not True
    ):
        raise ValueError("T20.36f attempt permit drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "source_result_identity_sha256": EXPECTED_SOURCE_RESULT_IDENTITY,
            "source_checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
            "authority_decision_identity_sha256": authority_identity,
            "inference_permit_identity_sha256": permit["identity_sha256"],
            "source_commit": source_commit,
            "attempt_number": 1,
            "created_before_checkpoint_tensor_read": True,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
        }
    )


def verify_attempt_marker(
    payload: dict[str, Any], *, permit: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.36f attempt marker")
    expected = build_attempt_marker(
        permit=permit,
        authority_identity=authority_identity,
        source_commit=payload.get("source_commit"),
    )
    if payload != expected:
        raise ValueError("T20.36f attempt marker drifted")


def build_result(
    *,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    reproduced_objective: float,
    repetition_action_hashes: list[str],
    direct_action_hash: str,
    direct_queue_maximum_error_rad: float,
    normalized_per_joint: list[dict[str, Any]],
    physical_per_joint: list[dict[str, Any]],
    time_regions: list[dict[str, Any]],
    maximum_error: dict[str, Any],
) -> dict[str, Any]:
    verify_signed_payload(permit, label="T20.36f inference permit")
    verify_signed_payload(attempt, label="T20.36f attempt marker")
    objective = _nonnegative(reproduced_objective, "objective")
    objective_matches = abs(objective - EXPECTED_FINAL_OBJECTIVE) <= OBJECTIVE_TOLERANCE
    if (
        not isinstance(repetition_action_hashes, list)
        or len(repetition_action_hashes) != 5
    ):
        raise ValueError("T20.36f repetition coverage drifted")
    hashes = [_sha(value, "repetition action") for value in repetition_action_hashes]
    direct_hash = _sha(direct_action_hash, "direct action")
    direct_queue = _nonnegative(
        direct_queue_maximum_error_rad, "direct queue error"
    )
    normalized = _joint_rows(normalized_per_joint, physical=False)
    physical = _joint_rows(physical_per_joint, physical=True)
    regions = _time_rows(time_regions)
    maximum = _maximum_error(maximum_error)
    computed_maximum = max(row["maximum_absolute_error"] for row in physical)
    exceedance_count = sum(row["threshold_exceedance_count"] for row in physical)
    maximum_joint = max(
        physical, key=lambda row: row["maximum_absolute_error"]
    )
    maximum_region = next(
        row
        for row in regions
        if row["start_timestep"]
        <= maximum["timestep"]
        < row["stop_timestep_exclusive"]
    )
    if (
        not objective_matches
        or set(hashes) != {EXPECTED_FINAL_ACTION_HASH}
        or direct_hash != EXPECTED_FINAL_ACTION_HASH
        or direct_queue > DIRECT_QUEUE_TOLERANCE
        or abs(computed_maximum - maximum["absolute_error_rad"]) > 1e-12
        or maximum["joint_name"] != maximum_joint["joint_name"]
        or maximum["timestep"] != maximum_joint["maximum_error_timestep"]
        or abs(
            maximum["absolute_error_rad"]
            - abs(maximum["predicted_action"] - maximum["target_action"])
        )
        > 1e-12
        or abs(
            maximum_region["maximum_absolute_error_rad"]
            - maximum["absolute_error_rad"]
        )
        > 1e-12
        or sum(row["threshold_exceedance_count"] for row in regions)
        != exceedance_count
    ):
        raise ValueError("T20.36f reproduced evidence is contradictory")
    physical_mean = sum(row["mean_absolute_error"] for row in physical) / 6.0
    concentration = (
        "localized_physical_outlier"
        if physical_mean <= PHYSICAL_THRESHOLD_RAD and exceedance_count <= 10
        else "distributed_physical_error"
    )
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "source_result_identity_sha256": EXPECTED_SOURCE_RESULT_IDENTITY,
            "source_run_identity_sha256": EXPECTED_SOURCE_RUN_IDENTITY,
            "source_checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
            "source_final_evaluation_identity_sha256": (
                EXPECTED_FINAL_EVALUATION_IDENTITY
            ),
            "inference_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "reproduced_objective": objective,
            "source_final_objective": EXPECTED_FINAL_OBJECTIVE,
            "objective_reproduced_within_tolerance": True,
            "repetition_action_hashes": hashes,
            "direct_action_hash": direct_hash,
            "source_action_hash": EXPECTED_FINAL_ACTION_HASH,
            "all_action_hashes_reproduced": True,
            "direct_queue_maximum_error_rad": direct_queue,
            "direct_queue_consistent": True,
            "normalized_per_joint": normalized,
            "physical_per_joint": physical,
            "time_regions": regions,
            "maximum_error": maximum,
            "physical_mean_absolute_error_rad": physical_mean,
            "physical_threshold_rad": PHYSICAL_THRESHOLD_RAD,
            "threshold_exceedance_count": exceedance_count,
            "error_concentration": concentration,
            "decision": "act_decode_localization_verified",
            "optimizer_created": False,
            "optimizer_training": False,
            "training_retry": False,
            "policy_track_selected": False,
            "smolvla_entry_authorized": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_result(
    payload: dict[str, Any], *, permit: dict[str, Any], attempt: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36f localization result")
    expected = build_result(
        permit=permit,
        attempt=attempt,
        reproduced_objective=payload.get("reproduced_objective"),
        repetition_action_hashes=payload.get("repetition_action_hashes"),
        direct_action_hash=payload.get("direct_action_hash"),
        direct_queue_maximum_error_rad=payload.get(
            "direct_queue_maximum_error_rad"
        ),
        normalized_per_joint=payload.get("normalized_per_joint"),
        physical_per_joint=payload.get("physical_per_joint"),
        time_regions=payload.get("time_regions"),
        maximum_error=payload.get("maximum_error"),
    )
    if payload != expected:
        raise ValueError("T20.36f localization result drifted")


def checkpoint_tree(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rows.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "size_bytes": path.stat().st_size,
                }
            )
    return rows


def _verify_sources(sources: dict[str, Any]) -> None:
    if (
        not isinstance(sources, dict)
        or sources.get("source_result", {}).get("identity_sha256")
        != EXPECTED_SOURCE_RESULT_IDENTITY
        or sources.get("source_run", {}).get("identity_sha256")
        != EXPECTED_SOURCE_RUN_IDENTITY
    ):
        raise ValueError("T20.36f sources drifted")


def _joint_rows(values: Any, *, physical: bool) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) != 6:
        raise ValueError("T20.36f per-joint coverage drifted")
    rows = []
    for index, row in enumerate(values):
        if not isinstance(row, dict) or row.get("joint_name") != JOINT_NAMES[index]:
            raise ValueError("T20.36f per-joint order drifted")
        normalized = {
            "joint_name": JOINT_NAMES[index],
            "mean_absolute_error": _nonnegative(
                row.get("mean_absolute_error"), "joint mean"
            ),
            "maximum_absolute_error": _nonnegative(
                row.get("maximum_absolute_error"), "joint maximum"
            ),
            "maximum_error_timestep": _index(
                row.get("maximum_error_timestep"), 50, "joint maximum timestep"
            ),
        }
        if physical:
            count = row.get("threshold_exceedance_count")
            if (
                isinstance(count, bool)
                or not isinstance(count, int)
                or not 0 <= count <= 50
            ):
                raise ValueError("T20.36f joint exceedance count drifted")
            normalized["threshold_exceedance_count"] = count
        rows.append(normalized)
    return rows


def _time_rows(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) != len(TIME_REGIONS):
        raise ValueError("T20.36f time-region coverage drifted")
    rows = []
    for expected, row in zip(TIME_REGIONS, values, strict=True):
        if not isinstance(row, dict) or row.get("label") != expected["label"]:
            raise ValueError("T20.36f time-region order drifted")
        count = row.get("threshold_exceedance_count")
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or not 0 <= count <= 60
        ):
            raise ValueError("T20.36f time-region exceedance count drifted")
        rows.append(
            {
                "label": expected["label"],
                "start_timestep": expected["start"],
                "stop_timestep_exclusive": expected["stop"],
                "mean_absolute_error_rad": _nonnegative(
                    row.get("mean_absolute_error_rad"), "time-region mean"
                ),
                "maximum_absolute_error_rad": _nonnegative(
                    row.get("maximum_absolute_error_rad"), "time-region maximum"
                ),
                "threshold_exceedance_count": count,
            }
        )
    return rows


def _maximum_error(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("joint_name") not in JOINT_NAMES:
        raise ValueError("T20.36f maximum-error joint drifted")
    return {
        "joint_name": value["joint_name"],
        "joint_index": JOINT_NAMES.index(value["joint_name"]),
        "timestep": _index(value.get("timestep"), 50, "maximum timestep"),
        "predicted_action": _finite(value.get("predicted_action"), "predicted action"),
        "target_action": _finite(value.get("target_action"), "target action"),
        "absolute_error_rad": _nonnegative(
            value.get("absolute_error_rad"), "maximum physical error"
        ),
    }


def _index(value: Any, bound: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < bound:
        raise ValueError(f"T20.36f {label} drifted")
    return value


def _nonnegative(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number < 0:
        raise ValueError(f"T20.36f {label} must be nonnegative")
    return number


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36f {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.36f {label} must be finite")
    return number


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36f {label} is not a lowercase SHA-256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36f {label} is not a full Git commit")
    return value

"""Frozen consequence Gate B amendment and retained-evidence scorer."""

from __future__ import annotations

import hashlib
import json
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_artifact_ref,
    verify_signed_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T20.36l"
OWNER_SCHEMA_VERSION = "scenesmith.t20_36l_owner_decision.v1"
SPEC_SCHEMA_VERSION = "scenesmith.t20_36l_frozen_consequence_gate.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36l_retained_candidate_scoring.v1"
OWNER_DECISION_PATH = Path(
    "configurations/robot_lab/t20_36l_owner_gate_b_amendment_decision.json"
)
SPEC_PATH = Path("configurations/robot_lab/t20_36l_frozen_consequence_gate.json")
RESULT_PATH = Path("configurations/robot_lab/t20_36l_retained_candidate_scoring.json")
CALIBRATION_PATH = Path(
    "configurations/robot_lab/t20_36k_consequence_gate_design.json"
)
HISTORICAL_GATE_PATH = Path(
    "configurations/robot_lab/t20_36d_exact_act_gate_b_control_spec.json"
)
ACT_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36e_exact_act_gate_b_control_result.json"
)
ACT_LOCALIZATION_PATH = Path(
    "configurations/robot_lab/t20_36f_act_decode_localization_result.json"
)
ACT_RUN_PATH = Path(
    "outputs/robot_lab/t20_36e_exact_act_gate_b_control_run_001/run_summary.json"
)
SMOLVLA_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36j_exact_smolvla_gate_b_result.json"
)
SMOLVLA_RUN_PATH = Path(
    "outputs/robot_lab/t20_36j_exact_smolvla_gate_b/run_summary.json"
)
REVIEWER_PATH = Path(
    "docs/reviewer-messages/261-verify-t20-36k-consequence-calibration.md"
)
CALIBRATION_IMPLEMENTATION_COMMIT = "fbdb0aad4f268268ae567836fc69866c97e528b1"
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
TARGET_HORIZON = 50
REACH_STOP_EXCLUSIVE = 32
OBJECTIVE_RATIO_THRESHOLD = 0.1
UNIFORM_REPORT_ONLY_THRESHOLD_RAD = 0.05
OWNER_STATEMENT = "Proceed. I authorize all of this."
OWNER_AUTHORIZED_SCOPE = [
    "freeze_candidate_independent_consequence_thresholds",
    "retain_uniform_metric_as_report_only",
    "score_existing_act_and_smolvla_evidence",
    "route_pass_only_to_separate_gate_c_authority",
]
OWNER_AUTHORITY_NOT_GRANTED = [
    "threshold_fit_to_candidate_errors",
    "model_load",
    "model_inference",
    "optimizer",
    "new_decode",
    "gate_c_execution",
    "policy_acceptance",
    "physical_actuation",
    "external_compute",
    "brev_compute",
]


def freeze_reach_grasp_thresholds(calibration: dict[str, Any]) -> dict[str, dict[str, float]]:
    verify_signed_payload(calibration, label="T20.36k calibration")
    if calibration.get("schema_version") != "scenesmith.t20_36k_consequence_gate_design.v1":
        raise ValueError("T20.36l calibration schema drifted")
    if calibration.get("candidate_evidence_context_only", {}).get(
        "used_for_threshold_derivation"
    ) is not False:
        raise ValueError("T20.36l thresholds cannot be candidate-derived")
    rows = calibration.get("derived_phase_joint_threshold_design")
    if not isinstance(rows, list):
        raise ValueError("T20.36l calibration threshold rows are missing")
    thresholds: dict[str, dict[str, float]] = {"reach": {}, "grasp": {}}
    for row in rows:
        group = row.get("phase_group")
        joint = row.get("joint_name")
        if group not in thresholds:
            continue
        if joint not in JOINT_NAMES or joint in thresholds[group]:
            raise ValueError("T20.36l calibration threshold row drifted")
        value = row.get("amendment_ceiling_rad")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("T20.36l threshold must be finite")
        numeric = float(value)
        if not math.isfinite(numeric) or numeric <= 0.0:
            raise ValueError("T20.36l threshold must be positive and finite")
        thresholds[group][str(joint)] = numeric
    if any(set(row) != set(JOINT_NAMES) for row in thresholds.values()):
        raise ValueError("T20.36l reach/grasp threshold matrix is incomplete")
    return thresholds


def score_act_retained_witness(
    *,
    localization: dict[str, Any],
    run: dict[str, Any],
    thresholds: dict[str, dict[str, float]],
) -> dict[str, Any]:
    verify_signed_payload(localization, label="T20.36f ACT localization")
    verify_signed_payload(run, label="T20.36e ACT run")
    final = _final_evaluation(run, label="ACT")
    rows = localization.get("physical_per_joint")
    if not isinstance(rows, list) or len(rows) != len(JOINT_NAMES):
        raise ValueError("T20.36l ACT localization rows are missing")
    witnesses = []
    seen = set()
    for row in rows:
        joint = row.get("joint_name")
        if joint not in JOINT_NAMES or joint in seen:
            raise ValueError("T20.36l ACT localization joint drifted")
        seen.add(joint)
        timestep = _timestep(row.get("maximum_error_timestep"))
        error = _finite_nonnegative(
            row.get("maximum_absolute_error"), label="ACT maximum joint error"
        )
        phase_group = _phase_group(timestep)
        threshold = thresholds[phase_group][joint]
        if error > threshold:
            witnesses.append(
                {
                    "joint_name": joint,
                    "timestep": timestep,
                    "phase_group": phase_group,
                    "maximum_absolute_error_rad": error,
                    "frozen_threshold_rad": threshold,
                    "excess_rad": error - threshold,
                }
            )
    deterministic = final.get("all_repetition_action_hashes_match") is True
    ratio = _finite_nonnegative(
        final.get("final_to_baseline_supervised_objective_ratio"),
        label="ACT objective ratio",
    )
    objective_pass = ratio <= OBJECTIVE_RATIO_THRESHOLD
    if not witnesses:
        action_status = "indeterminate_fail_closed_aggregate_witness_insufficient"
    else:
        action_status = "fail_with_retained_witness"
    return {
        "candidate": "ACT",
        "source_final_evaluation_identity_sha256": final["identity_sha256"],
        "objective_ratio": ratio,
        "objective_ratio_passed": objective_pass,
        "deterministic_repetitions_passed": deterministic,
        "strict_uniform_maximum_error_rad": final["maximum_absolute_error_rad"],
        "strict_uniform_threshold_rad": UNIFORM_REPORT_ONLY_THRESHOLD_RAD,
        "strict_uniform_gate_passed": final["all_actions_within_threshold"],
        "strict_uniform_status": "reported_original_negative_unchanged",
        "retained_decoded_tensor_available": False,
        "aggregate_witness_sufficient_to_fail": bool(witnesses),
        "failure_witnesses": witnesses,
        "action_gate_status": action_status,
        "amended_gate_b_passed": False,
        "gate_c_route_open": False,
    }


def score_smolvla_retained_evidence(
    *,
    run: dict[str, Any],
    decoded_tensor: Any,
) -> dict[str, Any]:
    verify_signed_payload(run, label="T20.36j SmolVLA run")
    if decoded_tensor is not None:
        raise ValueError("T20.36l may score retained tensors only; new decode is prohibited")
    final = _final_evaluation(run, label="SmolVLA")
    ratio = _finite_nonnegative(
        final.get("final_to_baseline_supervised_objective_ratio"),
        label="SmolVLA objective ratio",
    )
    rows = final.get("inference_rows")
    if not isinstance(rows, list) or len(rows) != 5:
        raise ValueError("T20.36l SmolVLA inference summaries are missing")
    deterministic = final.get("all_seed_repeats_deterministic") is True and all(
        row.get("action_hashes_match") is True
        and row.get("repeat_maximum_absolute_difference_rad") == 0.0
        for row in rows
    )
    return {
        "candidate": "SmolVLA",
        "source_final_evaluation_identity_sha256": final["identity_sha256"],
        "objective_ratio": ratio,
        "objective_ratio_passed": ratio <= OBJECTIVE_RATIO_THRESHOLD,
        "deterministic_repetitions_passed": deterministic,
        "strict_uniform_maximum_error_rad": final["maximum_absolute_error_rad"],
        "strict_uniform_threshold_rad": UNIFORM_REPORT_ONLY_THRESHOLD_RAD,
        "strict_uniform_gate_passed": final["all_actions_within_threshold"],
        "strict_uniform_status": "reported_original_negative_unchanged",
        "retained_decoded_tensor_available": False,
        "retained_action_hashes": [row["first_action_chunk_sha256"] for row in rows],
        "action_gate_status": "indeterminate_fail_closed_missing_retained_tensor",
        "amended_gate_b_passed": False,
        "gate_c_route_open": False,
    }


def build_artifacts(*, repo_root: Path = REPO_ROOT) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    sources = _load_sources(repo_root)
    thresholds = freeze_reach_grasp_thresholds(sources["calibration"])
    owner = _build_owner_decision(sources["calibration"])
    spec = _build_spec(
        sources=sources,
        owner=owner,
        thresholds=thresholds,
        repo_root=repo_root,
    )
    act_score = score_act_retained_witness(
        localization=sources["act_localization"],
        run=sources["act_run"],
        thresholds=thresholds,
    )
    smolvla_score = score_smolvla_retained_evidence(
        run=sources["smolvla_run"], decoded_tensor=None
    )
    result = _build_result(
        sources=sources,
        spec=spec,
        act_score=act_score,
        smolvla_score=smolvla_score,
        repo_root=repo_root,
    )
    return owner, spec, result


def verify_owner_decision(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36l owner decision")
    if payload.get("schema_version") != OWNER_SCHEMA_VERSION:
        raise ValueError("T20.36l owner decision schema drifted")
    if payload.get("owner_statement_record") != OWNER_STATEMENT:
        raise ValueError("T20.36l owner statement drifted")
    if (
        payload.get("authorization_timing")
        != "pre_registered_before_t20_36j_result_and_reaffirmed_after"
        or payload.get("authorized_scope") != OWNER_AUTHORIZED_SCOPE
        or payload.get("authority_not_granted") != OWNER_AUTHORITY_NOT_GRANTED
    ):
        raise ValueError("T20.36l owner decision scope drifted")
    if payload.get("source_calibration_identity_sha256") != load_strict_json(
        REPO_ROOT / CALIBRATION_PATH
    ).get("identity_sha256"):
        raise ValueError("T20.36l owner decision calibration binding drifted")
    _verify_false_authority(payload)


def verify_spec(payload: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> None:
    verify_signed_payload(payload, label="T20.36l frozen gate spec")
    if payload.get("schema_version") != SPEC_SCHEMA_VERSION:
        raise ValueError("T20.36l frozen gate spec schema drifted")
    if payload.get("decision") != "frozen_consequence_gate_non_authorizing":
        raise ValueError("T20.36l frozen gate decision drifted")
    sources = _load_sources(repo_root)
    owner = load_strict_json(repo_root / OWNER_DECISION_PATH)
    verify_owner_decision(owner)
    expected_refs = _source_refs(sources, repo_root=repo_root)
    expected_refs["owner_decision"] = artifact_ref(
        path=OWNER_DECISION_PATH, payload=owner, repo_root=repo_root
    )
    for name, expected in expected_refs.items():
        verify_artifact_ref(payload.get("source_refs", {}).get(name), expected, label=name)
    thresholds = freeze_reach_grasp_thresholds(sources["calibration"])
    expected_reviewer = {
        "id": "261",
        "path": str(REVIEWER_PATH),
        "file_sha256": hashlib.sha256((repo_root / REVIEWER_PATH).read_bytes()).hexdigest(),
    }
    if (
        payload.get("calibration_implementation_commit")
        != CALIBRATION_IMPLEMENTATION_COMMIT
        or payload.get("reviewer_decision") != expected_reviewer
        or payload.get("target_horizon") != TARGET_HORIZON
        or payload.get("timestep_phase_mapping")
        != {
            "reach": [0, REACH_STOP_EXCLUSIVE],
            "grasp": [REACH_STOP_EXCLUSIVE, TARGET_HORIZON],
        }
    ):
        raise ValueError("T20.36l frozen source or phase binding drifted")
    gate = payload.get("amended_gate_b_conjunction", {})
    if gate.get("phase_joint_maximum_error_rad") != thresholds:
        raise ValueError("T20.36l frozen thresholds drifted")
    if (
        gate.get("maximum_objective_ratio") != OBJECTIVE_RATIO_THRESHOLD
        or gate.get("all_fixed_repetitions_must_be_deterministic") is not True
        or gate.get("all_timesteps_and_joints_must_pass") is not True
        or gate.get("gate_c_behavior_still_required") is not True
    ):
        raise ValueError("T20.36l amended conjunction drifted")
    derivation = payload.get("threshold_derivation", {})
    if derivation != {
        "source": "t20_36k_model_free_symmetric_consequence_calibration",
        "candidate_outputs_are_inputs": False,
        "thresholds_frozen_before_retained_candidate_scoring": True,
    }:
        raise ValueError("T20.36l candidate outputs cannot derive thresholds")
    report = payload.get("strict_uniform_report_only", {})
    if (
        report.get("maximum_absolute_error_rad")
        != UNIFORM_REPORT_ONLY_THRESHOLD_RAD
        or report.get("historical_results_relabelled") is not False
    ):
        raise ValueError("T20.36l strict uniform reporting drifted")
    _verify_false_authority(payload)


def verify_result(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any] | None = None,
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.36l retained scoring")
    if payload.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise ValueError("T20.36l retained scoring schema drifted")
    if spec is None:
        spec = load_strict_json(repo_root / SPEC_PATH)
    verify_spec(spec, repo_root=repo_root)
    verify_artifact_ref(
        payload.get("spec_ref"),
        artifact_ref(path=SPEC_PATH, payload=spec, repo_root=repo_root),
        label="T20.36l frozen spec",
    )
    sources = _load_sources(repo_root)
    for name, expected in _candidate_refs(sources, repo_root=repo_root).items():
        verify_artifact_ref(payload.get("candidate_source_refs", {}).get(name), expected, label=name)
    thresholds = spec["amended_gate_b_conjunction"]["phase_joint_maximum_error_rad"]
    expected_act = score_act_retained_witness(
        localization=sources["act_localization"],
        run=sources["act_run"],
        thresholds=thresholds,
    )
    expected_smol = score_smolvla_retained_evidence(
        run=sources["smolvla_run"], decoded_tensor=None
    )
    if payload.get("candidate_scores") != {
        "ACT": expected_act,
        "SmolVLA": expected_smol,
    }:
        raise ValueError("T20.36l retained candidate scores drifted")
    inventory = payload.get("retained_tensor_inventory", {})
    if inventory != _retained_tensor_inventory(sources, repo_root=repo_root):
        raise ValueError("T20.36l retained tensor inventory drifted")
    if payload.get("decision") != "no_amended_gate_b_pass_smolvla_tensor_missing":
        raise ValueError("T20.36l fail-closed decision drifted")
    if (
        payload.get("historical_results_relabelled") is not False
        or payload.get("gate_b_amendment_frozen") is not True
        or payload.get("retained_evidence_scoring_complete") is not True
        or payload.get("smolvla_scoring_complete") is not False
        or payload.get("smolvla_scoring_blocker")
        != "full_50x6_per_seed_decoded_tensors_not_retained"
        or payload.get("new_authority_required")
        != "model_load_and_inference_only_tensor_reproduction"
    ):
        raise ValueError("T20.36l fail-closed disposition drifted")
    _verify_false_authority(payload)


def _build_owner_decision(calibration: dict[str, Any]) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": OWNER_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "owner_statement_record": OWNER_STATEMENT,
            "authorization_timing": "pre_registered_before_t20_36j_result_and_reaffirmed_after",
            "source_calibration_identity_sha256": calibration["identity_sha256"],
            "authorized_scope": OWNER_AUTHORIZED_SCOPE,
            "authority_not_granted": OWNER_AUTHORITY_NOT_GRANTED,
            **_false_authority_fields(),
        }
    )


def _build_spec(
    *,
    sources: dict[str, Any],
    owner: dict[str, Any],
    thresholds: dict[str, dict[str, float]],
    repo_root: Path,
) -> dict[str, Any]:
    refs = _source_refs(sources, repo_root=repo_root)
    refs["owner_decision"] = _pending_artifact_ref(
        path=OWNER_DECISION_PATH, payload=owner
    )
    return sign_payload(
        {
            "schema_version": SPEC_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "decision": "frozen_consequence_gate_non_authorizing",
            "source_refs": refs,
            "calibration_implementation_commit": CALIBRATION_IMPLEMENTATION_COMMIT,
            "reviewer_decision": {
                "id": "261",
                "path": str(REVIEWER_PATH),
                "file_sha256": hashlib.sha256((repo_root / REVIEWER_PATH).read_bytes()).hexdigest(),
            },
            "target_horizon": TARGET_HORIZON,
            "timestep_phase_mapping": {
                "reach": [0, REACH_STOP_EXCLUSIVE],
                "grasp": [REACH_STOP_EXCLUSIVE, TARGET_HORIZON],
            },
            "threshold_derivation": {
                "source": "t20_36k_model_free_symmetric_consequence_calibration",
                "candidate_outputs_are_inputs": False,
                "thresholds_frozen_before_retained_candidate_scoring": True,
            },
            "amended_gate_b_conjunction": {
                "maximum_objective_ratio": OBJECTIVE_RATIO_THRESHOLD,
                "phase_joint_maximum_error_rad": thresholds,
                "all_fixed_repetitions_must_be_deterministic": True,
                "all_timesteps_and_joints_must_pass": True,
                "gate_c_behavior_still_required": True,
            },
            "strict_uniform_report_only": {
                "maximum_absolute_error_rad": UNIFORM_REPORT_ONLY_THRESHOLD_RAD,
                "all_original_negative_results_remain_visible": True,
                "historical_results_relabelled": False,
            },
            **_false_authority_fields(),
        }
    )


def _build_result(
    *,
    sources: dict[str, Any],
    spec: dict[str, Any],
    act_score: dict[str, Any],
    smolvla_score: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "decision": "no_amended_gate_b_pass_smolvla_tensor_missing",
            "spec_ref": _pending_artifact_ref(path=SPEC_PATH, payload=spec),
            "candidate_source_refs": _candidate_refs(sources, repo_root=repo_root),
            "retained_tensor_inventory": _retained_tensor_inventory(
                sources, repo_root=repo_root
            ),
            "candidate_scores": {"ACT": act_score, "SmolVLA": smolvla_score},
            "historical_results_relabelled": False,
            "gate_b_amendment_frozen": True,
            "retained_evidence_scoring_complete": True,
            "smolvla_scoring_complete": False,
            "smolvla_scoring_blocker": "full_50x6_per_seed_decoded_tensors_not_retained",
            "new_authority_required": "model_load_and_inference_only_tensor_reproduction",
            **_false_authority_fields(),
        }
    )


def _load_sources(repo_root: Path) -> dict[str, Any]:
    paths = {
        "calibration": CALIBRATION_PATH,
        "historical_gate": HISTORICAL_GATE_PATH,
        "act_result": ACT_RESULT_PATH,
        "act_localization": ACT_LOCALIZATION_PATH,
        "act_run": ACT_RUN_PATH,
        "smolvla_result": SMOLVLA_RESULT_PATH,
        "smolvla_run": SMOLVLA_RUN_PATH,
    }
    loaded = {name: load_strict_json(repo_root / path) for name, path in paths.items()}
    for name, payload in loaded.items():
        verify_signed_payload(payload, label=f"T20.36l {name}")
    return {**loaded, "paths": paths}


def _source_refs(sources: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    return {
        name: artifact_ref(path=sources["paths"][name], payload=sources[name], repo_root=repo_root)
        for name in ("calibration", "historical_gate")
    }


def _candidate_refs(sources: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    return {
        name: artifact_ref(path=sources["paths"][name], payload=sources[name], repo_root=repo_root)
        for name in (
            "act_result",
            "act_localization",
            "act_run",
            "smolvla_result",
            "smolvla_run",
        )
    }


def _retained_tensor_inventory(
    sources: dict[str, Any], *, repo_root: Path
) -> dict[str, Any]:
    return {
        "ACT": _candidate_inventory(
            run=sources["act_run"], run_path=ACT_RUN_PATH, repo_root=repo_root
        ),
        "SmolVLA": _candidate_inventory(
            run=sources["smolvla_run"], run_path=SMOLVLA_RUN_PATH, repo_root=repo_root
        ),
    }


def _candidate_inventory(
    *, run: dict[str, Any], run_path: Path, repo_root: Path
) -> dict[str, Any]:
    root = (repo_root / run_path).parent
    retained_action_files = sorted(
        str(path.relative_to(repo_root))
        for path in root.rglob("*")
        if path.is_file()
        and (
            path.suffix.lower() in {".npy", ".npz", ".pt", ".pth"}
            or "decoded_action" in path.name.lower()
            or "action_chunk" in path.name.lower()
        )
    )
    embedded_tensors: list[str] = []
    for path in sorted(root.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        embedded_tensors.extend(
            f"{path.relative_to(repo_root)}#{pointer}"
            for pointer in _find_50x6_numeric_matrices(data)
        )
    checkpoint_weights = sorted(
        {
            row["path"]
            for row in run.get("checkpoint_tree", [])
            if row.get("path", "").endswith((".safetensors", ".bin"))
        }
    )
    final = _final_evaluation(run, label="candidate")
    return {
        "run_root": str(root.relative_to(repo_root)),
        "run_summary_file_sha256": hashlib.sha256((repo_root / run_path).read_bytes()).hexdigest(),
        "final_evaluation_keys": sorted(final),
        "retained_decoded_action_tensor_files": retained_action_files,
        "embedded_50x6_numeric_tensor_paths": embedded_tensors,
        "retained_decoded_action_tensor_available": bool(
            retained_action_files or embedded_tensors
        ),
        "checkpoint_weight_files_not_read": checkpoint_weights,
        "model_load_or_inference_performed": False,
    }


def _final_evaluation(run: dict[str, Any], *, label: str) -> dict[str, Any]:
    rows = run.get("evaluations")
    if not isinstance(rows, list) or not rows or not isinstance(rows[-1], dict):
        raise ValueError(f"T20.36l {label} final evaluation is missing")
    return rows[-1]


def _phase_group(timestep: int) -> str:
    return "reach" if timestep < REACH_STOP_EXCLUSIVE else "grasp"


def _timestep(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < TARGET_HORIZON:
        raise ValueError("T20.36l timestep is outside the frozen 50-step target")
    return value


def _finite_nonnegative(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be finite and nonnegative")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return numeric


def _false_authority_fields() -> dict[str, bool]:
    return {
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "new_decode": False,
        "gate_c_authorized": False,
        "gate_c_executed": False,
        "policy_track_selected": False,
        "simulation_policy_accepted": False,
        "promotion_eligible": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "physical_transfer_ready": False,
    }


def _verify_false_authority(payload: dict[str, Any]) -> None:
    for key in _false_authority_fields():
        if payload.get(key) is not False:
            raise ValueError(f"T20.36l must keep {key} false")


def _find_50x6_numeric_matrices(value: Any, pointer: str = "") -> list[str]:
    matches: list[str] = []
    if isinstance(value, list):
        if len(value) == TARGET_HORIZON and all(
            isinstance(row, list)
            and len(row) == len(JOINT_NAMES)
            and all(
                not isinstance(item, bool)
                and isinstance(item, (int, float))
                and math.isfinite(float(item))
                for item in row
            )
            for row in value
        ):
            matches.append(pointer or "/")
        for index, item in enumerate(value):
            matches.extend(_find_50x6_numeric_matrices(item, f"{pointer}/{index}"))
    elif isinstance(value, dict):
        for key, item in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            matches.extend(_find_50x6_numeric_matrices(item, f"{pointer}/{escaped}"))
    return matches


def _pending_artifact_ref(*, path: Path, payload: dict[str, Any]) -> dict[str, str]:
    file_bytes = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    return {
        "path": str(path),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
    }

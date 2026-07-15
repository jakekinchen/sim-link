"""Model-free objective-mass and compatibility audit for T20.35s."""

from __future__ import annotations

import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    INFERENCE_SEEDS,
    MAX_OBJECTIVE_RATIO,
)
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    _equal_with_float_tolerance,
)
from scenesmith.robot_lab.t20_35r_full_path_self_consistency_correction import (
    CORRECTION_EXAMPLE_COUNT,
    RESULT_PATH as T20_35R_RESULT_PATH,
    SPEC_PATH as T20_35R_SPEC_PATH,
    verify_result as verify_t20_35r_result,
    verify_run as verify_t20_35r_run,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_35s_objective_mass_compatibility_audit.json"
)
SCHEMA_VERSION = "scenesmith.t20_35s_objective_mass_compatibility_audit.v1"
EXPECTED_T20_35R_SPEC_IDENTITY = (
    "70be21a274c22d1fc9aaf0920a546b2ac3ab60efd5a3e51e143a485f7b0adfbe"
)
EXPECTED_T20_35R_RUN_IDENTITY = (
    "85826156468f3f5285cbfce66974aeaab99bc23dc6a6f4987d45c84a5d94a9e2"
)
EXPECTED_T20_35R_RESULT_IDENTITY = (
    "52d4c9edcbafc5de24fea6f0f9718068665675ec9728b3511cbcc1d9d93cf363"
)
NUM_INFERENCE_STEPS = 10
LATE_STEP_INDICES = (8, 9)
LATE_OBJECTIVE_MASS_DOMINANCE_THRESHOLD = 0.75
STANDARD_OBJECTIVE_INCREASE_THRESHOLD = 1.10
ABSOLUTE_TOLERANCE = 1e-12


def build_audit(
    *,
    training_spec: dict[str, Any],
    training_run: dict[str, Any],
    training_result: dict[str, Any],
) -> dict[str, Any]:
    for label, payload in (
        ("training spec", training_spec),
        ("training run", training_run),
        ("training result", training_result),
    ):
        verify_signed_payload(payload, label=f"T20.35s {label}")
    authority_identity = training_result.get(
        "authority_decision_identity_sha256"
    )
    verify_t20_35r_run(
        training_run,
        spec=training_spec,
        authority_identity=authority_identity,
    )
    verify_t20_35r_result(
        training_result,
        spec=training_spec,
        run=training_run,
    )
    if (
        training_spec.get("identity_sha256")
        != EXPECTED_T20_35R_SPEC_IDENTITY
        or training_run.get("identity_sha256")
        != EXPECTED_T20_35R_RUN_IDENTITY
        or training_result.get("identity_sha256")
        != EXPECTED_T20_35R_RESULT_IDENTITY
        or training_result.get("run_identity_sha256")
        != training_run.get("identity_sha256")
        or training_result.get("gate_b_passed") is not False
        or training_result.get("selected_next_hypothesis")
        != "full_path_correction_both_fail_route_capacity_or_interference_audit"
    ):
        raise ValueError("T20.35s source identity or route drifted")

    examples = training_spec.get("correction_examples")
    baseline = _finite_vector(
        training_run.get("baseline_objective_by_example"),
        CORRECTION_EXAMPLE_COUNT,
        "baseline objective",
    )
    final = _finite_vector(
        training_run.get("final_objective_by_example"),
        CORRECTION_EXAMPLE_COUNT,
        "final objective",
    )
    expected_pairs = [
        (seed, step)
        for seed in INFERENCE_SEEDS
        for step in range(NUM_INFERENCE_STEPS)
    ]
    if (
        not isinstance(examples, list)
        or len(examples) != CORRECTION_EXAMPLE_COUNT
        or [
            (row.get("inference_seed"), row.get("step_index"))
            for row in examples
            if isinstance(row, dict)
        ]
        != expected_pairs
    ):
        raise ValueError("T20.35s correction example order drifted")

    baseline_total = sum(baseline)
    final_total = sum(final)
    if baseline_total <= 0.0 or final_total < 0.0:
        raise ValueError("T20.35s objective mass is invalid")
    if (
        abs(
            baseline_total / CORRECTION_EXAMPLE_COUNT
            - training_run["baseline_correction_objective_mean"]
        )
        > ABSOLUTE_TOLERANCE
        or abs(
            final_total / CORRECTION_EXAMPLE_COUNT
            - training_run["final_correction_objective_mean"]
        )
        > ABSOLUTE_TOLERANCE
    ):
        raise ValueError("T20.35s objective mean failed exact recomputation")

    by_step = []
    for step_index in range(NUM_INFERENCE_STEPS):
        indices = [seed_index * NUM_INFERENCE_STEPS + step_index for seed_index in range(len(INFERENCE_SEEDS))]
        baseline_values = [baseline[index] for index in indices]
        final_values = [final[index] for index in indices]
        baseline_sum = sum(baseline_values)
        final_sum = sum(final_values)
        by_step.append(
            {
                "step_index": step_index,
                "time": 1.0 - step_index / NUM_INFERENCE_STEPS,
                "example_count": len(indices),
                "baseline_objective_mean": baseline_sum / len(indices),
                "final_objective_mean": final_sum / len(indices),
                "final_to_baseline_objective_ratio": final_sum / baseline_sum,
                "baseline_objective_mass_fraction": baseline_sum / baseline_total,
                "final_objective_mass_fraction": final_sum / final_total,
                "improved_example_count": sum(
                    after < before
                    for before, after in zip(
                        baseline_values, final_values, strict=True
                    )
                ),
            }
        )

    by_seed = []
    for seed_index, seed in enumerate(INFERENCE_SEEDS):
        start = seed_index * NUM_INFERENCE_STEPS
        stop = start + NUM_INFERENCE_STEPS
        baseline_values = baseline[start:stop]
        final_values = final[start:stop]
        baseline_sum = sum(baseline_values)
        final_sum = sum(final_values)
        by_seed.append(
            {
                "inference_seed": seed,
                "example_count": NUM_INFERENCE_STEPS,
                "baseline_objective_mean": baseline_sum / NUM_INFERENCE_STEPS,
                "final_objective_mean": final_sum / NUM_INFERENCE_STEPS,
                "final_to_baseline_objective_ratio": final_sum / baseline_sum,
                "improved_example_count": sum(
                    after < before
                    for before, after in zip(
                        baseline_values, final_values, strict=True
                    )
                ),
            }
        )

    last_two_share = sum(
        by_step[index]["baseline_objective_mass_fraction"]
        for index in LATE_STEP_INDICES
    )
    last_three_share = sum(
        row["baseline_objective_mass_fraction"] for row in by_step[-3:]
    )
    source_standard = _finite(
        training_run.get("baseline_standard_objective_mean"),
        "source standard objective",
    )
    final_standard = _finite(
        training_run.get("final_standard_objective_mean"),
        "final standard objective",
    )
    if source_standard <= 0.0:
        raise ValueError("T20.35s source standard objective must be positive")
    standard_increase = final_standard / source_standard
    original_ratio = final_standard / _finite(
        training_spec.get("source_gate_baseline_objective_mean"),
        "original Gate B baseline",
    )
    if (
        abs(
            original_ratio
            - training_result["final_to_source_gate_baseline_objective_ratio"]
        )
        > ABSOLUTE_TOLERANCE
    ):
        raise ValueError("T20.35s original Gate B ratio drifted")

    late_dominance = (
        last_two_share >= LATE_OBJECTIVE_MASS_DOMINANCE_THRESHOLD
    )
    standard_interference = (
        standard_increase > STANDARD_OBJECTIVE_INCREASE_THRESHOLD
        and original_ratio > MAX_OBJECTIVE_RATIO
    )
    if late_dominance and standard_interference:
        classification = (
            "terminal_objective_mass_dominance_with_standard_interference"
        )
        route = "design_time_normalized_standard_replay_correction"
    elif late_dominance:
        classification = "terminal_objective_mass_dominance_only"
        route = "design_time_normalized_full_path_correction"
    elif standard_interference:
        classification = "standard_objective_interference_only"
        route = "design_standard_replay_compatibility_correction"
    else:
        classification = "distributed_objective_incompatibility"
        route = "audit_per_module_gradient_compatibility"

    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35s",
            "scope": "one_model_free_objective_mass_and_standard_compatibility_audit",
            "t20_35r_spec_identity_sha256": training_spec["identity_sha256"],
            "t20_35r_run_identity_sha256": training_run["identity_sha256"],
            "t20_35r_result_identity_sha256": training_result["identity_sha256"],
            "objective_by_step": by_step,
            "objective_by_seed": by_seed,
            "improved_example_count": sum(
                after < before
                for before, after in zip(baseline, final, strict=True)
            ),
            "correction_example_count": CORRECTION_EXAMPLE_COUNT,
            "last_two_step_baseline_objective_mass_fraction": last_two_share,
            "last_three_step_baseline_objective_mass_fraction": last_three_share,
            "terminal_step_baseline_objective_mass_fraction": by_step[-1][
                "baseline_objective_mass_fraction"
            ],
            "late_objective_mass_dominance_threshold": LATE_OBJECTIVE_MASS_DOMINANCE_THRESHOLD,
            "late_objective_mass_dominance": late_dominance,
            "source_checkpoint_standard_objective_mean": source_standard,
            "final_standard_objective_mean": final_standard,
            "final_to_source_checkpoint_standard_objective_ratio": standard_increase,
            "standard_objective_increase_threshold": STANDARD_OBJECTIVE_INCREASE_THRESHOLD,
            "final_to_original_gate_baseline_objective_ratio": original_ratio,
            "maximum_allowed_original_gate_baseline_objective_ratio": MAX_OBJECTIVE_RATIO,
            "standard_objective_interference": standard_interference,
            "objective_compatibility_classification": classification,
            "gate_b_passed": False,
            "selected_next_hypothesis": route,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_read": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "sampler_mutated": False,
            "action_correction_selected": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_audit(
    payload: dict[str, Any],
    *,
    training_spec: dict[str, Any],
    training_run: dict[str, Any],
    training_result: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.35s objective-mass audit")
    expected = build_audit(
        training_spec=training_spec,
        training_run=training_run,
        training_result=training_result,
    )
    archived = {key: value for key, value in payload.items() if key != "identity_sha256"}
    rebuilt = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(
        archived, rebuilt, absolute_tolerance=1e-15
    ):
        raise ValueError("T20.35s objective-mass audit drifted")


def load_source_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = load_strict_json(root / T20_35R_SPEC_PATH)
    result = load_strict_json(root / T20_35R_RESULT_PATH)
    from scripts.robot_lab.run_t20_35r_full_path_self_consistency_correction import (
        SUMMARY_PATH,
    )

    run = load_strict_json(SUMMARY_PATH)
    verify_t20_35r_run(
        run,
        spec=spec,
        authority_identity=result["authority_decision_identity_sha256"],
    )
    verify_t20_35r_result(result, spec=spec, run=run)
    return {"training_spec": spec, "training_run": run, "training_result": result}


def write_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    audit = build_audit(**sources)
    dump_canonical_json(root / AUDIT_PATH, audit)
    return audit


def verify_audit_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    audit = load_strict_json(root / AUDIT_PATH)
    verify_audit(audit, **sources)
    return audit


def _finite_vector(value: Any, count: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != count:
        raise ValueError(f"T20.35s {label} coverage drifted")
    return [_finite(item, label) for item in value]


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.35s {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.35s {label} must be finite")
    return number

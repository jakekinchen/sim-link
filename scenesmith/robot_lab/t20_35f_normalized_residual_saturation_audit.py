"""Model-free normalized residual and saturation audit for T20.35f."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_coordinates import (
    GRIPPER_RANGE_RAD,
    MUJOCO_BODY_LIMITS_RAD,
    mujoco_to_lerobot,
)
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    INFERENCE_SEEDS,
    MAX_ACTION_ERROR_RAD,
    PERMIT_PATH,
    REPORT_PATH,
    SPEC_PATH,
    verify_evaluation_permit,
    verify_report,
)
from scenesmith.robot_lab.t20_35e_top_two_channel_correction import (
    CORRECTION_PATH,
    verify_correction,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_35f_normalized_residual_saturation_audit.json"
)
T20_35C_SPEC_PATH = Path(
    "configurations/robot_lab/t20_35c_expert_only_training_spec.json"
)
T20_33_SPEC_PATH = Path(
    "configurations/robot_lab/t20_33_one_batch_training_spec.json"
)
DATASET_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_17_lerobot_dataset_manifest.json"
)
DATASET_STATS_PATH = Path(
    "outputs/robot_lab/t20_17_lerobot_training_dataset/meta/stats.json"
)
PI05_CONFIG_SOURCE_PATH = Path(
    "external/lerobot/src/lerobot/policies/pi05/configuration_pi05.py"
)
PI05_NORMALIZER_SOURCE_PATH = Path(
    "external/lerobot/src/lerobot/processor/normalize_processor.py"
)
PI05_MODEL_SOURCE_PATH = Path(
    "external/lerobot/src/lerobot/policies/pi05/modeling_pi05.py"
)
COORDINATE_SOURCE_PATH = Path("scenesmith/robot_lab/so101_coordinates.py")

SCHEMA_VERSION = "scenesmith.t20_35f_normalized_residual_saturation_audit.v1"
EXPECTED_CORRECTION_IDENTITY = (
    "f2a8aa8089467b019310d24152f417d7987de0880d9664f3ef1184818a2ddea3"
)
EXPECTED_REPORT_IDENTITY = (
    "13b08e70a805a8b176b9f9a7c0e37843f7267d7918f82aeb523551e2dadf1fbe"
)
EXPECTED_T20_35D_SPEC_IDENTITY = (
    "b083c59393a0eb9027bb07253357e8c7ec9fb1f240c58118ad8d49fa1067c033"
)
EXPECTED_T20_35C_SPEC_IDENTITY = (
    "6c10a1c7ad1f901c8afd5452669a0f0ca845d9395fa75de8e84139b706e92309"
)
EXPECTED_T20_33_SPEC_IDENTITY = (
    "3fa3098c816b228a6687e952cb8444c77344e49877b17cfc5d1afdc32e6e685a"
)
EXPECTED_DATASET_MANIFEST_IDENTITY = (
    "689516af0ee418b600d51a5ae7cda8a5c49709a6f4e1c3356e18c9d5c708ab29"
)
EXPECTED_DATASET_STATS_FILE_SHA256 = (
    "9c013fde21c80e2dd0d184ac3122f1ce4fd75e662dedef97fd5f6b651376cf4c"
)
EXPECTED_PI05_CONFIG_SOURCE_SHA256 = (
    "a8b80f54ffe98993529d8013b1f8ddde4289a71b5c6a5e41d7346ac7622da6a6"
)
EXPECTED_PI05_NORMALIZER_SOURCE_SHA256 = (
    "e9c4745d44f6f3808a84ed7ee9bc23b99ad930cc14222030e9167d4999da1012"
)
EXPECTED_PI05_MODEL_SOURCE_SHA256 = (
    "b05b6afe70a4a09f2eb610827b9ae09e8b08e43cd748d435e47879344e3fa619"
)
EXPECTED_COORDINATE_SOURCE_SHA256 = (
    "9382e02106741906380eed572959f991382c285cedd08c8d652d0a3375cf843a"
)
SELECTED_CHANNELS = ((4, "wrist_roll"), (5, "gripper"))
SYSTEMATIC_BIAS_FRACTION_THRESHOLD = 0.75
STOCHASTIC_VARIANCE_FRACTION_THRESHOLD = 0.50
DEFAULT_NUM_INFERENCE_STEPS = 10


def build_audit(
    *,
    correction: dict[str, Any],
    report: dict[str, Any],
    action_stats: dict[str, Any],
    source_contract: dict[str, Any],
) -> dict[str, Any]:
    _source_contract(source_contract, correction=correction, report=report)
    selected = _selected_channels(correction)
    target = _matrix(report.get("target_action_chunk"), "target action chunk")
    replayed = _replayed_chunks(report)
    q01, q99, count = _action_quantiles(action_stats)

    target_lerobot = [mujoco_to_lerobot(row) for row in target]
    decoded_lerobot = [
        [mujoco_to_lerobot(row) for row in replay["decoded_action_chunk"]]
        for replay in replayed
    ]
    channel_audits = []
    for joint_index, joint_name, expected_count in selected:
        span = q99[joint_index] - q01[joint_index]
        units_per_rad = (
            180.0 / math.pi
            if joint_index < 5
            else 100.0 / (GRIPPER_RANGE_RAD[1] - GRIPPER_RANGE_RAD[0])
        )
        normalized_units_per_rad = 2.0 * units_per_rad / span
        normalized_gate = MAX_ACTION_ERROR_RAD * normalized_units_per_rad
        target_normalized = [
            _normalize(row[joint_index], q01[joint_index], span)
            for row in target_lerobot
        ]
        decoded_normalized = [
            [
                _normalize(row[joint_index], q01[joint_index], span)
                for row in replay
            ]
            for replay in decoded_lerobot
        ]
        signed_errors = [
            [decoded_normalized[seed][t] - target_normalized[t] for t in range(50)]
            for seed in range(5)
        ]
        absolute_errors = [abs(value) for row in signed_errors for value in row]
        physical_errors = [
            abs(replayed[seed]["decoded_action_chunk"][t][joint_index] - target[t][joint_index])
            for seed in range(5)
            for t in range(50)
        ]
        physical_count = sum(value > MAX_ACTION_ERROR_RAD for value in physical_errors)
        normalized_count = sum(value > normalized_gate for value in absolute_errors)
        if physical_count != expected_count or normalized_count != expected_count:
            raise ValueError("T20.35f selected-channel threshold count drifted")

        outside = [abs(value) > 1.0 for value in target_normalized]
        outside_exceedances = sum(
            abs(signed_errors[seed][t]) > normalized_gate and outside[t]
            for seed in range(5)
            for t in range(50)
        )
        decomposition = _decompose(signed_errors)
        low, high = _physical_bounds(joint_index)
        target_bound_hits = sum(value[joint_index] in (low, high) for value in target)
        decoded_bound_hits = sum(
            replayed[seed]["decoded_action_chunk"][t][joint_index] in (low, high)
            for seed in range(5)
            for t in range(50)
        )
        hard_saturation = target_bound_hits + decoded_bound_hits > 0
        channel_audits.append(
            {
                "joint_index": joint_index,
                "joint_name": joint_name,
                "dataset_statistic_count": count,
                "q01": q01[joint_index],
                "q99": q99[joint_index],
                "quantile_span": span,
                "lerobot_units_per_mujoco_rad": units_per_rad,
                "normalized_units_per_mujoco_rad": normalized_units_per_rad,
                "physical_error_gate_rad": MAX_ACTION_ERROR_RAD,
                "normalized_error_gate": normalized_gate,
                "physical_threshold_exceedance_count": physical_count,
                "normalized_threshold_exceedance_count": normalized_count,
                "target_normalized_minimum": min(target_normalized),
                "target_normalized_maximum": max(target_normalized),
                "target_normalized_maximum_absolute": max(
                    abs(value) for value in target_normalized
                ),
                "target_below_negative_one_count": sum(
                    value < -1.0 for value in target_normalized
                ),
                "target_above_positive_one_count": sum(
                    value > 1.0 for value in target_normalized
                ),
                "target_outside_quantile_range_count": sum(outside),
                "target_outside_quantile_range_fraction": sum(outside) / 50,
                "target_quantile_range_exceeded": any(outside),
                "normalizer_clips_normalized_values": False,
                "target_physical_bound_hit_count": target_bound_hits,
                "decoded_physical_bound_hit_count": decoded_bound_hits,
                "hard_saturation_detected": hard_saturation,
                "normalized_residual_mean_absolute": sum(absolute_errors) / 250,
                "normalized_residual_maximum_absolute": max(absolute_errors),
                "normalized_residual_root_mean_square": math.sqrt(
                    sum(value * value for value in absolute_errors) / 250
                ),
                "threshold_exceedances_on_outside_target_count": outside_exceedances,
                "threshold_exceedances_on_outside_target_fraction": (
                    outside_exceedances / physical_count if physical_count else 0.0
                ),
                "squared_error_decomposition": decomposition,
                "systematic_bias_dominant": decomposition[
                    "systematic_bias_fraction"
                ]
                >= SYSTEMATIC_BIAS_FRACTION_THRESHOLD,
            }
        )

    hard_saturation = any(row["hard_saturation_detected"] for row in channel_audits)
    all_bias_dominant = all(
        row["systematic_bias_dominant"] for row in channel_audits
    )
    any_variance_dominant = any(
        row["squared_error_decomposition"]["seed_variance_fraction"]
        > STOCHASTIC_VARIANCE_FRACTION_THRESHOLD
        for row in channel_audits
    )
    any_quantile_exceeded = any(
        row["target_quantile_range_exceeded"] for row in channel_audits
    )
    if hard_saturation:
        route = "audit_coordinate_output_clipping_before_decoder_change"
    elif any_variance_dominant:
        route = "gate_b_seed_noise_stability_discriminator"
    elif all_bias_dominant:
        route = "gate_b_inference_denoising_cadence_discriminator"
    elif any_quantile_exceeded:
        route = "model_free_action_quantile_coverage_counterfactual"
    else:
        route = "gate_b_output_projection_residual_audit"

    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35f",
            "scope": "model_free_normalized_residual_saturation_and_bias_variance_audit",
            "source_contract": dict(source_contract),
            "normalization_contract": {
                "action_mode": "QUANTILES",
                "normalized_reference_range": [-1.0, 1.0],
                "transform": "2*(lerobot_value-q01)/(q99-q01)-1",
                "normalizer_clips_normalized_values": False,
                "pi05_default_num_inference_steps": DEFAULT_NUM_INFERENCE_STEPS,
                "physical_error_gate_rad": MAX_ACTION_ERROR_RAD,
                "systematic_bias_fraction_threshold": SYSTEMATIC_BIAS_FRACTION_THRESHOLD,
                "stochastic_variance_fraction_threshold": STOCHASTIC_VARIANCE_FRACTION_THRESHOLD,
            },
            "selected_channels": [
                {"joint_index": index, "joint_name": name}
                for index, name in SELECTED_CHANNELS
            ],
            "channel_audits": channel_audits,
            "hard_saturation_detected": hard_saturation,
            "target_quantile_range_exceeded_without_normalizer_clipping": any_quantile_exceeded
            and not hard_saturation,
            "all_selected_channels_systematic_bias_dominant": all_bias_dominant,
            "any_selected_channel_seed_variance_dominant": any_variance_dominant,
            "selected_next_hypothesis": route,
            "source_report_mutated": False,
            "source_correction_mutated": False,
            "dataset_mutated": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_training": False,
            "checkpoint_read": False,
            "checkpoint_mutated": False,
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
    correction: dict[str, Any],
    report: dict[str, Any],
    action_stats: dict[str, Any],
    source_contract: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.35f normalized residual audit")
    expected = build_audit(
        correction=correction,
        report=report,
        action_stats=action_stats,
        source_contract=source_contract,
    )
    if payload != expected:
        raise ValueError("T20.35f normalized residual audit drifted from sources")


def build_live_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = _load_live_sources(Path(repo_root))
    audit = build_audit(
        correction=sources["correction"],
        report=sources["report"],
        action_stats=sources["action_stats"],
        source_contract=sources["source_contract"],
    )
    verify_audit(
        audit,
        correction=sources["correction"],
        report=sources["report"],
        action_stats=sources["action_stats"],
        source_contract=sources["source_contract"],
    )
    return audit


def write_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    audit = build_live_audit(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / AUDIT_PATH, audit)
    return audit


def verify_audit_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = _load_live_sources(Path(repo_root))
    archived = load_strict_json(Path(repo_root) / AUDIT_PATH)
    verify_audit(
        archived,
        correction=sources["correction"],
        report=sources["report"],
        action_stats=sources["action_stats"],
        source_contract=sources["source_contract"],
    )
    return archived


def _load_live_sources(root: Path) -> dict[str, Any]:
    correction = load_strict_json(root / CORRECTION_PATH)
    verify_correction(correction)
    _identity(correction, EXPECTED_CORRECTION_IDENTITY, "T20.35e correction")

    spec = load_strict_json(root / SPEC_PATH)
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    report = load_strict_json(root / REPORT_PATH)
    verify_report(report, spec=spec, permit=permit)
    _identity(spec, EXPECTED_T20_35D_SPEC_IDENTITY, "T20.35d spec")
    _identity(report, EXPECTED_REPORT_IDENTITY, "T20.35d report")
    if correction["source_t20_35d_report_identity_sha256"] != report["identity_sha256"]:
        raise ValueError("T20.35f correction/report linkage drifted")

    t20_35c = load_strict_json(root / T20_35C_SPEC_PATH)
    t20_33 = load_strict_json(root / T20_33_SPEC_PATH)
    dataset_manifest = load_strict_json(root / DATASET_MANIFEST_PATH)
    for label, payload, identity in (
        ("T20.35c spec", t20_35c, EXPECTED_T20_35C_SPEC_IDENTITY),
        ("T20.33 spec", t20_33, EXPECTED_T20_33_SPEC_IDENTITY),
        ("T20.17 dataset manifest", dataset_manifest, EXPECTED_DATASET_MANIFEST_IDENTITY),
    ):
        verify_signed_payload(payload, label=label)
        _identity(payload, identity, label)
    if (
        spec.get("t20_35c_training_spec_identity_sha256")
        != t20_35c["identity_sha256"]
        or t20_35c.get("t20_33_training_spec_identity_sha256")
        != t20_33["identity_sha256"]
        or t20_33.get("dataset_manifest_ref", {}).get("identity_sha256")
        != dataset_manifest["identity_sha256"]
    ):
        raise ValueError("T20.35f training/dataset lineage drifted")

    metadata_rows = dataset_manifest.get("dataset", {}).get("metadata_tree", {}).get("files")
    stats_row = next(
        (
            row
            for row in metadata_rows or []
            if isinstance(row, dict) and row.get("path") == "meta/stats.json"
        ),
        None,
    )
    stats_file_sha = _file_sha256(root / DATASET_STATS_PATH)
    if (
        not isinstance(stats_row, dict)
        or stats_row.get("sha256") != EXPECTED_DATASET_STATS_FILE_SHA256
        or stats_file_sha != EXPECTED_DATASET_STATS_FILE_SHA256
    ):
        raise ValueError("T20.35f dataset action statistics drifted")
    stats_payload = load_strict_json(root / DATASET_STATS_PATH)
    action_stats = stats_payload.get("action")
    if not isinstance(action_stats, dict):
        raise ValueError("T20.35f action statistics are missing")

    source_hashes = {
        "pi05_configuration_source_sha256": _file_sha256(root / PI05_CONFIG_SOURCE_PATH),
        "pi05_normalizer_source_sha256": _file_sha256(root / PI05_NORMALIZER_SOURCE_PATH),
        "pi05_model_source_sha256": _file_sha256(root / PI05_MODEL_SOURCE_PATH),
        "coordinate_source_sha256": _file_sha256(root / COORDINATE_SOURCE_PATH),
    }
    expected_hashes = {
        "pi05_configuration_source_sha256": EXPECTED_PI05_CONFIG_SOURCE_SHA256,
        "pi05_normalizer_source_sha256": EXPECTED_PI05_NORMALIZER_SOURCE_SHA256,
        "pi05_model_source_sha256": EXPECTED_PI05_MODEL_SOURCE_SHA256,
        "coordinate_source_sha256": EXPECTED_COORDINATE_SOURCE_SHA256,
    }
    if source_hashes != expected_hashes:
        raise ValueError("T20.35f pinned normalization/sampler source drifted")

    source_contract = {
        "t20_35e_correction_identity_sha256": correction["identity_sha256"],
        "t20_35d_report_identity_sha256": report["identity_sha256"],
        "t20_35d_spec_identity_sha256": spec["identity_sha256"],
        "t20_35c_training_spec_identity_sha256": t20_35c["identity_sha256"],
        "t20_33_training_spec_identity_sha256": t20_33["identity_sha256"],
        "dataset_manifest_identity_sha256": dataset_manifest["identity_sha256"],
        "dataset_stats_file_sha256": stats_file_sha,
        **source_hashes,
        "action_normalization_mode": "QUANTILES",
        "normalizer_clips_normalized_values": False,
        "pi05_default_num_inference_steps": DEFAULT_NUM_INFERENCE_STEPS,
    }
    return {
        "correction": correction,
        "report": report,
        "action_stats": action_stats,
        "source_contract": source_contract,
    }


def _source_contract(
    value: Any, *, correction: dict[str, Any], report: dict[str, Any]
) -> None:
    if not isinstance(value, dict):
        raise ValueError("T20.35f source contract is missing")
    sha_fields = (
        "t20_35e_correction_identity_sha256",
        "t20_35d_report_identity_sha256",
        "t20_35d_spec_identity_sha256",
        "t20_35c_training_spec_identity_sha256",
        "t20_33_training_spec_identity_sha256",
        "dataset_manifest_identity_sha256",
        "dataset_stats_file_sha256",
        "pi05_configuration_source_sha256",
        "pi05_normalizer_source_sha256",
        "pi05_model_source_sha256",
        "coordinate_source_sha256",
    )
    for field in sha_fields:
        _sha(value.get(field), field)
    if (
        value["t20_35e_correction_identity_sha256"]
        != correction.get("identity_sha256")
        or value["t20_35d_report_identity_sha256"]
        != report.get("identity_sha256")
        or correction.get("source_t20_35d_report_identity_sha256")
        != report.get("identity_sha256")
        or value.get("action_normalization_mode") != "QUANTILES"
        or value.get("normalizer_clips_normalized_values") is not False
        or value.get("pi05_default_num_inference_steps")
        != DEFAULT_NUM_INFERENCE_STEPS
    ):
        raise ValueError("T20.35f source contract drifted")


def _selected_channels(correction: dict[str, Any]) -> list[tuple[int, str, int]]:
    rows = correction.get("top_two_channels")
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("T20.35f selected channels are missing")
    selected = []
    for expected, row in zip(SELECTED_CHANNELS, rows, strict=True):
        if (
            not isinstance(row, dict)
            or row.get("joint_index") != expected[0]
            or row.get("joint_name") != expected[1]
            or isinstance(row.get("threshold_exceedance_count"), bool)
            or not isinstance(row.get("threshold_exceedance_count"), int)
            or row["threshold_exceedance_count"] <= 0
        ):
            raise ValueError("T20.35f selected channel drifted")
        selected.append((expected[0], expected[1], row["threshold_exceedance_count"]))
    return selected


def _replayed_chunks(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("replayed_chunks")
    if (
        not isinstance(rows, list)
        or len(rows) != 5
        or [row.get("inference_seed") for row in rows if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35f replay seed coverage drifted")
    return [
        {
            "inference_seed": row["inference_seed"],
            "decoded_action_chunk": _matrix(
                row.get("decoded_action_chunk"), "decoded action chunk"
            ),
        }
        for row in rows
    ]


def _action_quantiles(
    action_stats: dict[str, Any],
) -> tuple[list[float], list[float], int]:
    q01 = _six(action_stats.get("q01"), "action q01")
    q99 = _six(action_stats.get("q99"), "action q99")
    count_value = action_stats.get("count")
    if (
        not isinstance(count_value, list)
        or len(count_value) != 1
        or isinstance(count_value[0], bool)
        or not isinstance(count_value[0], int)
        or count_value[0] <= 0
        or any(high <= low for low, high in zip(q01, q99, strict=True))
    ):
        raise ValueError("T20.35f action quantile statistics drifted")
    return q01, q99, count_value[0]


def _decompose(signed_errors: list[list[float]]) -> dict[str, float]:
    systematic = 0.0
    variance = 0.0
    total = 0.0
    for timestep in range(50):
        values = [signed_errors[seed][timestep] for seed in range(5)]
        mean = sum(values) / 5
        population_variance = sum((value - mean) ** 2 for value in values) / 5
        systematic += mean * mean
        variance += population_variance
        total += sum(value * value for value in values) / 5
    systematic /= 50
    variance /= 50
    total /= 50
    if total <= 0 or abs(total - systematic - variance) > 1e-15:
        raise ValueError("T20.35f squared-error decomposition failed closure")
    return {
        "total_mean_square_error": total,
        "systematic_bias_mean_square": systematic,
        "seed_variance_mean_square": variance,
        "systematic_bias_fraction": systematic / total,
        "seed_variance_fraction": variance / total,
        "closure_absolute_error": abs(total - systematic - variance),
    }


def _matrix(value: Any, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 50:
        raise ValueError(f"T20.35f {label} must have 50 rows")
    return [_six(row, label) for row in value]


def _six(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(f"T20.35f {label} must have six finite values")
    result = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"T20.35f {label} must have six finite values")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(f"T20.35f {label} must have six finite values")
        result.append(number)
    return result


def _normalize(value: float, q01: float, span: float) -> float:
    normalized = 2.0 * (value - q01) / span - 1.0
    if not math.isfinite(normalized):
        raise ValueError("T20.35f normalization produced a non-finite value")
    return normalized


def _physical_bounds(joint_index: int) -> tuple[float, float]:
    if joint_index < 5:
        return MUJOCO_BODY_LIMITS_RAD[joint_index]
    return GRIPPER_RANGE_RAD


def _identity(payload: dict[str, Any], expected: str, label: str) -> None:
    if payload.get("identity_sha256") != expected:
        raise ValueError(f"T20.35f {label} identity drifted")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35f {label} must be lowercase SHA-256")
    return value

"""Truthful DAgger labels and held-out promotion gates for PI0.5 cycles."""

from __future__ import annotations

import math

from dataclasses import asdict, dataclass
from typing import Any, Iterable


DAGGER_CONTROLLER_SOURCES = frozenset(
    {
        "contact_gated_tray_transfer",
        "contact_gated_recovery_pick",
        "contact_reflex_post_place",
    }
)
UNSAFE_OBJECT_MOTION_MARKERS = ("scripted", "teleport", "free_body")


def is_dagger_correction_frame(frame: dict[str, Any]) -> bool:
    """Return true only for an executed human or privileged controller correction."""

    source = str(frame.get("action_source") or "")
    human_correction = bool(frame.get("is_intervention")) and frame.get("human_action") is not None
    controller_correction = source in DAGGER_CONTROLLER_SOURCES
    if not (human_correction or controller_correction):
        return False
    motion_mode = str(frame.get("object_motion_mode") or "").lower()
    if any(marker in motion_mode for marker in UNSAFE_OBJECT_MOTION_MARKERS):
        return False
    return _is_control(frame.get("policy_action")) and _is_control(frame.get("executed_action"))


def select_training_frames(
    frames: Iterable[dict[str, Any]], selection: str
) -> list[dict[str, Any]]:
    rows = list(frames)
    if selection == "all":
        return rows
    if selection == "intervention_only":
        return [row for row in rows if row.get("is_intervention")]
    if selection == "dagger_corrections":
        return [row for row in rows if is_dagger_correction_frame(row)]
    raise ValueError(f"Unknown frame selection: {selection}")


def select_dagger_context_frames(
    frames: Iterable[dict[str, Any]],
    *,
    before: int,
    after: int,
) -> list[dict[str, Any]]:
    """Select correction runs plus bounded contiguous policy context."""

    if before < 0 or after < 0:
        raise ValueError("DAgger context bounds cannot be negative")
    rows = list(frames)
    if not rows:
        return []
    indices = [int(row["frame_index"]) for row in rows]
    if any(right <= left for left, right in zip(indices, indices[1:])):
        raise ValueError("Source frames must be strictly ordered")
    selected: dict[int, dict[str, Any]] = {}
    for contiguous in _contiguous_source_runs(rows):
        correction_positions = [
            index for index, row in enumerate(contiguous) if is_dagger_correction_frame(row)
        ]
        for correction_run in _contiguous_integer_runs(correction_positions):
            first, last = correction_run[0], correction_run[-1]
            start = max(0, first - before)
            stop = min(len(contiguous), last + after + 1)
            for position in range(start, stop):
                row = dict(contiguous[position])
                if position in correction_run:
                    role = "expert_correction"
                elif position < first:
                    role = "pre_context"
                else:
                    role = "post_context"
                row["replay_role"] = role
                frame_index = int(row["frame_index"])
                existing = selected.get(frame_index)
                if existing is None or role == "expert_correction":
                    selected[frame_index] = row
    return [selected[index] for index in sorted(selected)]


def _contiguous_source_runs(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    runs: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for row in rows:
        if current and int(row["frame_index"]) != int(current[-1]["frame_index"]) + 1:
            runs.append(current)
            current = []
        current.append(row)
    if current:
        runs.append(current)
    return runs


def _contiguous_integer_runs(values: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for value in values:
        if not runs or value != runs[-1][-1] + 1:
            runs.append([value])
        else:
            runs[-1].append(value)
    return runs


def validate_dagger_episode_scope(
    summary: dict[str, Any], frames: Iterable[dict[str, Any]]
) -> None:
    """Reject fabricated, hardware-commanding, or non-neural correction sources."""

    proof = summary.get("proof_scope") or {}
    if proof.get("scripted_object_motion") is not False:
        raise ValueError("DAgger export requires explicit scripted_object_motion=false proof")
    if not proof.get("neural_policy_actions_applied_to_simulation"):
        raise ValueError("DAgger export requires a neural policy rollout")
    intervention = summary.get("intervention") or {}
    safety = intervention.get("safety_report") or {}
    policy_runtime = summary.get("policy_runtime") or {}
    if any(
        bool(value)
        for value in (
            intervention.get("physical_follower_commanded"),
            safety.get("physical_follower_commanded"),
            policy_runtime.get("physical_follower_commanded"),
        )
    ):
        raise ValueError("DAgger export refuses episodes that commanded a physical follower")
    corrections = [row for row in frames if is_dagger_correction_frame(row)]
    if not corrections:
        raise ValueError("DAgger export found no explicit expert correction frames")


def policy_expert_delta_l2(frame: dict[str, Any]) -> float:
    policy = _control(frame.get("policy_action"))
    executed = _control(frame.get("executed_action"))
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(policy, executed, strict=True)))


@dataclass(frozen=True)
class EvaluationMetrics:
    seeds: tuple[int, ...]
    episodes: int
    task_successes: int
    pure_successes: int
    task_success_rate: float
    pure_success_rate: float
    mean_sorted_count: float
    assisted_episodes: int
    scripted_episodes: int
    physical_follower_episodes: int
    stage_metric_episodes: int
    mean_stage_rates: dict[str, float]
    proof_mode_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["seeds"] = list(self.seeds)
        return payload


@dataclass(frozen=True)
class PromotionGate:
    expected_seeds: tuple[int, ...]
    min_pure_success_rate: float = 0.8
    min_success_rate_delta: float = 0.0
    allow_contact_gated_grasp_assist: bool = False
    required_proof_mode: str = "strict_neural"

    def __post_init__(self) -> None:
        if not self.expected_seeds:
            raise ValueError("Promotion gate requires held-out seeds")
        if len(set(self.expected_seeds)) != len(self.expected_seeds):
            raise ValueError("Promotion gate seeds must be unique")
        for name, value in (
            ("min_pure_success_rate", self.min_pure_success_rate),
            ("min_success_rate_delta", self.min_success_rate_delta),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class PromotionDecision:
    accepted: bool
    reasons: tuple[str, ...]
    baseline: EvaluationMetrics
    candidate: EvaluationMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "baseline": self.baseline.to_dict(),
            "candidate": self.candidate.to_dict(),
        }


def summarize_evaluation(
    batch: dict[str, Any], *, allow_contact_gated_grasp_assist: bool = False
) -> EvaluationMetrics:
    results = batch.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("Evaluation batch must contain non-empty results")
    seeds: list[int] = []
    task_successes = 0
    pure_successes = 0
    sorted_total = 0
    assisted_episodes = 0
    scripted_episodes = 0
    physical_episodes = 0
    stage_metric_episodes = 0
    stage_rate_totals = {
        stage: 0.0
        for stage in ("reach", "contact", "grasp", "lift", "transport", "release", "placement")
    }
    proof_mode_counts: dict[str, int] = {}
    for episode in results:
        seed = int(episode["seed"])
        seeds.append(seed)
        score = episode.get("final_score") or {}
        success = bool(episode.get("status") == "pass" and score.get("success"))
        task_successes += int(success)
        sorted_total += int(score.get("sorted_count") or 0)
        proof = episode.get("proof_scope") or {}
        scripted = proof.get("scripted_object_motion") is not False
        physical = _physical_follower_commanded(episode)
        assisted = _episode_was_assisted(
            episode,
            allow_contact_gated_grasp_assist=allow_contact_gated_grasp_assist,
        )
        scripted_episodes += int(scripted)
        physical_episodes += int(physical)
        assisted_episodes += int(assisted)
        pure_successes += int(success and not scripted and not physical and not assisted)
        proof_mode = classify_proof_mode(episode)
        proof_mode_counts[proof_mode] = proof_mode_counts.get(proof_mode, 0) + 1
        stage_metrics = episode.get("stage_metrics")
        if isinstance(stage_metrics, dict) and isinstance(stage_metrics.get("rates"), dict):
            stage_metric_episodes += 1
            for stage in stage_rate_totals:
                stage_rate_totals[stage] += float(stage_metrics["rates"].get(stage, 0.0))
    episodes = len(results)
    return EvaluationMetrics(
        seeds=tuple(sorted(seeds)),
        episodes=episodes,
        task_successes=task_successes,
        pure_successes=pure_successes,
        task_success_rate=task_successes / episodes,
        pure_success_rate=pure_successes / episodes,
        mean_sorted_count=sorted_total / episodes,
        assisted_episodes=assisted_episodes,
        scripted_episodes=scripted_episodes,
        physical_follower_episodes=physical_episodes,
        stage_metric_episodes=stage_metric_episodes,
        mean_stage_rates={
            stage: total / episodes for stage, total in stage_rate_totals.items()
        },
        proof_mode_counts=dict(sorted(proof_mode_counts.items())),
    )


def decide_promotion(
    baseline: EvaluationMetrics,
    candidate: EvaluationMetrics,
    gate: PromotionGate,
) -> PromotionDecision:
    reasons: list[str] = []
    expected = tuple(sorted(gate.expected_seeds))
    if baseline.seeds != expected:
        reasons.append("baseline_seed_set_incomplete")
    if candidate.seeds != expected:
        reasons.append("candidate_seed_set_incomplete")
    if candidate.scripted_episodes:
        reasons.append("candidate_contains_scripted_motion")
    if candidate.physical_follower_episodes:
        reasons.append("candidate_commanded_physical_follower")
    if candidate.assisted_episodes:
        reasons.append("candidate_contains_controller_or_human_assistance")
    if baseline.proof_mode_counts != {gate.required_proof_mode: baseline.episodes}:
        reasons.append("baseline_proof_mode_mismatch")
    if candidate.proof_mode_counts != {gate.required_proof_mode: candidate.episodes}:
        reasons.append("candidate_proof_mode_mismatch")
    if candidate.pure_success_rate < gate.min_pure_success_rate:
        reasons.append("candidate_below_pure_success_threshold")
    required_rate = baseline.pure_success_rate + gate.min_success_rate_delta
    if candidate.pure_success_rate < required_rate:
        reasons.append("candidate_regressed_from_baseline")
    if candidate.mean_sorted_count < baseline.mean_sorted_count:
        reasons.append("candidate_mean_sorted_count_regressed")
    return PromotionDecision(
        accepted=not reasons,
        reasons=tuple(reasons),
        baseline=baseline,
        candidate=candidate,
    )


def classify_proof_mode(episode: dict[str, Any]) -> str:
    proof = episode.get("proof_scope") or {}
    if proof.get("scripted_object_motion") is not False:
        return "invalid_scripted"
    if _physical_follower_commanded(episode):
        return "physical_robot"
    intervention = episode.get("intervention") or {}
    if int(intervention.get("frames") or 0) > 0:
        return "human_intervened"
    grasp = proof.get("grasp_assist") or {}
    controller = grasp.get("post_place_controller") or {}
    modes = {str(value) for value in proof.get("object_motion_modes") or []}
    if any("task_space" in mode or "post_place_controller" in mode for mode in modes) or any(
        int(controller.get(key) or 0) > 0
        for key in ("executed_frames", "tray_transfer_executed_frames", "recovery_pick_executed_frames")
    ):
        return "controller_assisted"
    if int(grasp.get("activation_count") or 0) > 0:
        return "contact_stabilized"
    if proof.get("neural_policy_actions_applied_to_simulation") or any(
        "neural_policy" in mode for mode in modes
    ):
        return "strict_neural"
    return "invalid_unproven"


def _episode_was_assisted(
    episode: dict[str, Any], *, allow_contact_gated_grasp_assist: bool
) -> bool:
    intervention = episode.get("intervention") or {}
    if int(intervention.get("frames") or 0) > 0:
        return True
    proof = episode.get("proof_scope") or {}
    modes = {str(value) for value in proof.get("object_motion_modes") or []}
    if any("task_space" in value or "post_place_controller" in value for value in modes):
        return True
    grasp = proof.get("grasp_assist") or {}
    controller = grasp.get("post_place_controller") or {}
    if any(
        int(controller.get(key) or 0) > 0
        for key in (
            "executed_frames",
            "tray_transfer_executed_frames",
            "recovery_pick_executed_frames",
        )
    ):
        return True
    if not allow_contact_gated_grasp_assist and int(grasp.get("activation_count") or 0) > 0:
        return True
    return False


def _physical_follower_commanded(episode: dict[str, Any]) -> bool:
    intervention = episode.get("intervention") or {}
    safety = intervention.get("safety_report") or {}
    runtime = episode.get("policy_runtime") or {}
    server = runtime.get("server_status") or {}
    return any(
        bool(value)
        for value in (
            intervention.get("physical_follower_commanded"),
            safety.get("physical_follower_commanded"),
            runtime.get("physical_follower_commanded"),
            server.get("physical_follower_commanded"),
        )
    )


def _is_control(value: Any) -> bool:
    return isinstance(value, list) and len(value) >= 6


def _control(value: Any) -> tuple[float, ...]:
    if not _is_control(value):
        raise ValueError(f"Expected six-value control, got {value!r}")
    return tuple(float(item) for item in value[:6])

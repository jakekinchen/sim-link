"""Deadman state and policy/human action arbitration."""

from __future__ import annotations

import json
import os
import time

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.leader_arm_bridge import JOINT_LIMITS_RAD


@dataclass(frozen=True)
class DeadmanSignal:
    armed: bool = False
    takeover: bool = False
    updated_at: float = 0.0
    sequence: int = 0
    source: str = "none"

    def age_s(self, now: float | None = None) -> float:
        current = time.time() if now is None else now
        return max(0.0, current - self.updated_at)

    def is_fresh(self, timeout_s: float, now: float | None = None) -> bool:
        return self.updated_at > 0 and self.age_s(now) <= timeout_s


@dataclass(frozen=True)
class ActionDecision:
    policy_action: tuple[float, ...]
    human_action: tuple[float, ...] | None
    executed_action: tuple[float, ...]
    action_source: str
    is_intervention: bool
    intervention_event: str
    deadman_armed: bool
    deadman_takeover: bool
    deadman_fresh: bool
    deadman_age_s: float | None
    deadman_sequence: int

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("policy_action", "human_action", "executed_action"):
            value = payload[key]
            payload[key] = list(value) if value is not None else None
        return payload


class InterventionArbiter:
    """Hard-switch position targets under a fresh deadman, with slew limiting."""

    def __init__(
        self,
        *,
        deadman_timeout_s: float = 0.5,
        max_delta_per_step: tuple[float, ...] = (0.12, 0.12, 0.12, 0.12, 0.18, 0.24),
    ):
        if deadman_timeout_s <= 0:
            raise ValueError("deadman_timeout_s must be positive")
        if len(max_delta_per_step) != 6:
            raise ValueError("max_delta_per_step must contain six values")
        self.deadman_timeout_s = deadman_timeout_s
        self.max_delta_per_step = max_delta_per_step
        self._was_intervening = False
        self._last_executed: tuple[float, ...] | None = None

    def decide(
        self,
        policy_action: list[float] | tuple[float, ...],
        human_action: list[float] | tuple[float, ...] | None,
        signal: DeadmanSignal,
        *,
        now: float | None = None,
    ) -> ActionDecision:
        current = time.time() if now is None else now
        policy = _clamp_six(policy_action)
        human = _clamp_six(human_action) if human_action is not None else None
        fresh = signal.is_fresh(self.deadman_timeout_s, current)
        intervening = bool(signal.armed and signal.takeover and fresh and human is not None)
        requested = human if intervening else policy
        executed = self._slew_limit(requested)

        if intervening and not self._was_intervening:
            event = "takeover_started"
        elif intervening:
            event = "takeover_held"
        elif self._was_intervening:
            event = "takeover_released"
        else:
            event = "policy_control"
        self._was_intervening = intervening
        self._last_executed = executed

        age = signal.age_s(current) if signal.updated_at > 0 else None
        return ActionDecision(
            policy_action=policy,
            human_action=human,
            executed_action=executed,
            action_source="human_leader" if intervening else "policy",
            is_intervention=intervening,
            intervention_event=event,
            deadman_armed=signal.armed,
            deadman_takeover=signal.takeover,
            deadman_fresh=fresh,
            deadman_age_s=round(age, 6) if age is not None else None,
            deadman_sequence=signal.sequence,
        )

    def _slew_limit(self, requested: tuple[float, ...]) -> tuple[float, ...]:
        if self._last_executed is None:
            return requested
        return tuple(
            round(previous + min(limit, max(-limit, target - previous)), 6)
            for previous, target, limit in zip(
                self._last_executed,
                requested,
                self.max_delta_per_step,
                strict=True,
            )
        )


class InterventionControlStore:
    """Atomic file-backed deadman state shared by browser server and runner."""

    def __init__(self, path: Path):
        self.path = path

    def initialize(self, *, armed: bool = False, source: str = "server") -> DeadmanSignal:
        return self.update(armed=armed, takeover=False, source=source)

    def update(
        self,
        *,
        armed: bool | None = None,
        takeover: bool | None = None,
        source: str = "browser",
        now: float | None = None,
    ) -> DeadmanSignal:
        previous = self.read()
        signal = DeadmanSignal(
            armed=previous.armed if armed is None else bool(armed),
            takeover=previous.takeover if takeover is None else bool(takeover),
            updated_at=time.time() if now is None else now,
            sequence=previous.sequence + 1,
            source=source,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(asdict(signal), sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)
        return signal

    def read(self) -> DeadmanSignal:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return DeadmanSignal(
                armed=bool(payload.get("armed")),
                takeover=bool(payload.get("takeover")),
                updated_at=float(payload.get("updated_at") or 0.0),
                sequence=int(payload.get("sequence") or 0),
                source=str(payload.get("source") or "unknown"),
            )
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
            return DeadmanSignal()


def _clamp_six(values: list[float] | tuple[float, ...] | None) -> tuple[float, ...]:
    if values is None or len(values) < 6:
        raise ValueError("SO-101 actions must contain six position targets")
    return tuple(
        round(min(high, max(low, float(value))), 6)
        for value, (low, high) in zip(values[:6], JOINT_LIMITS_RAD, strict=True)
    )

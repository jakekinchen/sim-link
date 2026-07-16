"""Injected, fail-closed sub-degree motion harness for T19.2b fixtures."""

from __future__ import annotations

import copy

from pathlib import Path
from typing import Any, Callable, Protocol

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.calibration_profile import verify_calibration_profile


PLAN_SCHEMA = "scenesmith.bounded_micro_motion_plan.v1"
RESULT_SCHEMA = "scenesmith.bounded_micro_motion_fixture_result.v1"
T19_1_PATH = Path(
    "configurations/robot_lab/t19_1_readonly_hardware_snapshot_20260716_0712.json"
)
CALIBRATION_PATH = Path("configurations/robot_lab/pi05_calibration_profile.json")
ACCEPTED_LIVE_MANIFEST_PATH = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
PROJECT_STATE_PATH = Path("docs/autonomous-workflow/project_state.json")
RAW_CALIBRATION_PATH = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
SELECTED_JOINT = "wrist_roll"
SELECTED_SERVO_ID = 5
DELTA_TICKS = 8
POSITION_TOLERANCE_TICKS = 3
SETTLE_CONSECUTIVE_SAMPLES = 2
MAX_SETTLE_POLLS = 8
WATCHDOG_NS = 3_000_000_000
VOLTAGE_RANGE = (11.0, 13.0)
MAX_TEMPERATURE_C = 45
AUTHORITY_NOT_GRANTED = (
    "live_hardware_constructor",
    "physical_motion",
    "calibration_update",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "policy_actuation",
    "external_compute",
    "brev_compute",
)


class MotionTransport(Protocol):
    def read(self, register: str, servo_id: int) -> int: ...

    def write(self, register: str, servo_id: int, value: int) -> None: ...

    def close(self, *, disable_torque: bool) -> None: ...


def build_bounded_micro_motion_plan(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    snapshot = load_strict_json(root / T19_1_PATH)
    calibration = load_strict_json(root / CALIBRATION_PATH)
    project_state = load_strict_json(root / PROJECT_STATE_PATH)
    for label, payload in (("T19.1 manifest", snapshot), ("calibration profile", calibration)):
        verify_signed_payload(payload, label=label)
    verify_calibration_profile(
        calibration,
        calibration_path=RAW_CALIBRATION_PATH,
        manifest_path=root / ACCEPTED_LIVE_MANIFEST_PATH,
    )
    if (
        project_state.get("tasks", {}).get("T19.1", {}).get("state") != "verified"
        or project_state.get("tasks", {})
        .get("T19.1", {})
        .get("artifact", {})
        .get("identity_sha256")
        != snapshot.get("identity_sha256")
    ):
        raise ValueError("Bounded motion T19.1 canonical source binding drifted")
    servo = next(
        item for item in snapshot["servos"] if item["joint_name"] == SELECTED_JOINT
    )
    joint = next(
        item for item in calibration["joints"] if item["joint_name"] == SELECTED_JOINT
    )
    baseline = servo["present_position_raw"]
    target = baseline + DELTA_TICKS
    if (
        servo["servo_id"] != SELECTED_SERVO_ID
        or joint["servo_id"] != SELECTED_SERVO_ID
        or servo["torque_enable_raw"] != 0
        or not joint["range_min"] <= baseline < target <= joint["range_max"]
    ):
        raise ValueError("Bounded motion source pose or calibration range is invalid")
    delta_degrees = DELTA_TICKS * 360.0 / 4095.0
    return sign_payload(
        {
            "schema_version": PLAN_SCHEMA,
            "plan_name": "pi05_t19_2b_wrist_roll_subdegree_delta_and_return",
            "evidence_mode": "offline_fixture_motion_harness",
            "source_t19_1_identity_sha256": snapshot["identity_sha256"],
            "source_calibration_identity_sha256": calibration["identity_sha256"],
            "selected_joint": SELECTED_JOINT,
            "selected_servo_id": SELECTED_SERVO_ID,
            "immutable_servo_ids": [1, 2, 3, 4, 6],
            "baseline_position_raw": baseline,
            "target_position_raw": target,
            "delta_ticks": DELTA_TICKS,
            "delta_degrees": delta_degrees,
            "position_tolerance_ticks": POSITION_TOLERANCE_TICKS,
            "settle_consecutive_samples": SETTLE_CONSECUTIVE_SAMPLES,
            "maximum_settle_polls_per_leg": MAX_SETTLE_POLLS,
            "watchdog_duration_ns": WATCHDOG_NS,
            "voltage_range_volts": list(VOLTAGE_RANGE),
            "maximum_temperature_celsius": MAX_TEMPERATURE_C,
            "allowed_read_registers": [
                "Torque_Enable",
                "Present_Position",
                "Present_Voltage",
                "Present_Temperature",
            ],
            "allowed_write_registers": ["Torque_Enable", "Goal_Position"],
            "success_write_sequence": [
                ["Torque_Enable", 1],
                ["Goal_Position", target],
                ["Goal_Position", baseline],
                ["Torque_Enable", 0],
            ],
            "close_contract": {"disable_torque": False, "close_calls": 1},
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "authority_not_granted": list(AUTHORITY_NOT_GRANTED),
        }
    )


def verify_bounded_micro_motion_plan(
    payload: dict[str, Any], *, repo_root: Path
) -> None:
    verify_signed_payload(payload, label="bounded micro-motion plan")
    if payload != build_bounded_micro_motion_plan(repo_root=repo_root):
        raise ValueError("Bounded micro-motion plan drifted from exact sources")


def run_injected_bounded_motion_harness(
    *,
    plan: dict[str, Any],
    transport: MotionTransport,
    deadman: Callable[[int], bool],
    monotonic_ns: Callable[[], int],
    repo_root: Path,
) -> dict[str, Any]:
    verify_bounded_micro_motion_plan(plan, repo_root=repo_root)
    if getattr(transport, "fixture_only", None) is not True:
        raise ValueError("Bounded motion harness accepts fixture transports only")
    trace: list[dict[str, Any]] = []
    start = monotonic_ns()
    torque_enabled = False
    closed = False

    def guard() -> int:
        now = monotonic_ns()
        if now - start > plan["watchdog_duration_ns"]:
            raise TimeoutError("Bounded motion watchdog expired")
        if deadman(now) is not True:
            raise RuntimeError("Bounded motion deadman is not active")
        return now

    def record(operation: str, now: int, **fields: Any) -> None:
        trace.append(
            {"sequence": len(trace), "operation": operation, "monotonic_ns": now, **fields}
        )

    def read(register: str) -> int:
        if register not in plan["allowed_read_registers"]:
            raise ValueError("Bounded motion read register is not allowed")
        now = guard()
        value = transport.read(register, plan["selected_servo_id"])
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Bounded motion read value is malformed")
        record("read", now, register=register, servo_id=plan["selected_servo_id"], value=value)
        return value

    def write(register: str, value: int, *, emergency: bool = False) -> None:
        if register not in plan["allowed_write_registers"]:
            raise ValueError("Bounded motion write register is not allowed")
        now = monotonic_ns() if emergency else guard()
        transport.write(register, plan["selected_servo_id"], value)
        record(
            "emergency_write" if emergency else "write",
            now,
            register=register,
            servo_id=plan["selected_servo_id"],
            value=value,
        )

    def settle(target: int) -> None:
        consecutive = 0
        for _ in range(plan["maximum_settle_polls_per_leg"]):
            position = read("Present_Position")
            if abs(position - target) <= plan["position_tolerance_ticks"]:
                consecutive += 1
                if consecutive == plan["settle_consecutive_samples"]:
                    return
            else:
                consecutive = 0
        raise TimeoutError("Bounded motion settling timed out")

    try:
        torque = read("Torque_Enable")
        baseline = read("Present_Position")
        voltage_raw = read("Present_Voltage")
        temperature = read("Present_Temperature")
        if torque != 0:
            raise ValueError("Bounded motion requires torque disabled at entry")
        if abs(baseline - plan["baseline_position_raw"]) > plan["position_tolerance_ticks"]:
            raise ValueError("Bounded motion starting pose drifted")
        voltage = voltage_raw / 10.0
        if not plan["voltage_range_volts"][0] <= voltage <= plan["voltage_range_volts"][1]:
            raise ValueError("Bounded motion voltage is outside the safe range")
        if temperature > plan["maximum_temperature_celsius"]:
            raise ValueError("Bounded motion temperature is outside the safe range")
        torque_enabled = True
        write("Torque_Enable", 1)
        write("Goal_Position", plan["target_position_raw"])
        settle(plan["target_position_raw"])
        write("Goal_Position", plan["baseline_position_raw"])
        settle(plan["baseline_position_raw"])
        write("Torque_Enable", 0)
        torque_enabled = False
        if read("Torque_Enable") != 0:
            raise ValueError("Bounded motion final torque state is not disabled")
        final_position = read("Present_Position")
        if abs(final_position - plan["baseline_position_raw"]) > plan["position_tolerance_ticks"]:
            raise ValueError("Bounded motion did not return to baseline")
    except BaseException as primary:
        cleanup_errors: list[BaseException] = []
        if torque_enabled:
            for register, value in (
                ("Goal_Position", plan["baseline_position_raw"]),
                ("Torque_Enable", 0),
            ):
                try:
                    write(register, value, emergency=True)
                except BaseException as cleanup:
                    cleanup_errors.append(cleanup)
        try:
            now = monotonic_ns()
            closed = True
            transport.close(disable_torque=False)
            record("close", now, disable_torque=False)
        except BaseException as cleanup:
            cleanup_errors.append(cleanup)
        if cleanup_errors:
            raise BaseExceptionGroup(
                "Bounded motion failed and cleanup also failed",
                [primary, *cleanup_errors],
            )
        raise
    finally:
        if not closed:
            now = monotonic_ns()
            transport.close(disable_torque=False)
            record("close", now, disable_torque=False)
            closed = True

    writes = [event for event in trace if event["operation"] == "write"]
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA,
            "result_name": "pi05_t19_2b_bounded_motion_harness_fixture",
            "evidence_mode": "deterministic_injected_fixture",
            "plan_identity_sha256": plan["identity_sha256"],
            "trace": trace,
            "read_count": sum(event["operation"] == "read" for event in trace),
            "write_count": len(writes),
            "torque_change_count": 2,
            "motion_command_count": 2,
            "close_count": sum(event["operation"] == "close" for event in trace),
            "returned_to_baseline": True,
            "final_torque_disabled": True,
            "watchdog_conformant": True,
            "deadman_checked_before_every_non_cleanup_operation": True,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "authority_granted": ["bounded_micro_motion_harness_fixture_conformant"],
            "authority_not_granted": list(AUTHORITY_NOT_GRANTED),
        }
    )


class DeterministicFixtureTransport:
    fixture_only = True

    def __init__(self, plan: dict[str, Any]):
        self.plan = plan
        self.torque = 0
        self.position = plan["baseline_position_raw"]
        self.goal = self.position
        self.poll_index = 0
        self.closed = False

    def read(self, register: str, servo_id: int) -> int:
        if servo_id != SELECTED_SERVO_ID:
            raise AssertionError("fixture touched an immutable servo")
        if register == "Torque_Enable":
            return self.torque
        if register == "Present_Voltage":
            return 122
        if register == "Present_Temperature":
            return 32
        if register == "Present_Position":
            if self.position != self.goal:
                step = 3 if self.goal > self.position else -3
                candidate = self.position + step
                self.position = min(candidate, self.goal) if step > 0 else max(candidate, self.goal)
            return self.position
        raise AssertionError("fixture received an unexpected read")

    def write(self, register: str, servo_id: int, value: int) -> None:
        if servo_id != SELECTED_SERVO_ID:
            raise AssertionError("fixture touched an immutable servo")
        if register == "Torque_Enable":
            if value not in {0, 1}:
                raise AssertionError("fixture torque value drifted")
            self.torque = value
            return
        if register == "Goal_Position":
            if value not in {
                self.plan["baseline_position_raw"],
                self.plan["target_position_raw"],
            }:
                raise AssertionError("fixture goal escaped the exact plan")
            self.goal = value
            return
        raise AssertionError("fixture received an unexpected write")

    def close(self, *, disable_torque: bool) -> None:
        if disable_torque is not False or self.closed:
            raise AssertionError("fixture close drifted")
        self.closed = True


class DeterministicClock:
    def __init__(self) -> None:
        self.now = 1_000_000_000

    def __call__(self) -> int:
        value = self.now
        self.now += 10_000_000
        return value


def build_bounded_motion_fixture_result(*, repo_root: Path) -> dict[str, Any]:
    plan = build_bounded_micro_motion_plan(repo_root=repo_root)
    return run_injected_bounded_motion_harness(
        plan=plan,
        transport=DeterministicFixtureTransport(plan),
        deadman=lambda _: True,
        monotonic_ns=DeterministicClock(),
        repo_root=repo_root,
    )


def verify_bounded_motion_fixture_result(
    payload: dict[str, Any], *, repo_root: Path
) -> None:
    verify_signed_payload(payload, label="bounded motion fixture result")
    if payload != build_bounded_motion_fixture_result(repo_root=repo_root):
        raise ValueError("Bounded motion fixture result drifted from deterministic replay")

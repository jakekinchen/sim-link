from __future__ import annotations

import ast
import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.readonly_servo_census import (
    DEFAULT_CENSUS_CONTRACT_PATH,
    DEFAULT_CENSUS_RESULT_PATH,
    DEFAULT_CENSUS_TRACE_PATH,
    InjectedReadOnlyBusAdapter,
    RecordedTraceTransport,
    build_census_contract,
    build_recorded_census_trace,
    replay_recorded_census,
    run_readonly_census,
    verify_census_contract,
    verify_census_fixture_artifacts,
    verify_recorded_census_trace,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class _CapturedFactory:
    def __init__(self, trace: dict):
        self.trace = trace
        self.transport: RecordedTraceTransport | None = None

    def __call__(self) -> RecordedTraceTransport:
        self.transport = RecordedTraceTransport(self.trace)
        return self.transport


class _InjectedBackend:
    def __init__(self):
        self.calls: list[tuple] = []
        self.is_connected = False

    def connect(self, *, handshake: bool) -> None:
        self.calls.append(("connect", handshake))
        self.is_connected = True

    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        self.calls.append(("read", register, motor, normalize, num_retry))
        return 777

    def disconnect(self, *, disable_torque: bool) -> None:
        self.calls.append(("disconnect", disable_torque))
        self.is_connected = False

    def write(self, *args, **kwargs) -> None:
        raise AssertionError("writable backend method must never be called")


class _ConnectFailureBackend(_InjectedBackend):
    def connect(self, *, handshake: bool) -> None:
        self.calls.append(("connect", handshake))
        self.is_connected = True
        raise ConnectionError("connect failed after opening")


class ReadonlyServoCensusTests(unittest.TestCase):
    def _bundle(self) -> dict:
        return verify_census_fixture_artifacts(repo_root=REPO_ROOT)

    def test_checked_in_fixture_replays_with_exact_no_write_counts(self):
        bundle = self._bundle()
        result = bundle["result"]

        self.assertEqual(result["conformance_state"], "census_trace_conformant")
        self.assertEqual(result["proof_label"], "census_trace_conformant")
        self.assertFalse(result["hardware_opened"])
        self.assertFalse(result["physical_follower_commanded"])
        self.assertEqual(len(result["servos"]), 6)
        self.assertEqual(
            [item["servo_id"] for item in result["servos"]], list(range(1, 7))
        )
        self.assertTrue(all(item["model"] == "sts3215" for item in result["servos"]))
        counts = result["operation_counts"]
        self.assertEqual(counts["construct_attempts"], 1)
        self.assertEqual(counts["connect_attempts"], 1)
        self.assertEqual(counts["read_successes"], 48)
        self.assertEqual(counts["read_retries"], 1)
        self.assertEqual(counts["read_attempts"], 49)
        self.assertEqual(counts["close_attempts"], 1)
        for key in (
            "motor_register_writes",
            "torque_changes",
            "motion_commands",
            "unexpected_operations",
        ):
            self.assertEqual(counts[key], 0)

    def test_contract_is_code_pinned_and_requires_complete_identity(self):
        contract = build_census_contract()
        mutations = (
            (
                "role",
                lambda value: value["target_device_identity"].__setitem__(
                    "device_role", "leader"
                ),
            ),
            (
                "serial",
                lambda value: value["target_device_identity"]["usb"].__setitem__(
                    "serial_number", ""
                ),
            ),
            (
                "alias",
                lambda value: value["target_device_identity"]["usb"][
                    "allowed_aliases"
                ].append("/dev/cu.fixture-so101-leader"),
            ),
            (
                "servo_id",
                lambda value: value["expected_servos"][0].__setitem__("servo_id", 6),
            ),
            (
                "model",
                lambda value: value["expected_servos"][0].__setitem__(
                    "model", "unknown"
                ),
            ),
            (
                "write_register",
                lambda value: value["read_plan"].append(
                    {
                        "register": "Goal_Position",
                        "width_bytes": 2,
                        "raw_type": "integer",
                    }
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(contract)
                mutate(changed)
                changed = sign_payload(changed)
                with self.assertRaisesRegex(
                    ValueError, "code-pinned|identity|read plan"
                ):
                    verify_census_contract(changed)

    def test_trace_rejects_write_torque_motion_unknown_and_bad_lifecycle(self):
        contract = build_census_contract()
        base = build_recorded_census_trace(contract)
        mutations = (
            (
                "write",
                lambda value: value["events"][2].__setitem__("operation", "write"),
                "forbidden operation",
            ),
            (
                "torque",
                lambda value: value["events"][2].__setitem__(
                    "operation", "disable_torque"
                ),
                "forbidden operation",
            ),
            (
                "motion",
                lambda value: value["events"][2].__setitem__(
                    "operation", "send_action"
                ),
                "forbidden operation",
            ),
            (
                "unknown",
                lambda value: value["events"][2].__setitem__(
                    "register", "Unknown_Register"
                ),
                "register",
            ),
            (
                "sequence",
                lambda value: value["events"][2].__setitem__("sequence", 99),
                "sequence",
            ),
            (
                "double_close",
                lambda value: value["events"].append(
                    copy.deepcopy(value["events"][-1])
                ),
                "close",
            ),
            (
                "teardown_write",
                lambda value: value["events"][-1].__setitem__("disable_torque", True),
                "disable_torque",
            ),
            (
                "malformed",
                lambda value: value["events"].__setitem__(2, []),
                "malformed",
            ),
            (
                "missing_read",
                lambda value: value["events"].pop(3),
                "sequence|missing|order",
            ),
            (
                "extra_read",
                lambda value: value["events"].insert(
                    3, copy.deepcopy(value["events"][2])
                ),
                "sequence|extra|order",
            ),
            (
                "duplicate_servo_id",
                lambda value: next(
                    event
                    for event in value["events"]
                    if event.get("operation") == "read"
                    and event.get("servo_id") == 2
                    and event.get("register") == "ID"
                ).__setitem__("raw_value", 1),
                "servo ID",
            ),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(base)
                mutate(changed)
                changed = sign_payload(changed)
                with self.assertRaisesRegex(ValueError, message):
                    verify_recorded_census_trace(changed, contract=contract)

    def test_transient_retry_is_bounded_and_deterministic(self):
        contract = build_census_contract()
        trace = build_recorded_census_trace(contract)
        left = replay_recorded_census(contract, trace)
        right = replay_recorded_census(contract, trace)
        self.assertEqual(left, right)
        self.assertEqual(left["operation_counts"]["read_retries"], 1)

    def test_content_identity_is_order_invariant_and_evidence_sensitive(self):
        contract = build_census_contract()
        trace = build_recorded_census_trace(contract)
        reordered = {key: trace[key] for key in reversed(tuple(trace))}
        self.assertEqual(
            sign_payload(reordered)["identity_sha256"], trace["identity_sha256"]
        )

        changed = copy.deepcopy(trace)
        position = next(
            event
            for event in changed["events"]
            if event.get("operation") == "read"
            and event.get("servo_id") == 1
            and event.get("register") == "Present_Position"
        )
        position["raw_value"] += 1
        changed = sign_payload(changed)
        verify_recorded_census_trace(changed, contract=contract)
        self.assertNotEqual(changed["identity_sha256"], trace["identity_sha256"])
        self.assertNotEqual(
            replay_recorded_census(contract, changed)["identity_sha256"],
            replay_recorded_census(contract, trace)["identity_sha256"],
        )

    def test_retry_exhaustion_closes_exactly_once(self):
        contract = build_census_contract()
        trace = _failure_trace(
            contract, first_outcome="transient_error", second_outcome="transient_error"
        )
        factory = _CapturedFactory(trace)
        with self.assertRaisesRegex(ConnectionError, "retry"):
            run_readonly_census(contract, factory)
        self.assertIsNotNone(factory.transport)
        self.assertEqual(factory.transport.audit()["close_calls"], 1)
        self.assertEqual(factory.transport.audit()["motor_register_writes"], 0)

    def test_primary_and_close_failures_are_both_preserved(self):
        contract = build_census_contract()
        trace = _failure_trace(
            contract,
            first_outcome="fatal_error",
            close_outcome="close_error",
        )
        factory = _CapturedFactory(trace)
        with self.assertRaises(ExceptionGroup) as captured:
            run_readonly_census(contract, factory)
        self.assertEqual(len(captured.exception.exceptions), 2)
        self.assertIn("read", str(captured.exception.exceptions[0]).lower())
        self.assertIn("close", str(captured.exception.exceptions[1]).lower())
        self.assertEqual(factory.transport.audit()["close_calls"], 1)

    def test_bad_decode_and_identity_mismatch_cleanup_without_writes(self):
        contract = build_census_contract()
        cases = (
            (
                "raw_type",
                lambda trace: trace["events"][2].__setitem__("raw_value", "777"),
                "integer",
            ),
            (
                "model",
                lambda trace: trace["events"][2].__setitem__("raw_value", 999),
                "model",
            ),
            (
                "usb_serial",
                lambda trace: trace["observed_device_identity"]["usb"].__setitem__(
                    "serial_number",
                    "fixture-wrong-device",
                ),
                "identity",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                trace = _failure_trace(contract, first_outcome="success")
                mutate(trace)
                trace = sign_payload(trace)
                factory = _CapturedFactory(trace)
                with self.assertRaisesRegex(ValueError, message):
                    run_readonly_census(contract, factory)
                self.assertEqual(factory.transport.audit()["close_calls"], 1)
                self.assertEqual(factory.transport.audit()["motor_register_writes"], 0)

    def test_observed_identity_rejects_role_usb_bus_and_alias_drift(self):
        contract = build_census_contract()
        base = build_recorded_census_trace(contract)
        cases = (
            (
                "role",
                lambda value: value["observed_device_identity"].__setitem__(
                    "device_role", "leader"
                ),
            ),
            (
                "vid",
                lambda value: value["observed_device_identity"]["usb"].__setitem__(
                    "vendor_id_hex", "0000"
                ),
            ),
            (
                "pid",
                lambda value: value["observed_device_identity"]["usb"].__setitem__(
                    "product_id_hex", "0000"
                ),
            ),
            (
                "serial",
                lambda value: value["observed_device_identity"]["usb"].__setitem__(
                    "serial_number", "wrong"
                ),
            ),
            (
                "path",
                lambda value: value["observed_device_identity"]["usb"].__setitem__(
                    "canonical_path", "/dev/cu.other"
                ),
            ),
            (
                "alias",
                lambda value: value["observed_device_identity"]["usb"][
                    "observed_aliases"
                ].append("/dev/cu.fixture-so101-leader"),
            ),
            (
                "protocol",
                lambda value: value["observed_device_identity"]["bus"].__setitem__(
                    "protocol_version", 2
                ),
            ),
            (
                "baud",
                lambda value: value["observed_device_identity"]["bus"].__setitem__(
                    "baudrate", 115200
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                changed = copy.deepcopy(base)
                mutate(changed)
                changed = sign_payload(changed)
                with self.assertRaisesRegex(ValueError, "identity|alias|protocol|baud"):
                    verify_recorded_census_trace(changed, contract=contract)

    def test_injected_adapter_uses_only_no_handshake_reads_and_no_write_close(self):
        backend = _InjectedBackend()
        identity = build_recorded_census_trace(build_census_contract())[
            "observed_device_identity"
        ]
        adapter = InjectedReadOnlyBusAdapter(
            backend=backend,
            device_identity=identity,
            servo_names={
                index: name
                for index, name in enumerate(
                    (
                        "shoulder_pan",
                        "shoulder_lift",
                        "elbow_flex",
                        "wrist_flex",
                        "wrist_roll",
                        "gripper",
                    ),
                    start=1,
                )
            },
        )
        adapter.connect()
        self.assertEqual(adapter.read("Model_Number", 1), 777)
        adapter.close()
        self.assertEqual(
            backend.calls,
            [
                ("connect", False),
                ("read", "Model_Number", "shoulder_pan", False, 0),
                ("disconnect", False),
            ],
        )
        audit = adapter.audit()
        self.assertEqual(audit["motor_register_writes"], 0)
        self.assertEqual(audit["torque_changes"], 0)
        self.assertEqual(audit["motion_commands"], 0)
        self.assertFalse(hasattr(adapter, "write"))
        self.assertFalse(hasattr(adapter, "disable_torque"))
        self.assertFalse(hasattr(adapter, "send_action"))

    def test_injected_adapter_closes_no_write_after_partial_connect_failure(self):
        backend = _ConnectFailureBackend()
        identity = build_recorded_census_trace(build_census_contract())[
            "observed_device_identity"
        ]
        adapter = InjectedReadOnlyBusAdapter(
            backend=backend,
            device_identity=identity,
            servo_names={
                servo_id: name
                for servo_id, name in enumerate(
                    (
                        "shoulder_pan",
                        "shoulder_lift",
                        "elbow_flex",
                        "wrist_flex",
                        "wrist_roll",
                        "gripper",
                    ),
                    start=1,
                )
            },
        )
        with self.assertRaisesRegex(ConnectionError, "connect failed"):
            run_readonly_census(build_census_contract(), lambda: adapter)
        self.assertEqual(
            backend.calls,
            [("connect", False), ("disconnect", False)],
        )
        audit = adapter.audit()
        self.assertTrue(audit["hardware_opened"])
        self.assertEqual(audit["close_calls"], 1)
        self.assertEqual(audit["motor_register_writes"], 0)

    def test_offline_cli_and_module_have_no_live_factory_surface(self):
        for relative_path in (
            "scripts/robot_lab/write_readonly_servo_census_fixture.py",
            "scenesmith/robot_lab/readonly_servo_census.py",
        ):
            source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imported.add(node.module or "")
                    imported.update(alias.name for alias in node.names)
            called_names = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            self.assertFalse(
                any(
                    token in name.lower()
                    for name in imported
                    for token in ("lerobot", "serial", "camera")
                )
            )
            self.assertTrue(
                {
                    "SOFollower",
                    "FeetechMotorsBus",
                    "comports",
                    "list_ports",
                }.isdisjoint(called_names)
            )

    def test_leader_bridge_teardown_explicitly_disables_no_torque(self):
        source_path = REPO_ROOT / "scenesmith" / "robot_lab" / "leader_arm_bridge.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disconnect_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "disconnect"
        ]
        self.assertEqual(len(disconnect_calls), 1)
        self.assertEqual(
            [
                (keyword.arg, keyword.value.value)
                for keyword in disconnect_calls[0].keywords
            ],
            [("disable_torque", False)],
        )

    def test_product_paths_are_scoped_fixture_artifacts(self):
        self.assertEqual(DEFAULT_CENSUS_CONTRACT_PATH.parts[0], "configurations")
        self.assertEqual(DEFAULT_CENSUS_TRACE_PATH.parts[:2], ("tests", "fixtures"))
        self.assertEqual(DEFAULT_CENSUS_RESULT_PATH.parts[:2], ("tests", "fixtures"))


def _failure_trace(
    contract: dict,
    *,
    first_outcome: str,
    second_outcome: str | None = None,
    close_outcome: str = "success",
) -> dict:
    trace = build_recorded_census_trace(contract)
    first_read = copy.deepcopy(trace["events"][2])
    first_read["sequence"] = 2
    first_read["outcome"] = first_outcome
    first_read["raw_value"] = 777 if first_outcome == "success" else None
    first_read["error_code"] = None if first_outcome == "success" else "timeout"
    events = [
        copy.deepcopy(trace["events"][0]),
        copy.deepcopy(trace["events"][1]),
        first_read,
    ]
    if second_outcome is not None:
        second = copy.deepcopy(first_read)
        second["sequence"] = 3
        second["attempt"] = 2
        second["outcome"] = second_outcome
        second["raw_value"] = 777 if second_outcome == "success" else None
        second["error_code"] = None if second_outcome == "success" else "timeout"
        events.append(second)
    close = copy.deepcopy(trace["events"][-1])
    close["sequence"] = len(events)
    close["outcome"] = close_outcome
    events.append(close)
    trace["events"] = events
    return sign_payload(trace)


if __name__ == "__main__":
    unittest.main()

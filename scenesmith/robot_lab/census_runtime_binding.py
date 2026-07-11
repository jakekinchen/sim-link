"""Independent pinned-source bindings for the SO-101 read-only census."""

from __future__ import annotations

import ast
import hashlib

from pathlib import Path
from typing import Any


RUNTIME_SOURCE_BINDINGS = (
    {
        "binding_id": "feetech_implementation",
        "path": "external/lerobot/src/lerobot/motors/feetech/feetech.py",
        "sha256": "0460413cd6a641cede015ac19ac53d2cfe9c343af1bd18ed74e1951229f64ff2",
    },
    {
        "binding_id": "feetech_tables",
        "path": "external/lerobot/src/lerobot/motors/feetech/tables.py",
        "sha256": "71f7f7beb17169781bd26a33b165ed4c5c3df7b9c477d36860f9d6011eb00428",
    },
    {
        "binding_id": "motor_bus_lifecycle",
        "path": "external/lerobot/src/lerobot/motors/motors_bus.py",
        "sha256": "ade55d42046f1f0fa737eb61c360d76ed98211f200e10918dc2e6fcfd640a688",
    },
    {
        "binding_id": "so_follower_joint_map",
        "path": "external/lerobot/src/lerobot/robots/so_follower/so_follower.py",
        "sha256": "d09a2e63ad916f3a9e69740b1033e8c1f2dd5b025d61e5b0baacf1767ca6b8d1",
    },
)

EXPECTED_READ_REGISTER_WIDTHS = {
    "Model_Number": 2,
    "Firmware_Major_Version": 1,
    "Firmware_Minor_Version": 1,
    "ID": 1,
    "Baud_Rate": 1,
    "Present_Position": 2,
    "Present_Voltage": 1,
    "Present_Temperature": 1,
}

EXPECTED_RUNTIME_SEMANTICS = {
    "default_protocol_version": 0,
    "constructor_protocol_default": 0,
    "sts3215_protocol_version": 0,
    "default_baudrate": 1_000_000,
    "sts3215_baud_code": 0,
    "sts3215_model_number": 777,
    "sts3215_resolution": 4096,
    "connect_handshake_default": True,
    "connect_handshake_guarded_by_flag": True,
    "connect_open_port_outside_handshake_guard": True,
    "disconnect_disable_torque_default": True,
    "disconnect_torque_write_guarded_by_flag": True,
    "disconnect_close_port_outside_torque_guard": True,
    "read_register_widths": EXPECTED_READ_REGISTER_WIDTHS,
    "follower_joint_map": [
        {"joint_name": "shoulder_pan", "servo_id": 1, "model": "sts3215"},
        {"joint_name": "shoulder_lift", "servo_id": 2, "model": "sts3215"},
        {"joint_name": "elbow_flex", "servo_id": 3, "model": "sts3215"},
        {"joint_name": "wrist_flex", "servo_id": 4, "model": "sts3215"},
        {"joint_name": "wrist_roll", "servo_id": 5, "model": "sts3215"},
        {"joint_name": "gripper", "servo_id": 6, "model": "sts3215"},
    ],
}


def verify_census_runtime_source_bindings(*, repo_root: Path) -> dict[str, Any]:
    """Hash and independently parse every runtime fact duplicated by the census."""

    root = repo_root.resolve()
    sources: dict[str, tuple[Path, ast.Module, dict[str, Any]]] = {}
    verified_bindings: list[dict[str, str]] = []
    for binding in RUNTIME_SOURCE_BINDINGS:
        relative_path = Path(binding["path"])
        path = (root / relative_path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                "Census runtime source path escapes the repository"
            ) from exc
        if not path.is_file():
            raise ValueError(f"Census runtime source is missing: {relative_path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != binding["sha256"]:
            raise ValueError(
                "Census runtime source hash drifted: "
                f"{relative_path} expected {binding['sha256']} got {digest}"
            )
        tree = _parse_source(path)
        sources[binding["binding_id"]] = (
            path,
            tree,
            _literal_assignment_environment(tree),
        )
        verified_bindings.append(dict(binding))

    semantics = _extract_runtime_semantics(sources)
    if semantics != EXPECTED_RUNTIME_SEMANTICS:
        raise ValueError(
            "Census runtime semantics drifted from the code-pinned contract: "
            f"expected {EXPECTED_RUNTIME_SEMANTICS!r}, got {semantics!r}"
        )
    return {
        "source_bindings": verified_bindings,
        "semantics": semantics,
    }


def _extract_runtime_semantics(
    sources: dict[str, tuple[Path, ast.Module, dict[str, Any]]],
) -> dict[str, Any]:
    _, feetech_tree, feetech_values = sources["feetech_implementation"]
    _, _, table_values = sources["feetech_tables"]
    _, bus_tree, bus_values = sources["motor_bus_lifecycle"]
    _, follower_tree, _ = sources["so_follower_joint_map"]

    control_table = _require_mapping(
        table_values.get("STS_SMS_SERIES_CONTROL_TABLE"),
        label="STS/SMS control table",
    )
    read_widths = {
        register: _require_register_width(control_table, register)
        for register in EXPECTED_READ_REGISTER_WIDTHS
    }
    baud_table = _require_mapping(
        table_values.get("STS_SMS_SERIES_BAUDRATE_TABLE"),
        label="STS/SMS baud table",
    )
    model_protocols = _require_mapping(
        table_values.get("MODEL_PROTOCOL"),
        label="model protocol table",
    )
    model_numbers = _require_mapping(
        table_values.get("MODEL_NUMBER_TABLE"),
        label="model number table",
    )
    model_resolutions = _require_mapping(
        table_values.get("MODEL_RESOLUTION"),
        label="model resolution table",
    )

    serial_bus = _find_class(bus_tree, "SerialMotorsBus")
    connect = _find_method(serial_bus, "connect")
    internal_connect = _find_method(serial_bus, "_connect")
    disconnect = _find_method(serial_bus, "disconnect")
    feetech_bus = _find_class(feetech_tree, "FeetechMotorsBus")
    constructor = _find_method(feetech_bus, "__init__")
    return {
        "default_protocol_version": _require_int(
            feetech_values.get("DEFAULT_PROTOCOL_VERSION"),
            label="default Feetech protocol",
        ),
        "constructor_protocol_default": _function_parameter_default(
            constructor,
            "protocol_version",
            environment=feetech_values,
        ),
        "sts3215_protocol_version": _require_int(
            model_protocols.get("sts3215"),
            label="STS3215 protocol",
        ),
        "default_baudrate": _require_int(
            feetech_values.get("DEFAULT_BAUDRATE"),
            label="default Feetech baudrate",
        ),
        "sts3215_baud_code": _require_int(
            baud_table.get(1_000_000),
            label="STS3215 1M baud code",
        ),
        "sts3215_model_number": _require_int(
            model_numbers.get("sts3215"),
            label="STS3215 model number",
        ),
        "sts3215_resolution": _require_int(
            model_resolutions.get("sts3215"),
            label="STS3215 resolution",
        ),
        "connect_handshake_default": _function_parameter_default(
            connect,
            "handshake",
            environment=bus_values,
        ),
        "connect_handshake_guarded_by_flag": _guard_contains_call(
            internal_connect,
            guard_name="handshake",
            call_name="_handshake",
        ),
        "connect_open_port_outside_handshake_guard": _contains_call_outside_guard(
            internal_connect,
            guard_name="handshake",
            call_name="openPort",
        ),
        "disconnect_disable_torque_default": _function_parameter_default(
            disconnect,
            "disable_torque",
            environment=bus_values,
        ),
        "disconnect_torque_write_guarded_by_flag": _guard_contains_call(
            disconnect,
            guard_name="disable_torque",
            call_name="disable_torque",
        ),
        "disconnect_close_port_outside_torque_guard": _contains_call_outside_guard(
            disconnect,
            guard_name="disable_torque",
            call_name="closePort",
        ),
        "read_register_widths": read_widths,
        "follower_joint_map": _extract_follower_joint_map(follower_tree),
    }


def _parse_source(path: Path) -> ast.Module:
    source = path.read_text(encoding="utf-8")
    # The pinned motor-bus source contains Python 3.12 ``type`` aliases while
    # this repository's verification interpreter is Python 3.11. Removing only
    # those declarations preserves every executable node that this audit reads.
    compatible = "\n".join(
        "" if line.startswith("type ") else line for line in source.splitlines()
    )
    try:
        return ast.parse(compatible, filename=str(path))
    except SyntaxError as exc:
        raise ValueError(f"Census runtime source cannot be parsed: {path}") from exc


def _literal_assignment_environment(tree: ast.Module) -> dict[str, Any]:
    pending: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                pending[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                pending[node.target.id] = node.value

    values: dict[str, Any] = {}
    progress = True
    while pending and progress:
        progress = False
        for name, node in tuple(pending.items()):
            try:
                values[name] = _literal_value(node, values)
            except (KeyError, ValueError):
                continue
            del pending[name]
            progress = True
    return values


def _literal_value(node: ast.AST, environment: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return environment[node.id]
    if isinstance(node, ast.Tuple):
        return tuple(_literal_value(item, environment) for item in node.elts)
    if isinstance(node, ast.List):
        return [_literal_value(item, environment) for item in node.elts]
    if isinstance(node, ast.Dict):
        return {
            _literal_value(key, environment): _literal_value(value, environment)
            for key, value in zip(node.keys, node.values, strict=True)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_literal_value(node.operand, environment)
    raise ValueError(f"Unsupported non-literal source expression: {ast.dump(node)}")


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise ValueError(f"Census runtime semantics missing class {name}")


def _find_method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise ValueError(
        f"Census runtime semantics missing method {class_node.name}.{name}"
    )


def _function_parameter_default(
    function: ast.FunctionDef,
    parameter_name: str,
    *,
    environment: dict[str, Any],
) -> Any:
    names = [argument.arg for argument in function.args.args]
    if parameter_name not in names:
        raise ValueError(
            f"Census runtime semantics missing parameter {function.name}.{parameter_name}"
        )
    index = names.index(parameter_name)
    first_default = len(names) - len(function.args.defaults)
    if index < first_default:
        raise ValueError(
            f"Census runtime semantics parameter has no default: {function.name}.{parameter_name}"
        )
    return _literal_value(function.args.defaults[index - first_default], environment)


def _guard_contains_call(
    function: ast.FunctionDef,
    *,
    guard_name: str,
    call_name: str,
) -> bool:
    for node in ast.walk(function):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Name):
            continue
        if node.test.id != guard_name:
            continue
        for child in node.body:
            for candidate in ast.walk(child):
                if not isinstance(candidate, ast.Call):
                    continue
                function_node = candidate.func
                if (
                    isinstance(function_node, ast.Attribute)
                    and function_node.attr == call_name
                ):
                    return True
                if (
                    isinstance(function_node, ast.Name)
                    and function_node.id == call_name
                ):
                    return True
    return False


def _contains_call_outside_guard(
    function: ast.FunctionDef,
    *,
    guard_name: str,
    call_name: str,
) -> bool:
    def visit(node: ast.AST, *, guarded: bool) -> bool:
        if isinstance(node, ast.Call):
            function_node = node.func
            observed_name = (
                function_node.attr
                if isinstance(function_node, ast.Attribute)
                else function_node.id if isinstance(function_node, ast.Name) else None
            )
            if observed_name == call_name and not guarded:
                return True
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name):
            if node.test.id == guard_name:
                return any(visit(child, guarded=True) for child in node.body) or any(
                    visit(child, guarded=guarded) for child in node.orelse
                )
        return any(
            visit(child, guarded=guarded) for child in ast.iter_child_nodes(node)
        )

    return visit(function, guarded=False)


def _extract_follower_joint_map(tree: ast.Module) -> list[dict[str, Any]]:
    follower = _find_class(tree, "SOFollower")
    constructor = _find_method(follower, "__init__")
    bus_calls = [
        node
        for node in ast.walk(constructor)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == "FeetechMotorsBus"
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "FeetechMotorsBus"
        )
    ]
    if len(bus_calls) != 1:
        raise ValueError("Census runtime semantics require one SOFollower Feetech bus")
    motors_keyword = next(
        (keyword for keyword in bus_calls[0].keywords if keyword.arg == "motors"),
        None,
    )
    if motors_keyword is None or not isinstance(motors_keyword.value, ast.Dict):
        raise ValueError("Census runtime semantics missing SOFollower motor map")
    result: list[dict[str, Any]] = []
    for key, value in zip(
        motors_keyword.value.keys,
        motors_keyword.value.values,
        strict=True,
    ):
        if (
            not isinstance(key, ast.Constant)
            or not isinstance(key.value, str)
            or not isinstance(value, ast.Call)
            or len(value.args) < 2
        ):
            raise ValueError(
                "Census runtime semantics contain malformed follower motor"
            )
        servo_id = _literal_value(value.args[0], {})
        model = _literal_value(value.args[1], {})
        if isinstance(servo_id, bool) or not isinstance(servo_id, int):
            raise ValueError(
                "Census runtime semantics contain invalid follower servo ID"
            )
        if not isinstance(model, str):
            raise ValueError("Census runtime semantics contain invalid follower model")
        result.append(
            {
                "joint_name": key.value,
                "servo_id": servo_id,
                "model": model,
            }
        )
    return result


def _require_mapping(value: Any, *, label: str) -> dict[Any, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Census runtime semantics missing {label}")
    return value


def _require_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Census runtime semantics require integer {label}")
    return value


def _require_register_width(control_table: dict[Any, Any], register: str) -> int:
    address_and_width = control_table.get(register)
    if (
        not isinstance(address_and_width, tuple)
        or len(address_and_width) != 2
        or isinstance(address_and_width[1], bool)
        or not isinstance(address_and_width[1], int)
    ):
        raise ValueError(f"Census runtime semantics missing register width: {register}")
    return address_and_width[1]

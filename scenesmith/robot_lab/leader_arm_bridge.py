"""Leader-only correction sources for SceneSmith simulated interventions."""

from __future__ import annotations

import math
import shutil
import sys
import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.request import Request, urlopen


DEFAULT_LEADER_PORT = "/dev/cu.usbmodem5B3D0448141"
DEFAULT_STUDIO_URL = "http://127.0.0.1:8790"
KNOWN_PHYSICAL_FOLLOWER_PORT = "/dev/cu.usbmodem5B3D0406411"
JOINT_LIMITS_RAD = (
    (-1.91986, 1.91986),
    (-1.74533, 1.74533),
    (-1.69, 1.69),
    (-1.65806, 1.65806),
    (-2.74385, 2.84121),
    (-0.17453, 1.74533),
)
JOINT_ACTION_KEYS = (
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
)


class CorrectionSource(Protocol):
    name: str

    def get_action(self, phase: str, step_index: int) -> list[float]:
        ...

    def close(self) -> None:
        ...

    def safety_report(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class PhysicalLeaderArmConfig:
    leader_port: str
    leader_config: str
    repo_root: Path
    forbidden_ports: tuple[str, ...] = (KNOWN_PHYSICAL_FOLLOWER_PORT,)


@dataclass(frozen=True)
class StudioLeaderConfig:
    base_url: str = DEFAULT_STUDIO_URL
    timeout_s: float = 0.35


class SimulatedLeaderCorrectionSource:
    """Deterministic test source; it is not evidence of physical teleoperation."""

    name = "simulated_leader"

    def get_action(self, phase: str, step_index: int) -> list[float]:
        scripted = {
            "intervention_approach": [0.05, -0.50, 0.92, -0.40, 0.0, 0.85],
            "intervention_lift": [0.08, -0.38, 0.84, -0.36, 0.0, 0.24],
            "intervention_carry": [0.34, -0.34, 0.70, -0.42, 0.0, 0.22],
            "intervention_place": [0.34, -0.46, 0.94, -0.50, 0.0, 0.95],
        }
        return _clamp_action(
            scripted.get(phase, [0.0, -0.48, 0.88, -0.44, 0.0, 0.5])
        )

    def close(self) -> None:
        return None

    def safety_report(self) -> dict[str, Any]:
        return {
            "source": self.name,
            "hardware_opened": False,
            "physical_follower_commanded": False,
            "proof_scope": "deterministic_test_source",
        }


class PhysicalLeaderCorrectionSource:
    """Read calibrated positions from one SO-101 leader without motor writes."""

    name = "physical_leader"

    def __init__(self, config: PhysicalLeaderArmConfig):
        self._validate_config(config)
        _ensure_lerobot_path(config.repo_root)
        from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
        from lerobot.utils.constants import HF_LEROBOT_CALIBRATION, TELEOPERATORS

        config_name = Path(config.leader_config).stem
        supplied_path = Path(config.leader_config).expanduser()
        cache_dir = HF_LEROBOT_CALIBRATION / TELEOPERATORS / "so_leader"
        cache_path = cache_dir / f"{config_name}.json"
        if supplied_path.is_file() and supplied_path.resolve() != cache_path.resolve():
            cache_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(supplied_path, cache_path)
        if not cache_path.is_file():
            raise FileNotFoundError(
                f"Leader calibration file not found: {cache_path}. "
                "Pass a cached id such as leader_arm or a calibration JSON path."
            )

        self._port = config.leader_port
        self._calibration_path = cache_path
        self._teleop = SO101Leader(
            SO101LeaderConfig(
                port=config.leader_port,
                id=config_name,
                use_degrees=True,
            )
        )
        if not self._teleop.calibration:
            raise RuntimeError(f"Leader calibration did not load from {cache_path}")

        # Deliberately bypass SO101Leader.connect(): it calls configure(), which
        # writes operating modes. A simulation input device only needs reads.
        self._teleop.bus.connect()

    @staticmethod
    def _validate_config(config: PhysicalLeaderArmConfig) -> None:
        if not config.leader_port:
            raise ValueError("--leader-port is required for physical_leader correction")
        if not config.leader_config:
            raise ValueError("--leader-config is required for physical_leader correction")
        resolved = str(Path(config.leader_port))
        forbidden = {str(Path(port)) for port in config.forbidden_ports}
        if resolved in forbidden:
            raise ValueError(f"Refusing to open forbidden non-leader port: {resolved}")

    def get_action(self, phase: str, step_index: int) -> list[float]:
        return _action_to_six_radians(self._teleop.get_action())

    def close(self) -> None:
        teleop = getattr(self, "_teleop", None)
        if teleop is not None and teleop.bus.is_connected:
            teleop.bus.disconnect(disable_torque=False)

    def safety_report(self) -> dict[str, Any]:
        return {
            "source": self.name,
            "leader_port": self._port,
            "calibration_path": str(self._calibration_path),
            "hardware_opened": True,
            "allowed_operations": ["serial_connect", "present_position_sync_read"],
            "motor_register_writes": 0,
            "teardown_disable_torque": False,
            "physical_follower_commanded": False,
        }


class StudioLeaderCorrectionSource:
    """Read calibrated leader telemetry from the already-running Studio broker."""

    name = "studio_leader"

    def __init__(self, config: StudioLeaderConfig = StudioLeaderConfig()):
        self._base_url = config.base_url.rstrip("/")
        self._timeout_s = config.timeout_s
        if not self._base_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("Studio leader source is restricted to the local host")
        self.get_action("connectivity_probe", 0)

    def get_action(self, phase: str, step_index: int) -> list[float]:
        request = Request(f"{self._base_url}/api/parity", method="GET")
        with urlopen(request, timeout=self._timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _studio_payload_to_six_radians(payload)

    def close(self) -> None:
        return None

    def safety_report(self) -> dict[str, Any]:
        return {
            "source": self.name,
            "studio_url": self._base_url,
            "hardware_opened_by_scenesmith": False,
            "allowed_operations": ["local_http_get_api_parity"],
            "motor_register_writes": 0,
            "physical_follower_commanded": False,
        }


def make_correction_source(
    correction_source: str,
    *,
    leader_port: str | None = None,
    leader_config: str | None = None,
    studio_url: str | None = None,
    repo_root: Path | None = None,
) -> CorrectionSource:
    if correction_source == "simulated_leader":
        return SimulatedLeaderCorrectionSource()
    if correction_source == "physical_leader":
        return PhysicalLeaderCorrectionSource(
            PhysicalLeaderArmConfig(
                leader_port=leader_port or DEFAULT_LEADER_PORT,
                leader_config=leader_config or "leader_arm",
                repo_root=repo_root or Path.cwd(),
            )
        )
    if correction_source == "studio_leader":
        return StudioLeaderCorrectionSource(
            StudioLeaderConfig(base_url=studio_url or DEFAULT_STUDIO_URL)
        )
    raise ValueError(f"Unsupported correction source: {correction_source}")


def _ensure_lerobot_path(repo_root: Path) -> None:
    path = repo_root / "external" / "lerobot" / "src"
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _action_to_six_radians(raw_action: Any) -> list[float]:
    """Map LeRobot's degree body joints and 0..100 gripper into MuJoCo."""

    if isinstance(raw_action, dict):
        body = [math.radians(float(raw_action.get(key, 0.0))) for key in JOINT_ACTION_KEYS[:5]]
        gripper_percent = min(100.0, max(0.0, float(raw_action.get(JOINT_ACTION_KEYS[5], 0.0))))
        gripper_low, gripper_high = JOINT_LIMITS_RAD[5]
        gripper = gripper_low + (gripper_high - gripper_low) * gripper_percent / 100.0
        return _clamp_action([*body, gripper])
    if isinstance(raw_action, (list, tuple)):
        return _clamp_action([float(value) for value in raw_action[:6]])
    raise ValueError(f"Unsupported leader action payload: {type(raw_action).__name__}")


def _studio_payload_to_six_radians(payload: dict[str, Any]) -> list[float]:
    if not payload.get("available"):
        raise RuntimeError("Studio leader telemetry is unavailable")
    joints = payload.get("joints")
    if not isinstance(joints, dict):
        raise ValueError("Studio parity payload is missing joints")
    raw = {
        f"{name}.pos": joints.get(name, {}).get("leaderDeg", 0.0)
        for name in (
            "shoulder_pan",
            "shoulder_lift",
            "elbow_flex",
            "wrist_flex",
            "wrist_roll",
            "gripper",
        )
    }
    return _action_to_six_radians(raw)


def _clamp_action(values: list[float]) -> list[float]:
    padded = (values + [0.0] * 6)[:6]
    return [
        round(min(high, max(low, value)), 6)
        for value, (low, high) in zip(padded, JOINT_LIMITS_RAD, strict=True)
    ]

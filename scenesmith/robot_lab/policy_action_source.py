"""Policy action sources for SceneSmith robot-lab control loops."""

from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


DEFAULT_POLICY_ACTION_URL = "http://127.0.0.1:8833"


@dataclass(frozen=True)
class HttpPolicyActionConfig:
    base_url: str = DEFAULT_POLICY_ACTION_URL
    timeout_s: float = 180.0


class HttpPolicyActionSource:
    """Consume actions from the persistent local LeRobot policy service."""

    name = "persistent_lerobot_http"

    def __init__(self, config: HttpPolicyActionConfig = HttpPolicyActionConfig()):
        self.base_url = config.base_url.rstrip("/")
        self.timeout_s = config.timeout_s
        if not self.base_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("Policy action service is restricted to the local host")
        self._status = self._get("/status")
        if not self._status.get("ready"):
            raise RuntimeError("Local policy action service is not ready")
        self.last_response: dict[str, Any] | None = None

    def reset(self, *, seed: int | None = None) -> None:
        self._status = self._post(
            "/reset", {"seed": seed} if seed is not None else {}
        )

    def simulation_home_control(self) -> list[float] | None:
        values = self._status.get("simulation_home_mujoco")
        if values is None:
            return None
        if not isinstance(values, list) or len(values) != 6:
            raise ValueError(f"Policy service returned an invalid simulation home: {values!r}")
        return [float(value) for value in values]

    def get_action(
        self,
        observation: dict[str, Any],
        *,
        episode_dir: Path,
        task: str,
    ) -> list[float]:
        images = {
            role: str((episode_dir / relative).resolve())
            for role, relative in observation["images"].items()
        }
        response = self._post(
            "/action",
            {
                "images": images,
                "state": observation["state"],
                "task": task,
            },
        )
        action = response.get("action_mujoco")
        if not isinstance(action, list) or len(action) < 6:
            raise ValueError(f"Policy service returned an invalid action: {action!r}")
        self.last_response = response
        return [float(value) for value in action[:6]]

    def report(self) -> dict[str, Any]:
        return {
            "kind": self.name,
            "neural_closed_loop": True,
            "observation_updates_per_control_step": True,
            "action_server": self.base_url,
            "server_status": self._status,
            "last_action": self.last_response,
            "physical_follower_commanded": False,
        }

    def _get(self, path: str) -> dict[str, Any]:
        request = Request(f"{self.base_url}{path}", method="GET")
        with urlopen(request, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_s) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "Policy action request failed")
        return result

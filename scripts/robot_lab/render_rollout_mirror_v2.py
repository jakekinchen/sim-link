#!/usr/bin/env python3
"""Render current traces without rewriting the immutable legacy renderer.

The historical T20.43b specification content-addresses
``render_rollout_mirror.py``. This compatibility entrypoint delegates every
existing schema to those exact legacy bytes and adds dispatch for the already
defined T20.43b trace schema. It does not run a policy, optimizer, or physics
rollout.
"""

from __future__ import annotations

import runpy
import sys

from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_RENDERER = REPO_ROOT / "scripts/robot_lab/render_rollout_mirror.py"
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_43b_r1_act_runner import (  # noqa: E402
    TRACE_SCHEMA_VERSION as T20_43B_TRACE_SCHEMA_VERSION,
    verify_trace as verify_t20_43b_trace,
)


def dispatch_trace(
    path: Path, *, legacy_loader: Callable[[Path], dict[str, Any]]
) -> dict[str, Any]:
    """Verify T20.43b locally and delegate every legacy schema unchanged."""

    payload = load_strict_json(path)
    if payload.get("schema_version") != T20_43B_TRACE_SCHEMA_VERSION:
        return legacy_loader(path)
    verify_signed_payload(payload, label="rollout mirror source trace")
    verify_t20_43b_trace(payload)
    return payload


def _legacy_namespace() -> dict[str, Any]:
    return runpy.run_path(str(LEGACY_RENDERER))


def load_trace(path: Path) -> dict[str, Any]:
    namespace = _legacy_namespace()
    return dispatch_trace(path, legacy_loader=namespace["_load_trace"])


def main() -> int:
    namespace = _legacy_namespace()
    legacy_loader = namespace["_load_trace"]
    legacy_main = namespace["main"]
    legacy_main.__globals__["_load_trace"] = lambda path: dispatch_trace(
        path, legacy_loader=legacy_loader
    )
    return int(legacy_main())


if __name__ == "__main__":
    raise SystemExit(main())

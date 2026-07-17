#!/usr/bin/env python3
"""Render current traces without rewriting the immutable legacy renderer.

The historical T20.43b specification content-addresses
``render_rollout_mirror.py``. This compatibility entrypoint delegates every
existing schema to those exact legacy bytes and adds dispatch for the already
defined T20.43b and F0b trace schemas. It does not run a policy, optimizer, or
physics rollout.
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
from scenesmith.robot_lab.f0b_hybrid_tail_cadence import (  # noqa: E402
    TRACE_SCHEMA as F0B_TRACE_SCHEMA,
    _source_episode_zero as load_f0b_source_episode_zero,
    verify_trace as verify_f0b_trace,
)


def dispatch_trace(
    path: Path, *, legacy_loader: Callable[[Path], dict[str, Any]]
) -> dict[str, Any]:
    """Verify current schemas locally and delegate legacy schemas unchanged."""

    payload = load_strict_json(path)
    schema = payload.get("schema_version")
    if schema == T20_43B_TRACE_SCHEMA_VERSION:
        verify_signed_payload(payload, label="rollout mirror source trace")
        verify_t20_43b_trace(payload)
        return payload
    if schema == F0B_TRACE_SCHEMA:
        verify_signed_payload(payload, label="rollout mirror source trace")
        verify_f0b_trace(payload)
        return payload
    return legacy_loader(path)


def _legacy_namespace() -> dict[str, Any]:
    return runpy.run_path(str(LEGACY_RENDERER))


def load_trace(path: Path) -> dict[str, Any]:
    namespace = _legacy_namespace()
    return dispatch_trace(path, legacy_loader=namespace["_load_trace"])


def dispatch_source_episode(
    trace: dict[str, Any],
    seed: int,
    *,
    legacy_loader: Callable[[int], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Use F0b's exact hash-bound source episode; preserve legacy routing otherwise."""

    if trace.get("schema_version") != F0B_TRACE_SCHEMA:
        return legacy_loader(seed)
    if seed != 0:
        raise ValueError("F0b renderer seed drifted")
    _, frames = load_f0b_source_episode_zero(REPO_ROOT)
    return frames


def main() -> int:
    namespace = _legacy_namespace()
    legacy_loader = namespace["_load_trace"]
    legacy_source_loader = namespace["_source_episode_frames"]
    legacy_main = namespace["main"]
    loaded: dict[str, dict[str, Any]] = {}

    def routed_trace(path: Path) -> dict[str, Any]:
        payload = dispatch_trace(path, legacy_loader=legacy_loader)
        loaded["trace"] = payload
        return payload

    legacy_main.__globals__["_load_trace"] = routed_trace
    legacy_main.__globals__["_source_episode_frames"] = lambda seed: (
        dispatch_source_episode(
            loaded["trace"], seed, legacy_loader=legacy_source_loader
        )
    )
    return int(legacy_main())


if __name__ == "__main__":
    raise SystemExit(main())

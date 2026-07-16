#!/usr/bin/env python3
"""Write or verify the terminal receipt for the consumed T20.43 attempt."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys

from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_43_r1_act_contracts import (  # noqa: E402
    ATTEMPT_PATH,
    PERMIT_PATH,
    RUN_ROOT,
    verify_attempt_marker,
)
from scenesmith.robot_lab.t20_43_r1_act_runner import verify_trace  # noqa: E402

FAILURE_PATH = Path("configurations/robot_lab/t20_43_r1_act_terminal_failure.json")
CHECKPOINT_PATH = RUN_ROOT / "checkpoints/step_00000"
TRACE_PATH = RUN_ROOT / "rollouts/step_00000_chunk_50.json"
VIDEO_PATH = RUN_ROOT / "mirrors/step_00000_chunk_50.mp4"
EXPECTED_PARTIAL_FILES = {
    "checkpoints/step_00000/config.json",
    "checkpoints/step_00000/model.safetensors",
    "rollouts/step_00000_chunk_50.json",
}


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"T20.43 partial output contains a symlink: {path}")
        if path.is_file():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha_file(path),
                }
            )
    return rows


def _aware_time(value: str, *, label: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"T20.43 {label} must include a UTC offset")
    return parsed


def build_receipt(*, terminated_at: str) -> dict[str, object]:
    permit = load_strict_json(REPO_ROOT / PERMIT_PATH)
    attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
    verify_attempt_marker(attempt, permit=permit)
    started = _aware_time(attempt["started_at"], label="attempt start")
    terminated = _aware_time(terminated_at, label="termination time")
    if terminated < started:
        raise ValueError("T20.43 termination precedes the attempt marker")

    trace = load_strict_json(REPO_ROOT / TRACE_PATH)
    verify_trace(trace)
    if (
        trace["optimizer_update_count"] != 0
        or trace["n_action_steps"] != 50
        or trace["seed"] != 0
        or trace["optimizer_training_preceded_this_checkpoint"] is not False
        or trace["model_inference_executed"] is not True
        or trace["simulation_policy_accepted"] is not False
    ):
        raise ValueError(
            "T20.43 partial trace is not the checkpoint-0 chunk-50 negative"
        )

    rows = _file_rows(REPO_ROOT / RUN_ROOT)
    if {row["path"] for row in rows} != EXPECTED_PARTIAL_FILES:
        raise ValueError("T20.43 partial output set drifted")
    checkpoint_rows = [
        {
            "path": row["path"].removeprefix("checkpoints/step_00000/"),
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
        }
        for row in rows
        if str(row["path"]).startswith("checkpoints/step_00000/")
    ]
    checkpoint_identity = hashlib.sha256(
        canonical_json_bytes(checkpoint_rows)
    ).hexdigest()
    if checkpoint_identity != trace["checkpoint_identity_sha256"]:
        raise ValueError("T20.43 checkpoint tree identity drifted")
    if VIDEO_PATH.exists() or VIDEO_PATH.is_symlink():
        raise ValueError("T20.43 failed mirror path unexpectedly exists")

    child_python = REPO_ROOT / "external/lerobot/.venv/bin/python"
    child_probe = subprocess.run(
        [str(child_python), "-c", "import mujoco"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    child_stderr = child_probe.stderr.decode("utf-8", errors="strict")
    if child_probe.returncode != 1 or "No module named 'mujoco'" not in child_stderr:
        raise ValueError(
            "T20.43 renderer child dependency failure no longer reproduces"
        )

    import mujoco

    if mujoco.__version__ != "3.3.5":
        raise ValueError("T20.43 main runtime MuJoCo version drifted")

    absent_terminal_paths = [
        "outputs/robot_lab/t20_43_r1_act_run_001/run_summary.json",
        "configurations/robot_lab/t20_43_r1_act_result.json",
        "configurations/robot_lab/t20_43_r1_act_scorecard.json",
        "configurations/robot_lab/t20_43_r1_act_retention_receipt.json",
    ]
    if any(
        (REPO_ROOT / path).exists() or (REPO_ROOT / path).is_symlink()
        for path in absent_terminal_paths
    ):
        raise ValueError("T20.43 full-result path unexpectedly exists")

    trace_row = next(
        row
        for row in rows
        if row["path"] == TRACE_PATH.relative_to(RUN_ROOT).as_posix()
    )
    return sign_payload(
        {
            "schema_version": "scenesmith.t20_43_r1_act_terminal_failure.v1",
            "task_id": "T20.43",
            "status": "verified_terminal_infrastructure_failure",
            "attempt_identity_sha256": attempt["identity_sha256"],
            "attempt_file_sha256": _sha_file(REPO_ROOT / ATTEMPT_PATH),
            "permit_identity_sha256": permit["identity_sha256"],
            "attempt_count": 1,
            "permit_consumed": True,
            "started_at": attempt["started_at"],
            "terminated_at": terminated.isoformat(),
            "failure": {
                "code": "RENDERER_CHILD_DEPENDENCY_MISSING",
                "stage": "checkpoint_0_chunk_50_mirror_render",
                "exception_type": "ModuleNotFoundError",
                "exception_message": "No module named 'mujoco'",
                "renderer_child_interpreter": "external/lerobot/.venv/bin/python",
                "renderer_child_import_exit_code": child_probe.returncode,
                "renderer_child_import_stderr_sha256": hashlib.sha256(
                    child_probe.stderr
                ).hexdigest(),
                "main_runtime_mujoco_version": mujoco.__version__,
                "preflight_environment_mismatch": True,
            },
            "execution": {
                "fresh_act_policy_constructed": True,
                "cached_backbone_deserialized": True,
                "optimizer_created": True,
                "optimizer_training_executed": False,
                "optimizer_update_count": 0,
                "checkpoint_count": 1,
                "policy_inference_executed": True,
                "policy_owned_rollout_count": 1,
                "trained_policy_rollout_count": 0,
                "gate_c_evaluation_executed": True,
                "gate_c_passed": False,
                "simulation_policy_accepted": False,
                "completed_mirror_count": 0,
            },
            "checkpoint_0": {
                "identity_sha256": checkpoint_identity,
                "files": checkpoint_rows,
            },
            "chunk_50_trace": {
                "path": TRACE_PATH.as_posix(),
                "schema_version": trace["schema_version"],
                "identity_sha256": trace["identity_sha256"],
                "file_sha256": trace_row["sha256"],
                "size_bytes": trace_row["size_bytes"],
                "strict_v2_passed": trace["t20_38_runtime_receipt"]["strict_v2_passed"],
                "strict_contact_frame_count": trace["diagnostics"][
                    "strict_contact_frame_count"
                ],
                "lift_displacement_m": trace["t20_38_runtime_receipt"][
                    "strict_v2_margins"
                ]["lift_displacement_m"]["measured"],
                "decode_start_frames": trace["decode_start_frames"],
                "executed_lengths": trace["executed_lengths"],
                "unexecuted_tail_actions_excluded": trace[
                    "unexecuted_tail_actions_excluded"
                ],
            },
            "partial_output_files": rows,
            "partial_output_file_count": len(rows),
            "absent_full_result_paths": absent_terminal_paths,
            "large_partial_outputs_tracked_in_git": False,
            "compact_failure_receipt_tracked_in_git": True,
            "raw_partial_outputs_rewritten": False,
            "retry_authorized": False,
            "retry_executed": False,
            "r2_activated": False,
            "hardware_accessed": False,
            "camera_accessed": False,
            "serial_accessed": False,
            "physical_motion": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_receipt(payload: dict[str, object]) -> None:
    verify_signed_payload(payload, label="T20.43 terminal failure")
    expected = build_receipt(terminated_at=str(payload.get("terminated_at")))
    if payload != expected:
        raise ValueError("T20.43 terminal failure receipt drifted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--terminated-at")
    args = parser.parse_args()
    if args.verify:
        payload = load_strict_json(REPO_ROOT / FAILURE_PATH)
        verify_receipt(payload)
    else:
        if not args.terminated_at:
            parser.error("writing the failure receipt requires --terminated-at")
        if (REPO_ROOT / FAILURE_PATH).exists():
            raise FileExistsError("T20.43 terminal failure receipt already exists")
        payload = build_receipt(terminated_at=args.terminated_at)
        dump_canonical_json(REPO_ROOT / FAILURE_PATH, payload)
        payload = load_strict_json(REPO_ROOT / FAILURE_PATH)
        verify_receipt(payload)
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

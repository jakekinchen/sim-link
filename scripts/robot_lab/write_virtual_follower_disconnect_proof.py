#!/usr/bin/env python3
"""Write or verify the consumed one-call virtual follower disconnect proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys

from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    enumerate_serial_identity_holders,
    require_no_serial_identity_holders,
)
from scenesmith.robot_lab.virtual_follower_disconnect_proof import (
    PERMIT_SOURCE_COMMIT,
    PERMIT_SOURCE_PATH,
    build_private_virtual_disconnect_evidence,
    build_redacted_virtual_disconnect_proof,
    verify_private_virtual_disconnect_evidence,
    verify_redacted_virtual_disconnect_proof,
    write_private_virtual_disconnect_evidence,
)


DEFAULT_PROJECT_STATE = Path("docs/autonomous-workflow/project_state.json")
DEFAULT_OBSERVATION_INPUT = Path(
    "outputs/robot_lab/virtual_disconnect/private/20260711-0857/observation.json"
)
DEFAULT_PRIVATE_EVIDENCE = Path(
    "outputs/robot_lab/virtual_disconnect/private/20260711-0857/"
    "private_virtual_disconnect.json"
)
DEFAULT_REDACTED_PROOF = Path(
    "configurations/robot_lab/pi05_virtual_follower_disconnect.redacted.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--project-state", type=Path, default=DEFAULT_PROJECT_STATE)
    parser.add_argument(
        "--observation-input",
        type=Path,
        default=DEFAULT_OBSERVATION_INPUT,
    )
    parser.add_argument(
        "--private-evidence",
        type=Path,
        default=DEFAULT_PRIVATE_EVIDENCE,
    )
    parser.add_argument(
        "--redacted-proof",
        type=Path,
        default=DEFAULT_REDACTED_PROOF,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_path = _resolve_repo_path(args.project_state)
    private_path = _resolve_private_path(args.private_evidence)
    redacted_path = _resolve_redacted_path(args.redacted_proof)
    state = load_strict_json(state_path)
    if state["tasks"]["T16.5b"]["live_gate"] != "closed":
        raise ValueError("Disconnect proof maintenance requires the live gate closed")
    private_reference_path = str(private_path.relative_to(REPO_ROOT))
    if args.verify:
        private = load_strict_json(private_path)
        _verify_permit_source_file(private["permit_source_file_sha256"])
        redacted = load_strict_json(redacted_path)
        reference = {
            "path": private_reference_path,
            "schema_version": private["schema_version"],
            "identity_sha256": private["identity_sha256"],
            "file_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
            "size_bytes": private_path.stat().st_size,
        }
        verify_private_virtual_disconnect_evidence(
            private,
            project_state=state,
        )
        verify_redacted_virtual_disconnect_proof(
            redacted,
            private_evidence=private,
            private_evidence_reference=reference,
            project_state=state,
        )
        status = "verified"
    else:
        observation = load_strict_json(_resolve_private_path(args.observation_input))
        _verify_permit_source_file(observation["permit_source_file_sha256"])
        follower_alias = KNOWN_PHYSICAL_FOLLOWER_PORT.replace(
            "/dev/cu.", "/dev/tty.", 1
        )
        holder_snapshot = enumerate_serial_identity_holders(
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            [follower_alias],
        )
        require_no_serial_identity_holders(holder_snapshot)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        private = build_private_virtual_disconnect_evidence(
            project_state=state,
            observation=observation,
            post_holder_snapshot=holder_snapshot,
            post_holder_revalidated_at=now,
        )
        reference = write_private_virtual_disconnect_evidence(
            path=private_path,
            evidence=private,
            reference_path=private_reference_path,
        )
        redacted = build_redacted_virtual_disconnect_proof(
            private_evidence=private,
            private_evidence_reference=reference,
        )
        if redacted_path.exists():
            raise ValueError("Tracked virtual disconnect proof must be new")
        dump_canonical_json(redacted_path, redacted)
        status = "written"
    print(
        json.dumps(
            {
                "status": status,
                "private_evidence_identity_sha256": private["identity_sha256"],
                "redacted_proof_identity_sha256": redacted["identity_sha256"],
                "permit_identity_sha256": redacted["permit_identity_sha256"],
                "observed_call_count": redacted["observed_call_count"],
                "additional_calls_allowed": redacted[
                    "additional_calls_allowed"
                ],
                "deduplicated_holder_count": redacted[
                    "serial_holder_evidence"
                ]["deduplicated_holder_count"],
                "physical_motion_commanded": redacted[
                    "physical_motion_commanded"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_repo_path(path: Path) -> Path:
    resolved = path if path.is_absolute() else REPO_ROOT / path
    try:
        resolved.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Disconnect proof path escapes the repository") from exc
    return resolved


def _resolve_private_path(path: Path) -> Path:
    resolved = _resolve_repo_path(path)
    private_root = (REPO_ROOT / "outputs/robot_lab/virtual_disconnect/private").resolve()
    try:
        resolved.resolve().relative_to(private_root)
    except ValueError as exc:
        raise ValueError("Disconnect proof private path is outside the private root") from exc
    return resolved


def _resolve_redacted_path(path: Path) -> Path:
    resolved = _resolve_repo_path(path)
    expected = (REPO_ROOT / DEFAULT_REDACTED_PROOF).resolve()
    if resolved.resolve() != expected:
        raise ValueError("Disconnect proof tracked path is not canonical")
    return resolved


def _verify_permit_source_file(expected_sha256: str) -> None:
    result = subprocess.run(
        [
            "/usr/bin/git",
            "show",
            f"{PERMIT_SOURCE_COMMIT}:{PERMIT_SOURCE_PATH}",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        timeout=10,
    )
    observed = hashlib.sha256(result.stdout).hexdigest()
    if observed != expected_sha256:
        raise ValueError("Disconnect permit source file hash drifted")


if __name__ == "__main__":
    raise SystemExit(main())

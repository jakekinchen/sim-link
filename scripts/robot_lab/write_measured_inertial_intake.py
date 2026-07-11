#!/usr/bin/env python3
"""Write or verify truthful measured-mass intake and assembly inertial artifacts."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.measured_inertial_intake import (
    DEFAULT_ASSEMBLY_INERTIALS_PATH,
    DEFAULT_MEASURED_MASS_INTAKE_PATH,
    require_compilation_ready,
    require_physical_transfer_authority,
    require_promotion_authority,
    require_ready_or_raise,
    require_simulation_training_authority,
    verify_assembly_inertials,
    verify_measured_mass_intake,
    write_assembly_inertials,
    write_measured_mass_intake,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intake",
        type=Path,
        default=DEFAULT_MEASURED_MASS_INTAKE_PATH,
        help="Measured-mass intake artifact path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ASSEMBLY_INERTIALS_PATH,
        help="Assembly inertials artifact path.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the tracked artifacts instead of rewriting them.",
    )
    parser.add_argument(
        "--write-intake",
        action="store_true",
        help="Rewrite the deterministic awaiting-measurements intake before compiling output.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Deprecated ambiguous gate; always fails. Choose an explicit authority flag.",
    )
    parser.add_argument("--require-compilation-ready", action="store_true")
    parser.add_argument("--require-simulation-training-authority", action="store_true")
    parser.add_argument("--require-physical-transfer-authority", action="store_true")
    parser.add_argument("--require-promotion-authority", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    intake_path = _resolve(args.intake)
    output_path = _resolve(args.output)
    intake_rel = _relative_to_repo(intake_path)
    output_rel = _relative_to_repo(output_path)

    if args.verify:
        intake_payload = json.loads(intake_path.read_text(encoding="utf-8"))
        output_payload = json.loads(output_path.read_text(encoding="utf-8"))
        verify_measured_mass_intake(
            intake_payload,
            repo_root=REPO_ROOT,
        )
        verify_assembly_inertials(
            output_payload,
            repo_root=REPO_ROOT,
            intake_path=intake_rel,
        )
        try:
            _apply_requested_authority(args, output_payload)
        except ValueError as exc:
            print(
                json.dumps(
                    {
                        "status": output_payload["status"],
                        "artifact": str(args.output),
                        "ready": False,
                        "reason": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 1
        print(
            json.dumps(
                {
                    "status": "verified",
                    "intake": str(args.intake),
                    "output": str(args.output),
                    "intake_identity_sha256": intake_payload["identity_sha256"],
                    "output_identity_sha256": output_payload["identity_sha256"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.write_intake:
        intake_payload = write_measured_mass_intake(
            repo_root=REPO_ROOT,
            output_path=intake_rel,
        )
    else:
        intake_payload = json.loads(intake_path.read_text(encoding="utf-8"))
        verify_measured_mass_intake(intake_payload, repo_root=REPO_ROOT)
    output_payload = write_assembly_inertials(
        repo_root=REPO_ROOT,
        intake_path=intake_rel,
        output_path=output_rel,
    )
    try:
        _apply_requested_authority(args, output_payload)
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "status": output_payload["status"],
                    "artifact": str(args.output),
                    "ready": False,
                    "reason": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "written",
                "intake": str(args.intake),
                "output": str(args.output),
                "intake_identity_sha256": intake_payload["identity_sha256"],
                "output_identity_sha256": output_payload["identity_sha256"],
                "output_status": output_payload["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _relative_to_repo(path: Path) -> Path:
    if not path.is_absolute():
        return path
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def _apply_requested_authority(args: argparse.Namespace, payload: dict) -> None:
    gates = (
        (args.require_ready, require_ready_or_raise),
        (args.require_compilation_ready, require_compilation_ready),
        (args.require_simulation_training_authority, require_simulation_training_authority),
        (args.require_physical_transfer_authority, require_physical_transfer_authority),
        (args.require_promotion_authority, require_promotion_authority),
    )
    selected = [gate for enabled, gate in gates if enabled]
    if len(selected) > 1:
        raise ValueError("Choose exactly one measured-inertial authority gate")
    if selected:
        selected[0](payload)


if __name__ == "__main__":
    raise SystemExit(main())

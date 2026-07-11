#!/usr/bin/env python3
"""Write or verify the offline static-pose-bracket contract and fixture."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.static_pose_bracket import (
    build_fixture_static_pose_observation,
    build_static_pose_bracket_contract,
    evaluate_static_pose_bracket,
    verify_static_pose_bracket_contract,
    verify_static_pose_bracket_result,
)


DEFAULT_CALIBRATION = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
DEFAULT_PROFILE = Path("configurations/robot_lab/pi05_calibration_profile.json")
DEFAULT_MANIFEST = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
DEFAULT_CONTRACT = Path(
    "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
)
DEFAULT_OBSERVATION = Path(
    "tests/fixtures/robot_lab/static_pose_bracket/observation.fixture.json"
)
DEFAULT_RESULT = Path(
    "tests/fixtures/robot_lab/static_pose_bracket/result.fixture.json"
)
EXPECTED_PREDECESSOR_IDENTITIES = {
    "contract": "90e7baea43ebc059c09ef45b615c5808cf74abbbab87948a23536666acb43ceb",
    "observation": "84d0aa12687574be6bae575f74dcb7e68c9b5643e4e086c9e1461f4e91bb64a4",
    "result": "6ebb9bd63c7267f193f4754af11012ac6e768404749891f4033381fa4ad0a410",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify", action="store_true")
    action.add_argument("--refresh-derived", action="store_true")
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--observation", type=Path, default=DEFAULT_OBSERVATION)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    calibration_path = _resolve_calibration(args.calibration)
    profile_path = _resolve_repo_file(args.profile, expected=DEFAULT_PROFILE)
    manifest_path = _resolve_repo_file(args.manifest, expected=DEFAULT_MANIFEST)
    contract_path = _resolve_repo_file(args.contract, expected=DEFAULT_CONTRACT)
    observation_path = _resolve_repo_file(
        args.observation,
        expected=DEFAULT_OBSERVATION,
    )
    result_path = _resolve_repo_file(args.result, expected=DEFAULT_RESULT)

    if args.verify:
        contract = load_strict_json(contract_path)
        observation = load_strict_json(observation_path)
        result = load_strict_json(result_path)
        verify_static_pose_bracket_contract(
            contract,
            calibration_path=calibration_path,
            calibration_profile_path=profile_path,
            manifest_path=manifest_path,
        )
        verify_static_pose_bracket_result(
            result,
            contract=contract,
            observation=observation,
        )
        status = "verified"
    elif args.refresh_derived:
        predecessor = {
            "contract": load_strict_json(contract_path),
            "observation": load_strict_json(observation_path),
            "result": load_strict_json(result_path),
        }
        if {
            name: payload.get("identity_sha256")
            for name, payload in predecessor.items()
        } != EXPECTED_PREDECESSOR_IDENTITIES:
            raise ValueError("Static pose artifacts are not the exact predecessors")
        contract = build_static_pose_bracket_contract(
            calibration_path=calibration_path,
            calibration_profile_path=profile_path,
            manifest_path=manifest_path,
        )
        observation = build_fixture_static_pose_observation(contract)
        result = evaluate_static_pose_bracket(
            contract=contract,
            observation=observation,
        )
        dump_canonical_json(contract_path, contract)
        dump_canonical_json(observation_path, observation)
        dump_canonical_json(result_path, result)
        status = "refreshed"
    else:
        outputs = (contract_path, observation_path, result_path)
        if any(path.exists() for path in outputs):
            raise ValueError("Static pose bracket outputs already exist; use --verify")
        contract = build_static_pose_bracket_contract(
            calibration_path=calibration_path,
            calibration_profile_path=profile_path,
            manifest_path=manifest_path,
        )
        observation = build_fixture_static_pose_observation(contract)
        result = evaluate_static_pose_bracket(
            contract=contract,
            observation=observation,
        )
        dump_canonical_json(contract_path, contract)
        dump_canonical_json(observation_path, observation)
        dump_canonical_json(result_path, result)
        status = "written"

    print(
        json.dumps(
            {
                "status": status,
                "contract_identity_sha256": contract["identity_sha256"],
                "observation_identity_sha256": observation["identity_sha256"],
                "result_identity_sha256": result["identity_sha256"],
                "static_pose_within_tolerance": result[
                    "static_pose_within_tolerance"
                ],
                "physical_follower_commanded": result[
                    "physical_follower_commanded"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_calibration(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved != DEFAULT_CALIBRATION.resolve():
        raise ValueError("Calibration path is not the pinned follower calibration")
    if not resolved.is_file():
        raise ValueError("Pinned follower calibration file is missing")
    return resolved


def _resolve_repo_file(path: Path, *, expected: Path) -> Path:
    resolved = (path if path.is_absolute() else REPO_ROOT / path).resolve()
    if resolved != (REPO_ROOT / expected).resolve():
        raise ValueError(f"Path is not canonical: {expected}")
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())

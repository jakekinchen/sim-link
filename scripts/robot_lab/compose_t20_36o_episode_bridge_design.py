#!/usr/bin/env python3
"""Compose or verify the model-free T20.36o episode bridge design."""

from __future__ import annotations

import argparse

from scenesmith.robot_lab.artifact_contract import dump_canonical_json
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (
    REPO_ROOT,
    SPEC_PATH,
    build_bridge_spec,
    load_verified_sources,
    verify_bridge_spec_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        spec = verify_bridge_spec_file()
        print(spec["identity_sha256"])
        return 0
    path = REPO_ROOT / SPEC_PATH
    if path.exists():
        raise FileExistsError("T20.36o bridge design exists; use --verify")
    spec = build_bridge_spec(sources=load_verified_sources())
    dump_canonical_json(path, spec)
    print(spec["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

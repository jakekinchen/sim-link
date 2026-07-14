#!/usr/bin/env python3
"""Write or verify one uniform robot-lab artifact by registry name."""

from __future__ import annotations

import argparse
import importlib
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.artifact_writer_registry import ARTIFACT_WRITERS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, choices=sorted(ARTIFACT_WRITERS))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument(
        "--rewrite",
        action="store_true",
        help="Regenerate an existing artifact after an intentional dependency change.",
    )
    parser.add_argument("--output", type=Path, help="Override the registry output path.")
    args = parser.parse_args()
    spec = ARTIFACT_WRITERS[args.name]
    module = importlib.import_module(spec.module)
    builder = getattr(module, spec.builder)
    verifier = getattr(module, spec.verifier)
    output = args.output or (REPO_ROOT / spec.output)
    if not output.is_absolute():
        output = REPO_ROOT / output
    kwargs = {"repo_root": REPO_ROOT} if spec.pass_repo_root else {}
    payload = builder(**kwargs)
    if args.verify:
        stored = load_strict_json(output)
        if stored != payload:
            raise ValueError(f"Checked {args.name} artifact drifted")
        status = "verified"
    elif args.rewrite:
        dump_canonical_json(output, payload)
        status = "rewritten"
    else:
        if output.exists() or output.is_symlink():
            raise ValueError(f"{args.name} artifact exists; use --verify or --rewrite")
        dump_canonical_json(output, payload)
        status = "written"
    verify_kwargs = {"repo_root": REPO_ROOT} if spec.pass_repo_root else {}
    verifier(load_strict_json(output), **verify_kwargs)
    print(
        json.dumps(
            {
                "name": args.name,
                "status": status,
                "output": str(output.relative_to(REPO_ROOT)),
                "identity_sha256": payload.get("identity_sha256"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Write or verify the centered bilateral contact-face audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.centered_contact_face_audit import build_centered_contact_face_audit, verify_centered_contact_face_audit

OUTPUT = REPO_ROOT / "configurations/robot_lab/centered_contact_face_audit.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_centered_contact_face_audit()
    if args.verify:
        if load_strict_json(OUTPUT) != payload:
            raise ValueError("Checked centered contact-face audit drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("Centered contact-face audit exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_centered_contact_face_audit(load_strict_json(OUTPUT))
    print(json.dumps({"status": status, "identity_sha256": payload["identity_sha256"], "candidate_count": len(payload["candidates"]), "diagnostic_frame_counts": {str(row["candidate_index"]): len(row["contact_phase_diagnostics"]) for row in payload["candidates"]}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

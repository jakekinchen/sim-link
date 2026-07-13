#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.normalization_bundle import BUNDLE_PATH, build_normalization_bundle, verify_normalization_bundle
def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--verify",action="store_true"); args=parser.parse_args(); path=REPO_ROOT/BUNDLE_PATH
    payload=build_normalization_bundle(repo_root=REPO_ROOT)
    if args.verify:
        if load_strict_json(path)!=payload: raise ValueError("Checked normalization bundle drifted")
        status="verified"
    else:
        if path.exists() or path.is_symlink(): raise ValueError("Normalization bundle exists; use --verify")
        dump_canonical_json(path,payload); status="written"
    verify_normalization_bundle(load_strict_json(path),repo_root=REPO_ROOT)
    print(json.dumps({"status":status,"identity_sha256":payload["identity_sha256"],"sample_count":payload["normalization"]["sample_count"],"production_eligible":payload["production_eligible"]},indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())

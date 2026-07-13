#!/usr/bin/env python3
"""Write or verify the identical pad-midpoint search."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(REPO_ROOT))
from scenesmith.robot_lab.artifact_contract import dump_canonical_json,load_strict_json
from scenesmith.robot_lab.pad_midpoint_search import build_pad_midpoint_search,verify_pad_midpoint_search
OUTPUT=REPO_ROOT/"configurations/robot_lab/pad_midpoint_search.json"
def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--verify",action="store_true");a=p.parse_args();x=build_pad_midpoint_search()
 if a.verify:
  if load_strict_json(OUTPUT)!=x:raise ValueError("Checked pad-midpoint search drifted")
  s="verified"
 else:
  if OUTPUT.exists() or OUTPUT.is_symlink():raise ValueError("Pad-midpoint search exists; use --verify")
  dump_canonical_json(OUTPUT,x);s="written"
 verify_pad_midpoint_search(load_strict_json(OUTPUT));print(json.dumps({"status":s,"identity_sha256":x["identity_sha256"],"candidate_count":x["training_candidate_count"],"bilateral_contact_candidates":x["bilateral_contact_candidate_count"],"eligible_count":x["geometry_eligible_count"],"holdout_eligible":x["holdout"]["candidate"]["geometry_eligible"]},indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())

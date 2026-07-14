#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scenesmith.robot_lab.artifact_contract import canonical_json_bytes,dump_canonical_json,load_strict_json
from scenesmith.robot_lab.dataset_mixture_freeze import INPUT_PATH,MIXTURE_PATH,build_manifests,verify_manifests
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');p.add_argument('--rewrite',action='store_true');a=p.parse_args()
 if a.rewrite: raise ValueError('T18.5 mixture is immutable; write a reviewed successor')
 if a.verify:
  if not MIXTURE_PATH.is_file() or not INPUT_PATH.is_file(): raise ValueError('T18.5 manifests are absent')
  mixture=load_strict_json(MIXTURE_PATH);training=load_strict_json(INPUT_PATH);verify_manifests(mixture,training);status='verified'
 else:
  if MIXTURE_PATH.exists() or INPUT_PATH.exists(): raise ValueError('T18.5 manifests exist; use --verify')
  mixture,training=build_manifests();verify_manifests(mixture,training);dump_canonical_json(MIXTURE_PATH,mixture);dump_canonical_json(INPUT_PATH,training);status='written'
 print(json.dumps({'status':status,'window_count':mixture['window_count'],'correction_window_count':mixture['correction_window_count'],'dataset_mixture_frozen':mixture['dataset_mixture_frozen'],'training_eligible':training['training_eligible']},sort_keys=True,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

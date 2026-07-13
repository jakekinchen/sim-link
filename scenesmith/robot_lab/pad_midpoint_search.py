"""Identical explicit-pad search with pad-midpoint object targeting."""
from __future__ import annotations
from typing import Any
from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload, verify_signed_payload
from scenesmith.robot_lab.geometry_first_grasp_search import REPO_ROOT, RANGES, TRAINING_CANDIDATES, _candidate, _rank
SCHEMA_VERSION="scenesmith.pad_midpoint_grasp_search.v1"
SOURCE=REPO_ROOT/"configurations/robot_lab/explicit_pad_proxy_search.json"
def build_pad_midpoint_search()->dict[str,Any]:
    source=load_strict_json(SOURCE); verify_signed_payload(source,label="source explicit-pad search")
    candidates=[_midpoint_candidate(i,holdout=False) for i in range(1,TRAINING_CANDIDATES+1)]
    eligible=[row for row in candidates if row["geometry_eligible"]]; selected=min(eligible,key=_rank) if eligible else None
    holdout=_midpoint_candidate(TRAINING_CANDIDATES+1,holdout=True)
    return sign_payload({"schema_version":SCHEMA_VERSION,"evidence_mode":"identical_search_pad_midpoint_targeting","source_explicit_pad_search_identity_sha256":source["identity_sha256"],"candidate_design_identical_to_source":True,"contact_physics_unchanged":True,"ranges":{k:list(v) for k,v in RANGES.items()},"training_candidate_count":len(candidates),"bilateral_contact_candidate_count":sum(row.get("close_pad_contact_frame_count",0)>0 for row in candidates),"geometry_eligible_count":len(eligible),"candidates":candidates,"selected_candidate":selected,"holdout":{"excluded_from_selection":True,"candidate":holdout},"actual_mujoco_grasp_success":False,"simulation_training_ready":False,"hardware_accessed":False,"physical_follower_commanded":False,"authority_not_granted":["unassisted_mujoco_grasp_success","simulation_training_ready","physical_actuation"]})
def _midpoint_candidate(index:int,*,holdout:bool)->dict[str,Any]:
    row=_candidate(index,holdout=holdout,explicit_pad_proxy_only=True,pad_midpoint_targeting=True)
    if not row.get("setup_valid"): return row
    row["base_contact_geometry_eligible"]=row["geometry_eligible"]
    row["approach_object_motion_valid"]=row["preclose_object_displacement_m"]<=0.0001
    row["nonpad_contact_valid"]=row["nonpad_robot_object_contact_frame_count"]==0
    row["geometry_eligible"]=bool(row["base_contact_geometry_eligible"] and row["approach_object_motion_valid"] and row["nonpad_contact_valid"])
    return row
def verify_pad_midpoint_search(payload:dict[str,Any])->None:
    verify_signed_payload(payload,label="pad-midpoint search"); candidates=payload.get("candidates",[])
    if payload.get("training_candidate_count")!=len(candidates): raise ValueError("Pad-midpoint candidate count drifted")
    if not payload.get("candidate_design_identical_to_source") or not payload.get("contact_physics_unchanged"): raise ValueError("Pad-midpoint isolation drifted")
    if payload.get("geometry_eligible_count")!=sum(row["geometry_eligible"] for row in candidates): raise ValueError("Pad-midpoint eligibility drifted")

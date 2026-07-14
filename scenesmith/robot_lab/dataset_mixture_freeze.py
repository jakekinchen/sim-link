"""Deterministic, reference-only T18.5 dataset-mixture freeze."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import pyarrow.parquet as pq
from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, load_strict_json, sign_payload, verify_signed_payload
from scenesmith.robot_lab.episode_first_window_sampling import verify_episode_first_window_sample
from scenesmith.robot_lab.exact_state_components import ACTOR_INPUT_SCHEMA, CYCLE_REGISTRY_PATH, REPO_ROOT, WINDOW_INDEX_PATH, _sha256_file, verify_exact_state_components
from scenesmith.robot_lab.experience_records import ACTION_VARIANTS
from scenesmith.robot_lab.logical_source_cycle_buffers import verify_initial_buffer_registry
from scenesmith.robot_lab.snapshot_branch_corrections import EXACT_STATE_PATH, verify_snapshot_branch_manifest

MIXTURE_SCHEMA_VERSION = "scenesmith.dataset_mixture_manifest.v1"
INPUT_SCHEMA_VERSION = "scenesmith.training_input_manifest.v1"
TASK_ID = "T18.5"
SNAPSHOT_PATH = REPO_ROOT / "configurations/robot_lab/t18_4_snapshot_branch_corrections.json"
SELECTION_PATH = REPO_ROOT / "configurations/robot_lab/t18_1_episode_first_window_sample.json"
MIXTURE_PATH = REPO_ROOT / "configurations/robot_lab/dataset_mixture_manifest.json"
INPUT_PATH = REPO_ROOT / "configurations/robot_lab/training_input_manifest.json"
FALSE_FIELDS = ("buffer_materialized","buffer_mutated","model_loaded","model_inference_executed","optimizer_training","training_eligible","simulation_training_ready","physical_actuation","raw_bytes_rewritten","external_compute_started","brev_compute_started")

def build_manifests() -> tuple[dict[str, Any], dict[str, Any]]:
    selection=load_strict_json(SELECTION_PATH); cycle=load_strict_json(CYCLE_REGISTRY_PATH)
    exact=load_strict_json(EXACT_STATE_PATH); snapshots=load_strict_json(SNAPSHOT_PATH)
    verify_episode_first_window_sample(selection); verify_initial_buffer_registry(cycle)
    verify_exact_state_components(exact); verify_snapshot_branch_manifest(snapshots)
    cycle_ids=_cycle_ids(cycle)
    bindings=_bindings(exact, cycle_ids)
    selection_by_id={row["window_id"]:row for row in selection["selected_windows"]}
    if snapshots.get("correction_event_count") != 0 or snapshots.get("source_correction_evidence_present") is not False:
        raise ValueError("T18.5 source correction count is not truthfully zero")
    index=_window_index(cycle_ids)
    rows=[]
    for binding in bindings:
        source=index[binding["window_id"]]
        action_ids=_json_list(source.get("action_frame_ids_json"),"action frame IDs")
        variants=_json_list(source.get("action_variants_json"),"action variants")
        frame_ids=[frame["frame_id"] for frame in binding["frames"]]
        if action_ids != frame_ids or variants != list(ACTION_VARIANTS): raise ValueError("T18.5 source action binding drifted")
        selected=selection_by_id.get(binding["window_id"])
        if not isinstance(selected,dict) or selected.get("task_phase")!=binding["task_phase"] or selected.get("horizon")!=binding["horizon"]: raise ValueError("T18.5 selection binding drifted")
        rows.append({"window_id":binding["window_id"],"cycle_position":binding["cycle_position"],"source_class":selected["source_class"],"task_phase":binding["task_phase"],"control_mode":selected["control_mode"],"horizon":binding["horizon"],"frame_ids_sha256":_sha(frame_ids),"component_record_ids_sha256":_sha([frame["component_record_id"] for frame in binding["frames"]]),"action_frame_ids_sha256":_sha(action_ids)})
    ids=[row["window_id"] for row in rows]
    common={"task_id":TASK_ID,"logical_cycle_id":exact["logical_cycle_id"],"ordered_window_ids_sha256":_sha(ids),"window_count":len(rows),"source_selection_identity_sha256":selection["identity_sha256"],"source_cycle_identity_sha256":cycle["identity_sha256"],"source_exact_state_identity_sha256":exact["identity_sha256"],"source_snapshot_identity_sha256":snapshots["identity_sha256"],"source_window_index_file_sha256":_sha256_file(WINDOW_INDEX_PATH),"correction_window_count":0,"source_correction_evidence_present":False,"actor_input_schema":list(ACTOR_INPUT_SCHEMA),"actor_input_schema_sha256":_sha(list(ACTOR_INPUT_SCHEMA)),"action_variants":list(ACTION_VARIANTS),"action_variants_sha256":_sha(list(ACTION_VARIANTS)),**{field:False for field in FALSE_FIELDS}}
    mixture=sign_payload({"schema_version":MIXTURE_SCHEMA_VERSION,"mixture_scope":"immutable_reference_only_source_composition","dataset_mixture_frozen":True,"mixture_rows":rows,**common})
    inputs=[{"window_id":r["window_id"],"cycle_position":r["cycle_position"],"horizon":r["horizon"],"frame_ids_sha256":r["frame_ids_sha256"],"component_record_ids_sha256":r["component_record_ids_sha256"],"action_frame_ids_sha256":r["action_frame_ids_sha256"],"actor_input_schema":list(ACTOR_INPUT_SCHEMA),"action_variants":list(ACTION_VARIANTS)} for r in rows]
    training=sign_payload({"schema_version":INPUT_SCHEMA_VERSION,"training_input_scope":"reference_only_not_materialized_not_model_read","dataset_mixture_identity_sha256":mixture["identity_sha256"],"dataset_mixture_canonical_payload_sha256":_sha_bytes(canonical_json_bytes(mixture)),"dataset_mixture_frozen":True,"input_rows":inputs,"input_row_count":len(inputs),"input_row_ids_sha256":_sha(ids),"privileged_fields_available_to_actor":False,**common})
    return mixture, training

def verify_manifests(mixture:dict[str,Any], training:dict[str,Any])->None:
    _verify(mixture,MIXTURE_SCHEMA_VERSION); _verify(training,INPUT_SCHEMA_VERSION)
    expected_mixture,expected_training=build_manifests()
    if canonical_json_bytes(mixture)!=canonical_json_bytes(expected_mixture) or canonical_json_bytes(training)!=canonical_json_bytes(expected_training): raise ValueError("T18.5 manifest drifted from verified sources")

def _verify(payload:dict[str,Any],schema:str)->None:
    verify_signed_payload(payload,label="T18.5 manifest")
    if payload.get("schema_version")!=schema or payload.get("task_id")!=TASK_ID: raise ValueError("T18.5 manifest schema drifted")
    for field in FALSE_FIELDS:
        if payload.get(field) is not False: raise ValueError(f"T18.5 authority flag drifted: {field}")
    if payload.get("dataset_mixture_frozen") is not True: raise ValueError("T18.5 mixture is not frozen")
    if payload.get("source_correction_evidence_present") is not False or payload.get("correction_window_count")!=0: raise ValueError("T18.5 correction accounting drifted")
    if payload.get("actor_input_schema")!=list(ACTOR_INPUT_SCHEMA): raise ValueError("T18.5 actor input privilege drifted")
    if schema==INPUT_SCHEMA_VERSION and payload.get("privileged_fields_available_to_actor") is not False: raise ValueError("T18.5 training input exposes privileged fields")
    if payload.get("action_variants")!=list(ACTION_VARIANTS): raise ValueError("T18.5 action variants drifted")
    ids=[]; rows=payload.get("mixture_rows",payload.get("input_rows"))
    if not isinstance(rows,list) or not rows: raise ValueError("T18.5 rows are absent")
    for i,row in enumerate(rows,1):
        if not isinstance(row,dict) or row.get("cycle_position")!=i: raise ValueError("T18.5 row order drifted")
        ids.append(_sha_id(row.get("window_id"),"window ID")); _sha_id(row.get("frame_ids_sha256"),"frame digest"); _sha_id(row.get("component_record_ids_sha256"),"component digest"); _sha_id(row.get("action_frame_ids_sha256"),"action digest")
        if "actor_input_schema" in row and row["actor_input_schema"]!=list(ACTOR_INPUT_SCHEMA): raise ValueError("T18.5 input row privilege drifted")
        if "action_variants" in row and row["action_variants"]!=list(ACTION_VARIANTS): raise ValueError("T18.5 input row action variants drifted")
    if len(ids)!=len(set(ids)) or payload.get("ordered_window_ids_sha256")!=_sha(ids): raise ValueError("T18.5 window identity drifted")
    if payload.get("window_count")!=len(ids): raise ValueError("T18.5 window count drifted")

def _cycle_ids(cycle:dict[str,Any])->list[str]:
    rows=cycle.get("cycles")
    if not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict): raise ValueError("T18.5 logical cycle is invalid")
    ids=rows[0].get("window_ids")
    if not isinstance(ids,list) or not ids or rows[0].get("window_ids_sha256")!=_sha(ids): raise ValueError("T18.5 logical cycle IDs drifted")
    return [_sha_id(x,"cycle window ID") for x in ids]

def _bindings(exact:dict[str,Any],ids:list[str])->list[dict[str,Any]]:
    rows=exact.get("window_frame_bindings")
    if not isinstance(rows,list) or [r.get("window_id") for r in rows]!=ids: raise ValueError("T18.5 exact-state cycle binding drifted")
    return rows

def _window_index(ids:list[str])->dict[str,dict[str,Any]]:
    values={}
    for row in pq.read_table(WINDOW_INDEX_PATH).to_pylist():
        window_id=row.get("window_id")
        if window_id in values: raise ValueError("T18.5 source window duplicates")
        values[window_id]=row
    if not set(ids).issubset(values): raise ValueError("T18.5 source window is absent")
    return values

def _json_list(value:Any,label:str)->list[str]:
    if not isinstance(value,str): raise ValueError(f"T18.5 {label} are invalid")
    parsed=json.loads(value)
    if not isinstance(parsed,list) or any(not isinstance(x,str) for x in parsed): raise ValueError(f"T18.5 {label} are invalid")
    return parsed
def _sha(value:Any)->str:return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
def _sha_bytes(value:bytes)->str:return hashlib.sha256(value).hexdigest()
def _sha_id(value:Any,label:str)->str:
    if not isinstance(value,str) or len(value)!=64 or any(c not in "0123456789abcdef" for c in value): raise ValueError(f"T18.5 {label} must be SHA-256")
    return value

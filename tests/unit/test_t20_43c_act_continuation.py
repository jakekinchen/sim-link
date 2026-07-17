from __future__ import annotations

import copy
import hashlib

import pytest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_43c_act_continuation import (
    OUTPUT_PATHS,
    SOURCE_ATTEMPT_IDENTITY,
    SOURCE_CHECKPOINT_IDENTITY,
    SOURCE_FAILURE_IDENTITY,
    SOURCE_MODEL_FILE_SHA256,
    SOURCE_TRACE_FILE_SHA256,
    SOURCE_TRACE_IDENTITY,
    build_acceptance,
    build_central_authority,
    build_continuation_marker,
    build_equivalence_receipt,
    build_final_receipt,
    build_owner_grant,
    build_permit,
    build_renderer_smoke,
    build_retention_receipt,
    build_runtime_preflight,
    load_continuation_sources,
    verify_acceptance,
    verify_continuation_marker,
    verify_equivalence_receipt,
    verify_owner_grant,
    verify_permit,
)
from scenesmith.robot_lab.t20_43b_r1_act_contracts import EXPECTED_DEPENDENCIES
from scenesmith.robot_lab.t20_43c_act_continuation_runner import (
    _prove_tensor_equivalence,
)


ZERO = "0" * 64
SOURCE_COMMIT = "1" * 40
VALID_FROM = "2026-07-16T22:00:00-05:00"
VALID_UNTIL = "2026-07-17T02:00:00-05:00"


@pytest.fixture(scope="module")
def sources():
    return load_continuation_sources()


@pytest.fixture()
def authority(sources):
    smoke = build_renderer_smoke(
        evidence={
            "renderer_v2_file_sha256": "2" * 64,
            "legacy_renderer_file_sha256": "3" * 64,
            "video_file_sha256": "4" * 64,
            "video_size_bytes": 100,
            "manifest_identity_sha256": "5" * 64,
            "manifest_file_sha256": "6" * 64,
            "runner_interpreter": "external/lerobot/.venv/bin/python",
        }
    )
    owner = build_owner_grant(
        required_source_commit=SOURCE_COMMIT,
        valid_from=VALID_FROM,
        valid_until=VALID_UNTIL,
    )
    request, decision = build_central_authority(
        sources=sources, smoke=smoke, owner=owner
    )
    snapshot = {
        "source_commit": SOURCE_COMMIT,
        "branch": "codex/pi05-autolearn-loop",
        "origin_contains_source_commit": True,
        "scoped_dirty_paths": [],
        "dependencies": EXPECTED_DEPENDENCIES,
        "mps_available": True,
        "free_disk_bytes": 20 * 1024**3,
        "network_enabled": False,
        "source_attempt_identity_sha256": SOURCE_ATTEMPT_IDENTITY,
        "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
        "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
        "source_model_file_sha256": SOURCE_MODEL_FILE_SHA256,
        "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
        "source_trace_file_sha256": SOURCE_TRACE_FILE_SHA256,
        "source_partial_tree_identity_sha256": hashlib.sha256(
            canonical_json_bytes(sources["failure"]["partial_run_tree"])
        ).hexdigest(),
        "output_path_state": {
            path.as_posix(): {"exists": False, "is_symlink": False}
            for path in OUTPUT_PATHS
        },
        "authority_artifacts_materialized": False,
        "continuation_marker_exists": False,
    }
    runtime = build_runtime_preflight(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        snapshot=snapshot,
    )
    permit = build_permit(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )
    return sources, smoke, owner, request, decision, runtime, permit


def test_source_boundary_is_the_exact_terminal_zero_update_failure(sources):
    assert sources["failure"]["identity_sha256"] == SOURCE_FAILURE_IDENTITY
    assert sources["failure"]["optimizer_update_count"] == 0
    assert sources["attempt"]["identity_sha256"] == SOURCE_ATTEMPT_IDENTITY
    assert sources["trace"]["identity_sha256"] == SOURCE_TRACE_IDENTITY
    assert (
        hashlib.sha256(canonical_json_bytes(sources["checkpoint_tree"])).hexdigest()
        == SOURCE_CHECKPOINT_IDENTITY
    )


def test_central_authority_grants_only_simulation_training(authority):
    sources, smoke, owner, request, decision, runtime, permit = authority
    verify_owner_grant(owner)
    assert decision["authority_granted"] == ["simulation_training_ready"]
    verify_permit(
        permit,
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )
    assert permit["equivalence_required_before_update_1"] is True
    assert permit["hardware_authorized"] is False
    assert permit["brev_compute_authorized"] is False


def test_runtime_rejects_existing_output(authority):
    sources, smoke, owner, request, decision, runtime, _ = authority
    tampered = copy.deepcopy(runtime)
    key = next(iter(tampered["output_path_state"]))
    tampered["output_path_state"][key]["exists"] = True
    tampered = sign_payload(tampered)
    with pytest.raises(ValueError, match="output path"):
        build_permit(
            sources=sources,
            smoke=smoke,
            owner=owner,
            request=request,
            decision=decision,
            runtime=tampered,
        )


def test_marker_acceptance_and_equivalence_are_closed_chain(authority):
    *_, permit = authority
    acceptance = build_acceptance(
        authority_commit="7" * 40,
        reviewer_decision_id="307",
        reviewer_path="docs/reviewer-messages/307.md",
        reviewer_file_sha256="8" * 64,
        permit=permit,
    )
    verify_acceptance(acceptance, permit=permit)
    marker = build_continuation_marker(
        permit=permit,
        source_commit="9" * 40,
        started_at="2026-07-16T22:10:00-05:00",
    )
    verify_continuation_marker(marker, permit=permit)
    equivalence = build_equivalence_receipt(
        marker=marker,
        tensor_key_count=2,
        tensor_element_count=6,
        tensor_dtype_counts={"torch.float32": 2},
        compared_tensor_sha256="a" * 64,
    )
    verify_equivalence_receipt(equivalence, marker=marker)
    tampered = dict(equivalence)
    tampered["optimizer_state_entry_count"] = 1
    tampered = sign_payload(tampered)
    with pytest.raises(ValueError, match="equivalence receipt drifted"):
        verify_equivalence_receipt(tampered, marker=marker)


def test_tensor_equivalence_is_bit_exact_and_fails_on_value_change():
    torch = pytest.importorskip("torch")
    fresh = {
        "a": torch.tensor([1.0, 2.0], dtype=torch.float32),
        "b": torch.tensor([3], dtype=torch.int64),
        "scalar": torch.tensor(4.0, dtype=torch.float32),
    }
    saved = {key: value.clone() for key, value in fresh.items()}
    evidence = _prove_tensor_equivalence(
        fresh_state=fresh, saved_state=saved, torch=torch
    )
    assert evidence["tensor_key_count"] == 3
    assert evidence["tensor_element_count"] == 4
    changed = {key: value.clone() for key, value in saved.items()}
    changed["a"][0] += 1
    with pytest.raises(ValueError, match="tensor mismatch"):
        _prove_tensor_equivalence(fresh_state=fresh, saved_state=changed, torch=torch)


def test_outer_receipt_binds_original_failure_and_continuation(authority):
    *_, permit = authority
    marker = build_continuation_marker(
        permit=permit,
        source_commit="9" * 40,
        started_at="2026-07-16T22:10:00-05:00",
    )
    equivalence = build_equivalence_receipt(
        marker=marker,
        tensor_key_count=1,
        tensor_element_count=1,
        tensor_dtype_counts={"torch.float32": 1},
        compared_tensor_sha256="a" * 64,
    )
    result = {
        "identity_sha256": "b" * 64,
        "status": "verified_terminal_negative",
        "optimizer_update_count": 10_000,
        "gate_c_passed": False,
        "first_gate_c_pass": None,
    }
    run = {"identity_sha256": "c" * 64}
    retention = build_retention_receipt(
        result=result,
        run=run,
        local_output_trees={"checkpoints": [], "rollouts": [], "mirrors": []},
    )
    final = build_final_receipt(
        marker=marker,
        equivalence=equivalence,
        result=result,
        retention=retention,
    )
    assert final["source_failure_identity_sha256"] == SOURCE_FAILURE_IDENTITY
    assert final["zero_update_continuation_proven"] is True
    assert final["retry_authorized"] is False

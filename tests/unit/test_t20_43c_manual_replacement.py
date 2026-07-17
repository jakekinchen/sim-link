from __future__ import annotations

import copy
import hashlib

from datetime import timedelta

import pytest

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    verify_signed_payload,
)
from scenesmith.robot_lab import t20_43c_act_continuation as base
from scenesmith.robot_lab import t20_43c_act_continuation_runner as base_runner
from scenesmith.robot_lab.t20_43c_manual_replacement import (
    AUTHORIZATION_ID,
    EQUIVALENCE_PATH,
    FAILURE_PATH,
    FINAL_RECEIPT_PATH,
    MARKER_PATH,
    MINIMUM_COMPLETION_BUDGET_SECONDS,
    PRIOR_FAILURE_IDENTITY,
    RESULT_PATH,
    RETENTION_PATH,
    RUN_ROOT,
    SCORECARD_PATH,
    build_acceptance,
    build_equivalence_receipt,
    build_owner_grant,
    build_replacement_marker,
    build_terminal_failure,
    verify_acceptance,
    verify_equivalence_receipt,
    verify_owner_grant,
    verify_replacement_marker,
    verify_terminal_failure,
    _patched_runner_contract,
    _require_completion_budget,
)


COMMIT = "a" * 40
SHA = "b" * 64
START = "2026-07-16T22:45:00-05:00"
STOP = "2026-07-17T06:30:00-05:00"


def _permit() -> dict:
    from scenesmith.robot_lab.artifact_contract import sign_payload

    return sign_payload({"schema_version": "fixture", "task_id": "T20.43c-R2"})


def test_owner_grant_is_one_manual_replacement_only():
    owner = build_owner_grant(
        required_source_commit=COMMIT, valid_from=START, valid_until=STOP
    )
    verify_owner_grant(owner)
    assert owner["authorization_id"] == AUTHORIZATION_ID
    assert owner["fresh_manual_replacement_authorized"] is True
    assert owner["authorized_attempt_count"] == 1
    assert owner["replacement_ordinal"] == 2
    assert owner["automatic_retry_authorized"] is False
    assert owner["retry_after_this_attempt_authorized"] is False
    assert owner["hardware_authorized"] is False
    assert owner["network_authorized"] is False
    assert owner["external_compute_authorized"] is False
    assert owner["brev_compute_authorized"] is False


def test_acceptance_and_marker_bind_new_permit_without_reusing_old_paths():
    permit = _permit()
    acceptance = build_acceptance(
        authority_commit=COMMIT,
        reviewer_decision_id="312",
        reviewer_path="docs/reviewer-messages/312-fixture.md",
        reviewer_file_sha256=SHA,
        permit=permit,
    )
    verify_acceptance(acceptance, permit=permit)
    marker = build_replacement_marker(
        permit=permit, source_commit=COMMIT, started_at=START
    )
    verify_replacement_marker(marker, permit=permit)
    assert marker["fresh_manual_replacement"] is True
    assert marker["replacement_ordinal"] == 2
    assert MARKER_PATH != base.MARKER_PATH
    assert FAILURE_PATH != base.FAILURE_PATH
    assert RUN_ROOT != base.RUN_ROOT


def test_equivalence_receipt_is_exact_and_binds_prior_interruption():
    permit = _permit()
    marker = build_replacement_marker(
        permit=permit, source_commit=COMMIT, started_at=START
    )
    receipt = build_equivalence_receipt(
        marker=marker,
        tensor_key_count=2,
        tensor_element_count=3,
        tensor_dtype_counts={"torch.float32": 2},
        compared_tensor_sha256=SHA,
    )
    verify_equivalence_receipt(receipt, marker=marker)
    assert receipt["prior_terminal_failure_identity_sha256"] == PRIOR_FAILURE_IDENTITY
    assert receipt["optimizer_state_entry_count"] == 0
    assert receipt["training_batches_consumed"] == 0
    assert receipt["tensor_values_bit_exact"] is True
    tampered = copy.deepcopy(receipt)
    tampered["training_batches_consumed"] = 1
    with pytest.raises(ValueError):
        verify_equivalence_receipt(tampered, marker=marker)


def test_completion_budget_fails_before_marker():
    owner = build_owner_grant(
        required_source_commit=COMMIT, valid_from=START, valid_until=STOP
    )
    stop = __import__("datetime").datetime.fromisoformat(STOP)
    too_late = stop - timedelta(seconds=MINIMUM_COMPLETION_BUDGET_SECONDS - 1)
    with pytest.raises(ValueError, match="completion budget"):
        _require_completion_budget(owner=owner, started_at=too_late.isoformat())
    enough = stop - timedelta(seconds=MINIMUM_COMPLETION_BUDGET_SECONDS)
    _require_completion_budget(owner=owner, started_at=enough.isoformat())


def test_terminal_failure_binds_tree_and_forbids_retry():
    permit = _permit()
    marker = build_replacement_marker(
        permit=permit, source_commit=COMMIT, started_at=START
    )
    tree = [{"path": "progress.json", "sha256": SHA, "size_bytes": 10}]
    failure = build_terminal_failure(
        marker=marker,
        progress={
            "stage": "fixture",
            "optimizer_update_count": 0,
            "training_batches_consumed": 0,
        },
        partial_run_tree=tree,
        error_type="FixtureError",
        error_message="fixture",
    )
    verify_terminal_failure(failure, marker=marker, partial_run_tree=tree)
    assert failure["retry_after_this_attempt_authorized"] is False
    assert (
        failure["partial_run_tree_identity_sha256"]
        == hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
    )
    with pytest.raises(ValueError):
        verify_terminal_failure(failure, marker=marker, partial_run_tree=[])


def test_runner_patch_is_scoped_and_uses_disjoint_outputs():
    original_marker = base_runner.MARKER_PATH
    original_result = base_runner.RESULT_PATH
    original_verify = base_runner.verify_materialized_authority
    with _patched_runner_contract():
        assert base_runner.MARKER_PATH == MARKER_PATH
        assert base_runner.EQUIVALENCE_PATH == EQUIVALENCE_PATH
        assert base_runner.RESULT_PATH == RESULT_PATH
        assert base_runner.SCORECARD_PATH == SCORECARD_PATH
        assert base_runner.RETENTION_PATH == RETENTION_PATH
        assert base_runner.FINAL_RECEIPT_PATH == FINAL_RECEIPT_PATH
        assert base_runner.verify_materialized_authority is not original_verify
    assert base_runner.MARKER_PATH == original_marker
    assert base_runner.RESULT_PATH == original_result
    assert base_runner.verify_materialized_authority is original_verify


def test_owner_payload_signature_rejects_mutation():
    owner = build_owner_grant(
        required_source_commit=COMMIT, valid_from=START, valid_until=STOP
    )
    verify_signed_payload(owner, label="fixture owner")
    owner["authorized_attempt_count"] = 2
    with pytest.raises(ValueError):
        verify_signed_payload(owner, label="fixture owner")

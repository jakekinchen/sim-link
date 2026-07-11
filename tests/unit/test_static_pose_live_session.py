from __future__ import annotations

import copy
import os
import unittest

from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch

from scenesmith.robot_lab.artifact_contract import sign_payload
import scenesmith.robot_lab.static_pose_live_session as session_module
from scenesmith.robot_lab.static_pose_live_session import (
    STATIC_POSE_LIVE_SESSION_RECEIPT_SCHEMA_VERSION,
    StaticPoseLiveSessionRejected,
    build_static_pose_live_session_receipt,
    run_pinned_static_pose_live_session,
    verify_static_pose_live_session_receipt,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
THREAD_ID = "019f5006-2455-7941-bc76-b992dd96f8a8"
PREFLIGHT_AT = "2026-07-11T15:09:59-05:00"
STARTED_AT = "2026-07-11T15:10:00-05:00"
COMPLETED_AT = "2026-07-11T15:10:10-05:00"
SESSION_ID = "brief-054-fixture-session"
AUTHORITY_NOT_GRANTED = [
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]


class _WallTime:
    def __init__(self, *values: str | BaseException):
        self.values = iter(values)

    def __call__(self) -> str:
        value = next(self.values)
        if isinstance(value, BaseException):
            raise value
        return value


def _contract() -> dict:
    return sign_payload(
        {
            "schema_version": "scenesmith.static_pose_live_candidate_contract.v1",
            "session_id": SESSION_ID,
            "execution_class": "live_candidate",
            "candidate_only": True,
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED),
            "physical_follower_commanded": False,
        }
    )


def _profile() -> dict:
    return sign_payload(
        {
            "schema_version": "scenesmith.hardware_execution_profile_evidence.v1",
            "thread_id": THREAD_ID,
            "approval_policy": "on-request",
            "sandbox_mode": "danger-full-access",
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED),
            "hardware_accessed": False,
            "physical_follower_commanded": False,
        }
    )


def _result(contract: dict, profile: dict) -> dict:
    return sign_payload(
        {
            "schema_version": "scenesmith.static_pose_live_candidate_result.v2",
            "result_name": "pi05_static_pose_live_candidate_runtime",
            "execution_class": "live_candidate",
            "evidence_mode": "private_source_bound_live_candidate_runtime",
            "candidate_only": True,
            "verified_at": STARTED_AT,
            "candidate_contract_identity_sha256": contract["identity_sha256"],
            "hardware_execution_profile_identity_sha256": profile[
                "identity_sha256"
            ],
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED),
            "hardware_opened": True,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
        }
    )


def _success_evidence(contract: dict, profile: dict, result: dict) -> dict:
    return sign_payload(
        {
            "schema_version": (
                "scenesmith.static_pose_live_candidate_private_success.v1"
            ),
            "status": "candidate_observed",
            "session_id": SESSION_ID,
            "candidate_only": True,
            "candidate_contract_identity_sha256": contract["identity_sha256"],
            "hardware_execution_profile_identity_sha256": profile[
                "identity_sha256"
            ],
            "candidate_result_identity_sha256": result["identity_sha256"],
            "completed_at": COMPLETED_AT,
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED),
            "physical_follower_commanded": False,
        }
    )


def _failure_evidence(contract: dict, profile: dict) -> dict:
    return sign_payload(
        {
            "schema_version": (
                "scenesmith.static_pose_live_candidate_private_failure.v1"
            ),
            "status": "rejected",
            "session_id": SESSION_ID,
            "candidate_only": True,
            "candidate_contract_identity_sha256": contract["identity_sha256"],
            "hardware_execution_profile_identity_sha256": profile[
                "identity_sha256"
            ],
            "failed_at": COMPLETED_AT,
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED),
            "physical_follower_commanded": False,
        }
    )


def _reference(evidence: dict) -> dict:
    return {
        "relative_path": (
            f"{SESSION_ID}/{evidence['identity_sha256']}/private_success.json"
        ),
        "schema_version": evidence["schema_version"],
        "identity_sha256": evidence["identity_sha256"],
        "file_sha256": "f" * 64,
        "size_bytes": 123,
    }


def _base_arguments() -> dict:
    return {
        "project_state": {},
        "static_pose_contract": {},
        "calibration_path": Path("fixture-calibration.json"),
        "calibration_profile_path": Path("fixture-profile.json"),
        "manifest_path": Path("fixture-manifest.json"),
        "private_root": Path("fixture-private-root"),
        "pre_open_holder_snapshot": {},
        "post_close_holder_snapshot_factory": Mock(name="post_holder"),
        "monotonic_ns": Mock(name="monotonic_ns"),
    }


class StaticPoseLiveSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = _contract()
        self.profile = _profile()
        self.result = _result(self.contract, self.profile)
        self.success = _success_evidence(
            self.contract,
            self.profile,
            self.result,
        )
        self.failure = _failure_evidence(self.contract, self.profile)
        self.reference = _reference(self.success)

    def _patch_preflight(self, stack: ExitStack):
        verify_profile = stack.enter_context(
            patch.object(session_module, "verify_hardware_execution_profile_evidence")
        )
        verify_contract = stack.enter_context(
            patch.object(session_module, "verify_static_pose_live_candidate_contract")
        )
        verify_destination = stack.enter_context(
            patch.object(
                session_module,
                "verify_private_static_pose_candidate_evidence_destination",
            )
        )
        transport = object()
        camera = object()
        make_transport = stack.enter_context(
            patch.object(
                session_module,
                "make_pinned_static_pose_transport_factory",
                return_value=transport,
            )
        )
        make_camera = stack.enter_context(
            patch.object(
                session_module,
                "make_pinned_static_pose_camera_factory",
                return_value=camera,
            )
        )
        return (
            verify_profile,
            verify_contract,
            verify_destination,
            make_transport,
            make_camera,
            transport,
            camera,
        )

    def test_success_returns_only_after_one_verified_private_write(self):
        with ExitStack() as stack, patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": THREAD_ID},
        ):
            (
                verify_profile,
                verify_contract,
                verify_destination,
                make_transport,
                make_camera,
                transport,
                camera,
            ) = self._patch_preflight(stack)
            runner = stack.enter_context(
                patch.object(
                    session_module,
                    "run_static_pose_live_candidate",
                    return_value=self.result,
                )
            )
            build_success = stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_success_evidence",
                    return_value=self.success,
                )
            )
            verify_success = stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_success_evidence",
                )
            )
            writer = stack.enter_context(
                patch.object(
                    session_module,
                    "write_private_static_pose_candidate_evidence",
                    return_value=self.reference,
                )
            )
            verify_reference = stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_evidence_reference",
                )
            )
            receipt_verifier = stack.enter_context(
                patch.object(session_module, "verify_static_pose_live_session_receipt")
            )
            output = run_pinned_static_pose_live_session(
                self.contract,
                hardware_execution_profile=self.profile,
                wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, COMPLETED_AT),
                **_base_arguments(),
            )
        verify_profile.assert_called_once()
        verify_contract.assert_called_once()
        verify_destination.assert_called_once_with(
            private_root=Path("fixture-private-root"),
            session_id=SESSION_ID,
        )
        make_transport.assert_called_once()
        make_camera.assert_called_once()
        self.assertIs(runner.call_args.kwargs["transport_factory"], transport)
        self.assertIs(runner.call_args.kwargs["camera_factory"], camera)
        build_success.assert_called_once()
        verify_success.assert_called_once()
        writer.assert_called_once()
        verify_reference.assert_called_once()
        receipt_verifier.assert_called_once()
        self.assertEqual(output["candidate_result"], self.result)
        self.assertEqual(output["private_evidence"], self.success)
        self.assertEqual(output["private_reference"], self.reference)
        self.assertEqual(output["session_receipt"]["proof_labels"], [])
        self.assertTrue(output["session_receipt"]["candidate_only"])

    def test_primary_failure_writes_once_then_raises_typed_rejection(self):
        primary = BaseExceptionGroup(
            "runtime and cleanup",
            [RuntimeError("camera failed"), OSError("holder failed")],
        )
        failure_reference = {
            **self.reference,
            "relative_path": self.reference["relative_path"].replace(
                "private_success.json",
                "private_failure.json",
            ),
            "schema_version": self.failure["schema_version"],
            "identity_sha256": self.failure["identity_sha256"],
        }
        with ExitStack() as stack, patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": THREAD_ID},
        ):
            self._patch_preflight(stack)
            stack.enter_context(
                patch.object(
                    session_module,
                    "run_static_pose_live_candidate",
                    side_effect=primary,
                )
            )
            build_failure = stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_failure_evidence",
                    return_value=self.failure,
                )
            )
            verify_failure = stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_failure_evidence",
                )
            )
            writer = stack.enter_context(
                patch.object(
                    session_module,
                    "write_private_static_pose_candidate_evidence",
                    return_value=failure_reference,
                )
            )
            verify_reference = stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_evidence_reference",
                )
            )
            with self.assertRaises(StaticPoseLiveSessionRejected) as caught:
                run_pinned_static_pose_live_session(
                    self.contract,
                    hardware_execution_profile=self.profile,
                    wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, COMPLETED_AT),
                    **_base_arguments(),
                )
        build_failure.assert_called_once()
        self.assertIs(build_failure.call_args.kwargs["error"], primary)
        verify_failure.assert_called_once()
        writer.assert_called_once()
        verify_reference.assert_called_once()
        self.assertIs(caught.exception.__cause__, primary)
        self.assertEqual(caught.exception.private_evidence, self.failure)
        self.assertEqual(caught.exception.private_reference, failure_reference)
        self.assertFalse(hasattr(caught.exception, "candidate_result"))

    def test_preflight_failure_never_runs_or_writes_a_session(self):
        for failed_stage in (
            "profile",
            "contract",
            "destination",
            "transport",
            "camera",
        ):
            with self.subTest(stage=failed_stage), ExitStack() as stack, patch.dict(
                os.environ,
                {"CODEX_THREAD_ID": THREAD_ID},
            ):
                (
                    verify_profile,
                    verify_contract,
                    verify_destination,
                    make_transport,
                    make_camera,
                    _,
                    _,
                ) = self._patch_preflight(stack)
                stages = {
                    "profile": verify_profile,
                    "contract": verify_contract,
                    "destination": verify_destination,
                    "transport": make_transport,
                    "camera": make_camera,
                }
                stages[failed_stage].side_effect = ValueError(
                    f"{failed_stage} preflight failed"
                )
                runner = stack.enter_context(
                    patch.object(session_module, "run_static_pose_live_candidate")
                )
                writer = stack.enter_context(
                    patch.object(
                        session_module,
                        "write_private_static_pose_candidate_evidence",
                    )
                )
                with self.assertRaisesRegex(ValueError, "preflight failed"):
                    run_pinned_static_pose_live_session(
                        self.contract,
                        hardware_execution_profile=self.profile,
                        wall_time=_WallTime(PREFLIGHT_AT),
                        **_base_arguments(),
                    )
                runner.assert_not_called()
                writer.assert_not_called()

    def test_clock_regression_before_start_writes_nothing(self):
        with ExitStack() as stack, patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": THREAD_ID},
        ):
            self._patch_preflight(stack)
            runner = stack.enter_context(
                patch.object(session_module, "run_static_pose_live_candidate")
            )
            writer = stack.enter_context(
                patch.object(
                    session_module,
                    "write_private_static_pose_candidate_evidence",
                )
            )
            with self.assertRaisesRegex(ValueError, "clock regressed"):
                run_pinned_static_pose_live_session(
                    self.contract,
                    hardware_execution_profile=self.profile,
                    wall_time=_WallTime(STARTED_AT, PREFLIGHT_AT),
                    **_base_arguments(),
                )
        runner.assert_not_called()
        writer.assert_not_called()

    def test_clock_regression_after_result_persists_rejection_not_success(self):
        with ExitStack() as stack, patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": THREAD_ID},
        ):
            self._patch_preflight(stack)
            stack.enter_context(
                patch.object(
                    session_module,
                    "run_static_pose_live_candidate",
                    return_value=self.result,
                )
            )
            build_failure = stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_failure_evidence",
                    return_value=self.failure,
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_failure_evidence",
                )
            )
            writer = stack.enter_context(
                patch.object(
                    session_module,
                    "write_private_static_pose_candidate_evidence",
                    return_value=self.reference,
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_evidence_reference",
                )
            )
            build_success = stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_success_evidence",
                )
            )
            with self.assertRaises(StaticPoseLiveSessionRejected) as caught:
                run_pinned_static_pose_live_session(
                    self.contract,
                    hardware_execution_profile=self.profile,
                    wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, PREFLIGHT_AT),
                    **_base_arguments(),
                )
        self.assertEqual(
            str(build_failure.call_args.kwargs["error"]),
            "Static-pose live session completion clock regressed",
        )
        self.assertEqual(build_failure.call_args.kwargs["failed_at"], STARTED_AT)
        writer.assert_called_once()
        build_success.assert_not_called()
        self.assertEqual(caught.exception.private_evidence, self.failure)

    def test_primary_failure_and_timing_failure_are_both_preserved(self):
        primary = RuntimeError("candidate failed")
        timing = OSError("failure clock unavailable")
        with ExitStack() as stack, patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": THREAD_ID},
        ):
            self._patch_preflight(stack)
            stack.enter_context(
                patch.object(
                    session_module,
                    "run_static_pose_live_candidate",
                    side_effect=primary,
                )
            )
            build_failure = stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_failure_evidence",
                    return_value=self.failure,
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_failure_evidence",
                )
            )
            writer = stack.enter_context(
                patch.object(
                    session_module,
                    "write_private_static_pose_candidate_evidence",
                    return_value=self.reference,
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_evidence_reference",
                )
            )
            with self.assertRaises(StaticPoseLiveSessionRejected) as caught:
                run_pinned_static_pose_live_session(
                    self.contract,
                    hardware_execution_profile=self.profile,
                    wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, timing),
                    **_base_arguments(),
                )
        combined = build_failure.call_args.kwargs["error"]
        self.assertIsInstance(combined, BaseExceptionGroup)
        self.assertEqual(combined.exceptions, (primary, timing))
        self.assertEqual(build_failure.call_args.kwargs["failed_at"], STARTED_AT)
        writer.assert_called_once()
        self.assertIs(caught.exception.__cause__, combined)

    def test_completion_timing_failure_persists_rejection_and_withholds_result(self):
        timing = OSError("completion clock unavailable")
        with ExitStack() as stack, patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": THREAD_ID},
        ):
            self._patch_preflight(stack)
            stack.enter_context(
                patch.object(
                    session_module,
                    "run_static_pose_live_candidate",
                    return_value=self.result,
                )
            )
            build_failure = stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_failure_evidence",
                    return_value=self.failure,
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_failure_evidence",
                )
            )
            writer = stack.enter_context(
                patch.object(
                    session_module,
                    "write_private_static_pose_candidate_evidence",
                    return_value=self.reference,
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_evidence_reference",
                )
            )
            build_success = stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_success_evidence",
                )
            )
            with self.assertRaises(StaticPoseLiveSessionRejected) as caught:
                run_pinned_static_pose_live_session(
                    self.contract,
                    hardware_execution_profile=self.profile,
                    wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, timing),
                    **_base_arguments(),
                )
        self.assertIs(build_failure.call_args.kwargs["error"], timing)
        self.assertEqual(build_failure.call_args.kwargs["failed_at"], STARTED_AT)
        writer.assert_called_once()
        build_success.assert_not_called()
        self.assertIs(caught.exception.__cause__, timing)

    def test_primary_and_failure_evidence_errors_are_both_preserved_without_write(self):
        primary = RuntimeError("candidate failed")
        evidence_error = ValueError("failure evidence could not be built")
        with ExitStack() as stack, patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": THREAD_ID},
        ):
            self._patch_preflight(stack)
            stack.enter_context(
                patch.object(
                    session_module,
                    "run_static_pose_live_candidate",
                    side_effect=primary,
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "build_private_static_pose_candidate_failure_evidence",
                    side_effect=evidence_error,
                )
            )
            writer = stack.enter_context(
                patch.object(
                    session_module,
                    "write_private_static_pose_candidate_evidence",
                )
            )
            with self.assertRaises(BaseExceptionGroup) as caught:
                run_pinned_static_pose_live_session(
                    self.contract,
                    hardware_execution_profile=self.profile,
                    wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, COMPLETED_AT),
                    **_base_arguments(),
                )
        self.assertEqual(caught.exception.exceptions, (primary, evidence_error))
        writer.assert_not_called()

    def test_failure_verify_write_or_reference_error_preserves_primary_without_retry(self):
        for failed_stage in ("verify", "write", "reference"):
            primary = RuntimeError("candidate failed")
            persistence = ValueError(f"failure {failed_stage} failed")
            with self.subTest(stage=failed_stage), ExitStack() as stack, patch.dict(
                os.environ,
                {"CODEX_THREAD_ID": THREAD_ID},
            ):
                self._patch_preflight(stack)
                stack.enter_context(
                    patch.object(
                        session_module,
                        "run_static_pose_live_candidate",
                        side_effect=primary,
                    )
                )
                verify_failure = stack.enter_context(
                    patch.object(
                        session_module,
                        "build_private_static_pose_candidate_failure_evidence",
                        return_value=self.failure,
                    )
                )
                stack.enter_context(
                    patch.object(
                        session_module,
                        "verify_private_static_pose_candidate_failure_evidence",
                    )
                )
                writer = stack.enter_context(
                    patch.object(
                        session_module,
                        "write_private_static_pose_candidate_evidence",
                        return_value=self.reference,
                    )
                )
                reference = stack.enter_context(
                    patch.object(
                        session_module,
                        "verify_private_static_pose_candidate_evidence_reference",
                    )
                )
                {"verify": verify_failure, "write": writer, "reference": reference}[
                    failed_stage
                ].side_effect = persistence
                with self.assertRaises(BaseExceptionGroup) as caught:
                    run_pinned_static_pose_live_session(
                        self.contract,
                        hardware_execution_profile=self.profile,
                        wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, COMPLETED_AT),
                        **_base_arguments(),
                    )
            self.assertEqual(caught.exception.exceptions, (primary, persistence))
            self.assertLessEqual(writer.call_count, 1)

    def test_success_persistence_or_reference_failure_withholds_result_without_retry(self):
        for failed_stage in (
            "build",
            "verify",
            "write",
            "reference",
            "receipt_build",
            "receipt_verify",
        ):
            with self.subTest(stage=failed_stage), ExitStack() as stack, patch.dict(
                os.environ,
                {"CODEX_THREAD_ID": THREAD_ID},
            ):
                self._patch_preflight(stack)
                stack.enter_context(
                    patch.object(
                        session_module,
                        "run_static_pose_live_candidate",
                        return_value=self.result,
                    )
                )
                build = stack.enter_context(
                    patch.object(
                        session_module,
                        "build_private_static_pose_candidate_success_evidence",
                        return_value=self.success,
                    )
                )
                verify_success = stack.enter_context(
                    patch.object(
                        session_module,
                        "verify_private_static_pose_candidate_success_evidence",
                    )
                )
                writer = stack.enter_context(
                    patch.object(
                        session_module,
                        "write_private_static_pose_candidate_evidence",
                        return_value=self.reference,
                    )
                )
                reference = stack.enter_context(
                    patch.object(
                        session_module,
                        "verify_private_static_pose_candidate_evidence_reference",
                    )
                )
                receipt_builder = stack.enter_context(
                    patch.object(
                        session_module,
                        "build_static_pose_live_session_receipt",
                        wraps=build_static_pose_live_session_receipt,
                    )
                )
                receipt_verifier = stack.enter_context(
                    patch.object(
                        session_module,
                        "verify_static_pose_live_session_receipt",
                    )
                )
                failure = ValueError(f"{failed_stage} failed")
                {
                    "build": build,
                    "verify": verify_success,
                    "write": writer,
                    "reference": reference,
                    "receipt_build": receipt_builder,
                    "receipt_verify": receipt_verifier,
                }[
                    failed_stage
                ].side_effect = failure
                with self.assertRaises(BaseExceptionGroup) as caught:
                    run_pinned_static_pose_live_session(
                        self.contract,
                        hardware_execution_profile=self.profile,
                        wall_time=_WallTime(PREFLIGHT_AT, STARTED_AT, COMPLETED_AT),
                        **_base_arguments(),
                    )
                self.assertIs(caught.exception.exceptions[-1], failure)
                self.assertIsInstance(caught.exception.exceptions[0], RuntimeError)
                self.assertLessEqual(writer.call_count, 1)

    def test_receipt_rejects_profile_result_evidence_or_authority_substitution(self):
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(session_module, "verify_hardware_execution_profile_evidence")
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_success_evidence",
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_static_pose_live_candidate_result_from_embedded_authority",
                )
            )
            stack.enter_context(
                patch.object(
                    session_module,
                    "verify_private_static_pose_candidate_evidence_reference",
                )
            )
            receipt = build_static_pose_live_session_receipt(
                candidate_contract=self.contract,
                hardware_execution_profile=self.profile,
                candidate_result=self.result,
                private_evidence=self.success,
                private_reference=self.reference,
                private_root=Path("fixture-private-root"),
                preflight_at=PREFLIGHT_AT,
                started_at=STARTED_AT,
                completed_at=COMPLETED_AT,
            )
            verify_static_pose_live_session_receipt(
                receipt,
                candidate_contract=self.contract,
                hardware_execution_profile=self.profile,
                candidate_result=self.result,
                private_evidence=self.success,
                private_reference=self.reference,
                private_root=Path("fixture-private-root"),
                static_pose_contract={},
                calibration_path=Path("fixture-calibration.json"),
                calibration_profile_path=Path("fixture-profile.json"),
                manifest_path=Path("fixture-manifest.json"),
            )
            mutations = (
                lambda value: value.__setitem__(
                    "hardware_execution_profile_identity_sha256", "0" * 64
                ),
                lambda value: value.__setitem__(
                    "candidate_result_identity_sha256", "0" * 64
                ),
                lambda value: value.__setitem__(
                    "private_evidence_identity_sha256", "0" * 64
                ),
                lambda value: value.__setitem__(
                    "private_reference_sha256", "0" * 64
                ),
                lambda value: value.__setitem__(
                    "proof_labels", ["static_pose_bracketed_observation"]
                ),
                lambda value: value.__setitem__("candidate_only", False),
                lambda value: value.__setitem__(
                    "preflight_at", "2026-07-11T15:10:01-05:00"
                ),
                lambda value: value.__setitem__(
                    "completed_at", "2026-07-11T15:09:59-05:00"
                ),
            )
            for mutate in mutations:
                changed = copy.deepcopy(receipt)
                mutate(changed)
                with self.assertRaises(ValueError):
                    verify_static_pose_live_session_receipt(
                        sign_payload(changed),
                        candidate_contract=self.contract,
                        hardware_execution_profile=self.profile,
                        candidate_result=self.result,
                        private_evidence=self.success,
                        private_reference=self.reference,
                        private_root=Path("fixture-private-root"),
                        static_pose_contract={},
                        calibration_path=Path("fixture-calibration.json"),
                        calibration_profile_path=Path("fixture-profile.json"),
                        manifest_path=Path("fixture-manifest.json"),
                    )
        self.assertEqual(
            receipt["schema_version"],
            STATIC_POSE_LIVE_SESSION_RECEIPT_SCHEMA_VERSION,
        )
        self.assertEqual(
            receipt["local_capabilities"],
            ["private_static_pose_live_session_receipt_valid"],
        )


if __name__ == "__main__":
    unittest.main()

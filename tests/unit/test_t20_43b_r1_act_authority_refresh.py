import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.t20_43b_r1_act_authority_refresh import (
    BASE_CLOSEOUT_REVIEWER_FILE_SHA256,
    BASE_IMMUTABLE_PATHS,
    REFRESH_OWNER_INSTRUCTION,
    REFRESH_OUTPUT_PATHS,
    build_refresh_acceptance,
    build_refresh_central_authority,
    build_refresh_owner_grant,
    build_refresh_permit,
    build_refresh_runtime_preflight,
    verify_refresh_acceptance,
    verify_refresh_owner_grant,
    verify_refresh_permit,
)
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (
    ATTEMPT_PATH,
    EXPECTED_DEPENDENCIES,
    MUJOCO_SUPPORT_SITE_PACKAGES,
    OWNER_GRANT_PATH,
    PERMIT_PATH,
    PRE_RUN_ACCEPTANCE_PATH,
    RENDERER_SMOKE_RECEIPT_PATH,
    RESNET18_CACHE_BYTES,
    RESNET18_CACHE_SHA256,
    SPEC_PATH,
    build_attempt_marker,
    load_verified_sources,
    verify_attempt_marker,
    verify_pre_run_acceptance,
)
from scenesmith.robot_lab.t20_43b_r1_act_materialization import (
    verify_materialized_authority,
)


class T2043bR1ACTAuthorityRefreshTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = load_verified_sources()
        self.spec = load_strict_json(SPEC_PATH)
        self.base = verify_materialized_authority()
        self.base_acceptance = load_strict_json(PRE_RUN_ACCEPTANCE_PATH)
        verify_pre_run_acceptance(
            self.base_acceptance, permit=self.base[PERMIT_PATH.as_posix()]
        )
        self.owner = build_refresh_owner_grant(
            spec=self.spec,
            base_bundle=self.base,
            base_acceptance=self.base_acceptance,
            required_source_commit="a" * 40,
            valid_from="2026-07-16T21:30:00-05:00",
            valid_until="2026-07-17T05:30:00-05:00",
        )
        self.request, self.decision = build_refresh_central_authority(
            sources=self.sources,
            spec=self.spec,
            base_bundle=self.base,
            owner_grant=self.owner,
        )

    def test_owner_refresh_is_bounded_and_not_a_second_attempt(self) -> None:
        verify_refresh_owner_grant(
            self.owner,
            spec=self.spec,
            base_bundle=self.base,
            base_acceptance=self.base_acceptance,
        )
        self.assertEqual(self.owner["refresh_epoch"], 2)
        self.assertEqual(self.owner["replacement_ordinal"], 1)
        self.assertEqual(self.owner["attempt_ordinal"], 1)
        self.assertEqual(self.owner["authorized_attempt_count"], 1)
        self.assertEqual(self.owner["owner_instruction"], REFRESH_OWNER_INSTRUCTION)
        self.assertFalse(self.owner["retry_or_sweep_authorized"])
        with self.assertRaises(ValueError):
            build_refresh_owner_grant(
                spec=self.spec,
                base_bundle=self.base,
                base_acceptance=self.base_acceptance,
                required_source_commit="a" * 40,
                valid_from="2026-07-16T21:30:00-05:00",
                valid_until="2026-07-17T05:30:01-05:00",
            )

    def test_central_composer_grants_only_simulation_training(self) -> None:
        self.assertEqual(
            self.decision["authority_granted"], ["simulation_training_ready"]
        )
        self.assertEqual(self.request["evaluation_time"], self.owner["valid_from"])

    def test_runtime_rejects_marker_or_base_artifact_drift(self) -> None:
        snapshot = self._runtime_snapshot()
        runtime = build_refresh_runtime_preflight(
            spec=self.spec,
            base_bundle=self.base,
            base_acceptance=self.base_acceptance,
            owner_grant=self.owner,
            request=self.request,
            decision=self.decision,
            runtime_snapshot=snapshot,
        )
        self.assertFalse(runtime["attempt_marker_exists"])
        for mutation in ("marker", "base"):
            changed = copy.deepcopy(snapshot)
            if mutation == "marker":
                changed["output_path_state"][ATTEMPT_PATH.as_posix()]["exists"] = True
                changed["attempt_marker_exists"] = True
            else:
                changed["base_artifact_file_sha256"][OWNER_GRANT_PATH.as_posix()] = (
                    "f" * 64
                )
            with self.assertRaises(ValueError):
                build_refresh_runtime_preflight(
                    spec=self.spec,
                    base_bundle=self.base,
                    base_acceptance=self.base_acceptance,
                    owner_grant=self.owner,
                    request=self.request,
                    decision=self.decision,
                    runtime_snapshot=changed,
                )

    def test_refresh_permit_and_acceptance_bind_ordinal_one(self) -> None:
        runtime = build_refresh_runtime_preflight(
            spec=self.spec,
            base_bundle=self.base,
            base_acceptance=self.base_acceptance,
            owner_grant=self.owner,
            request=self.request,
            decision=self.decision,
            runtime_snapshot=self._runtime_snapshot(),
        )
        permit = build_refresh_permit(
            spec=self.spec,
            base_bundle=self.base,
            base_acceptance=self.base_acceptance,
            owner_grant=self.owner,
            request=self.request,
            decision=self.decision,
            runtime_preflight=runtime,
        )
        verify_refresh_permit(
            permit,
            spec=self.spec,
            base_bundle=self.base,
            base_acceptance=self.base_acceptance,
            owner_grant=self.owner,
            request=self.request,
            decision=self.decision,
            runtime_preflight=runtime,
        )
        marker = build_attempt_marker(
            permit=permit,
            source_commit="b" * 40,
            started_at="2026-07-16T22:00:00-05:00",
        )
        verify_attempt_marker(marker, permit=permit)
        self.assertEqual(marker["attempt_ordinal"], 1)
        acceptance = build_refresh_acceptance(
            authority_commit="c" * 40,
            reviewer_decision_id="304",
            reviewer_path="docs/reviewer-messages/304-test.md",
            reviewer_file_sha256="d" * 64,
            permit=permit,
        )
        verify_refresh_acceptance(acceptance, permit=permit)
        self.assertEqual(acceptance["decision"], "ACCEPT_T20_43B_EPOCH_2_ATTEMPT_1")
        mutated = copy.deepcopy(permit)
        mutated["authorized_attempt_count"] = 2
        with self.assertRaises(ValueError):
            verify_refresh_permit(
                mutated,
                spec=self.spec,
                base_bundle=self.base,
                base_acceptance=self.base_acceptance,
                owner_grant=self.owner,
                request=self.request,
                decision=self.decision,
                runtime_preflight=runtime,
            )

    def _runtime_snapshot(self) -> dict:
        base_files = {
            path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in BASE_IMMUTABLE_PATHS
        }
        return {
            "source_commit": "a" * 40,
            "branch": "codex/pi05-autolearn-loop",
            "origin_contains_source_commit": True,
            "scoped_dirty_paths": [],
            "dependencies": dict(EXPECTED_DEPENDENCIES),
            "mps_available": True,
            "free_disk_bytes": 20 * 1024**3,
            "network_enabled": False,
            "dependency_fallback_enabled": False,
            "cached_backbone_file_sha256": RESNET18_CACHE_SHA256,
            "cached_backbone_size_bytes": RESNET18_CACHE_BYTES,
            "mujoco_support_site_packages": str(MUJOCO_SUPPORT_SITE_PACKAGES),
            "mujoco_support_tree_identity_sha256": "2" * 64,
            "renderer_smoke_identity_sha256": self.base[
                RENDERER_SMOKE_RECEIPT_PATH.as_posix()
            ]["identity_sha256"],
            "renderer_interpreter": "external/lerobot/.venv/bin/python",
            "renderer_interpreter_matches_runner": True,
            "renderer_smoke_exit_code": 0,
            "base_artifact_file_sha256": base_files,
            "base_closeout_reviewer_file_sha256": BASE_CLOSEOUT_REVIEWER_FILE_SHA256,
            "base_acceptance_identity_sha256": self.base_acceptance["identity_sha256"],
            "output_path_state": {
                path.as_posix(): {"exists": False, "is_symlink": False}
                for path in REFRESH_OUTPUT_PATHS
            },
            "attempt_marker_exists": False,
        }


if __name__ == "__main__":
    unittest.main()

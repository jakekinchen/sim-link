import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.counterexample_archive import (
    RECEIPT_PATH,
    build_archive_index,
    build_receipt_ref,
    build_seed_receipt,
    load_verified_sources,
    validate_lifecycle_transition,
    validate_routing,
)


class CounterexampleArchiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()
        cls.receipt = build_seed_receipt(sources=cls.sources)
        cls.ref = build_receipt_ref(path=RECEIPT_PATH, payload=cls.receipt)

    def test_seed_is_truthful_evidence_only_source_controller_negative(self) -> None:
        receipt = self.receipt
        self.assertEqual(receipt["counterexample_id"], "cex-0001")
        self.assertEqual(receipt["failure_class"], "source_controller_boundary_negative")
        self.assertEqual(receipt["cell"]["value"], 1.05)
        self.assertEqual(receipt["predicate_evidence"]["terminal_outcome"], "lifted_without_strict_cycle")
        self.assertFalse(receipt["policy_regression_blame_allowed"])
        self.assertFalse(receipt["replay_eligible"])
        self.assertFalse(receipt["training_ingestion_eligible"])
        self.assertFalse(receipt["source_refs"]["full_trace_evidence"]["remotely_retained"])
        self.assertFalse(
            receipt["source_refs"]["full_trace_evidence"][
                "local_copy_verified_for_archive"
            ]
        )
        self.assertTrue(
            receipt["source_refs"]["full_trace_evidence"][
                "receipt_derived_without_trace_bytes"
            ]
        )

    def test_index_is_deterministic_and_denies_activation(self) -> None:
        index = build_archive_index(receipt_refs=[self.ref], receipts=[self.receipt])
        self.assertEqual(index["entry_count"], 1)
        self.assertEqual(index["active_entry_count"], 1)
        self.assertFalse(index["replay_gate_active"])
        self.assertFalse(index["training_ingestion_active"])

    def test_active_duplicate_and_path_alias_fail_closed(self) -> None:
        duplicate = copy.deepcopy(self.receipt)
        duplicate["archive_sequence"] = 2
        duplicate["counterexample_id"] = "cex-0002"
        duplicate["canonical_counterexample_id"] = "cex-0002"
        duplicate = sign_payload(duplicate)
        duplicate_ref = build_receipt_ref(
            path=Path("configurations/robot_lab/t20_39_counterexample_receipt_0002.json"),
            payload=duplicate,
        )
        with self.assertRaisesRegex(ValueError, "duplicate|alias"):
            build_archive_index(
                receipt_refs=[self.ref, duplicate_ref],
                receipts=[self.receipt, duplicate],
            )
        alias = {**duplicate_ref, "path": self.ref["path"]}
        with self.assertRaises(ValueError):
            build_archive_index(
                receipt_refs=[self.ref, alias],
                receipts=[self.receipt, duplicate],
            )
        reference = copy.deepcopy(duplicate)
        reference["lifecycle_state"] = "superseded"
        reference["canonical_counterexample_id"] = "cex-0001"
        reference["duplicate_of_counterexample_id"] = "cex-0001"
        reference = sign_payload(reference)
        reference_ref = build_receipt_ref(
            path=Path("configurations/robot_lab/t20_39_counterexample_receipt_0002.json"),
            payload=reference,
        )
        index = build_archive_index(
            receipt_refs=[self.ref, reference_ref],
            receipts=[self.receipt, reference],
        )
        self.assertEqual(index["entry_count"], 2)
        self.assertEqual(index["active_entry_count"], 1)

    def test_lifecycle_transitions_are_one_way_and_history_preserving(self) -> None:
        for target in ("superseded", "retired", "invalid"):
            validate_lifecycle_transition(current="active", target=target)
        validate_lifecycle_transition(current="superseded", target="invalid")
        for current, target in (("invalid", "active"), ("retired", "active"), ("active", "active")):
            with self.assertRaises(ValueError):
                validate_lifecycle_transition(current=current, target=target)

    def test_routing_blocks_policy_blame_missing_trace_replay_and_training(self) -> None:
        route = validate_routing(
            routing_class="evidence_only",
            policy_owned_evidence=False,
            full_trace_remotely_retained=False,
            requested_policy_blame=False,
            requested_replay_gate=False,
            requested_training_ingestion=False,
        )
        self.assertFalse(route["fixed_replay_eligible"])
        with self.assertRaisesRegex(ValueError, "policy blame"):
            validate_routing(
                routing_class="policy_regression_candidate",
                policy_owned_evidence=False,
                full_trace_remotely_retained=True,
                requested_policy_blame=True,
                requested_replay_gate=False,
                requested_training_ingestion=False,
            )
        with self.assertRaisesRegex(ValueError, "retained trace"):
            validate_routing(
                routing_class="fixed_regression_candidate",
                policy_owned_evidence=False,
                full_trace_remotely_retained=False,
                requested_policy_blame=False,
                requested_replay_gate=False,
                requested_training_ingestion=False,
            )
        for replay, training in ((True, False), (False, True)):
            with self.assertRaisesRegex(ValueError, "new authority"):
                validate_routing(
                    routing_class="evidence_only",
                    policy_owned_evidence=False,
                    full_trace_remotely_retained=False,
                    requested_policy_blame=False,
                    requested_replay_gate=replay,
                    requested_training_ingestion=training,
                )

    def test_source_drift_fails_before_receipt(self) -> None:
        drift = copy.deepcopy(self.sources)
        drift["manifest"] = copy.deepcopy(self.sources["manifest"])
        drift["manifest"]["cells"][11]["value"] = 1.0
        with self.assertRaises(ValueError):
            build_seed_receipt(sources=drift)


if __name__ == "__main__":
    unittest.main()

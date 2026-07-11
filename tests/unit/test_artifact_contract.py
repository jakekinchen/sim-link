from __future__ import annotations

import json
import math
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    require_finite_number,
    sign_payload,
    validate_content_addressed_evidence,
    validate_inertia_tensor,
    validate_unique_ids,
    verify_signed_payload,
)


class ArtifactContractTests(unittest.TestCase):
    def test_strict_json_rejects_nonstandard_constants(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "artifact.json"
                path.write_text(f'{{"value": {constant}}}', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Non-finite JSON constant"):
                    load_strict_json(path)

    def test_canonical_writer_rejects_nan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                dump_canonical_json(Path(tmpdir) / "artifact.json", {"value": math.nan})

    def test_finite_number_rejects_nan_and_infinity(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaisesRegex(ValueError, "finite number"):
                require_finite_number(value, label="mass")

    def test_unique_ids_reject_blank_and_duplicate(self):
        with self.assertRaisesRegex(ValueError, "nonblank"):
            validate_unique_ids([{"measurement_id": " "}], field="measurement_id", label="measurement")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_unique_ids(
                [{"measurement_id": "m1"}, {"measurement_id": "m1"}],
                field="measurement_id",
                label="measurement",
            )

    def test_inertia_rejects_symmetric_indefinite_tensor(self):
        with self.assertRaisesRegex(ValueError, "positive semidefinite"):
            validate_inertia_tensor(
                [[1.0, 2.0, 0.0], [2.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                label="inertia",
            )

    def test_inertia_checks_triangle_on_principal_moments(self):
        with self.assertRaisesRegex(ValueError, "principal moments"):
            validate_inertia_tensor(
                [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 3.0]],
                label="inertia",
            )

    def test_evidence_requires_content_hash_and_nonblank_identity(self):
        with self.assertRaisesRegex(ValueError, "nonblank"):
            validate_content_addressed_evidence(
                [{"kind": "measurement_record", "ref": "", "sha256": "0" * 64}],
                label="measurement",
            )
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            validate_content_addressed_evidence(
                [{"kind": "measurement_record", "ref": "record.json", "sha256": "None"}],
                label="measurement",
            )

    def test_signing_is_canonical_and_rejects_tamper(self):
        left = sign_payload({"b": 2, "a": 1})
        right = sign_payload({"a": 1, "b": 2})
        self.assertEqual(left["identity_sha256"], right["identity_sha256"])
        self.assertEqual(canonical_json_bytes({"b": 2, "a": 1}), b'{"a":1,"b":2}')
        verify_signed_payload(left, label="test")
        left["a"] = 3
        with self.assertRaisesRegex(ValueError, "identity hash"):
            verify_signed_payload(left, label="test")


if __name__ == "__main__":
    unittest.main()

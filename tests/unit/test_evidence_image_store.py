"""Tests for append-only content-addressed evidence image storage."""

from __future__ import annotations

import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.evidence_image_store import (
    build_image_manifest,
    store_image_bytes,
    verify_image_manifest,
    verify_image_ref,
)


class EvidenceImageStoreTests(unittest.TestCase):
    def test_store_is_content_addressed_and_manifest_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sim-link-image-store-") as directory:
            root = Path(directory)
            first = store_image_bytes(root, b"png-proof-bytes")
            second = store_image_bytes(root, b"png-proof-bytes")
            self.assertEqual(first, second)
            manifest = build_image_manifest(
                root,
                [first],
                source_identity_sha256="a" * 64,
            )
            verify_image_manifest(manifest, root, source_identity_sha256="a" * 64)
            self.assertEqual(manifest, build_image_manifest(root, [first], source_identity_sha256="a" * 64))

    def test_tampering_and_path_escape_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sim-link-image-store-") as directory:
            root = Path(directory)
            reference = store_image_bytes(root, b"png-proof-bytes")
            (root / reference["path"]).write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                verify_image_ref(root, reference)
            with self.assertRaises(ValueError):
                verify_image_ref(
                    root,
                    {**reference, "path": "../outside.png"},
                )


if __name__ == "__main__":
    unittest.main()

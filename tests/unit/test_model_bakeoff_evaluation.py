"""T20.7 closed-loop evidence validation tests."""

from __future__ import annotations

import base64
import hashlib
import io
import unittest

from PIL import Image

from scenesmith.robot_lab.model_bakeoff_evaluation import (
    _verify_margin,
    _verify_rendered_image,
)


class ModelBakeoffEvaluationTests(unittest.TestCase):
    def test_margin_derivation_retains_measured_threshold_and_none(self) -> None:
        _verify_margin(
            {
                "measured": 0.79,
                "threshold": 0.8,
                "comparison": ">=",
                "margin": -0.010000000000000009,
                "passed": False,
            }
        )
        _verify_margin(
            {
                "measured": None,
                "threshold": 0.8,
                "comparison": ">=",
                "margin": None,
                "passed": False,
            }
        )
        with self.assertRaisesRegex(ValueError, "derivation drifted"):
            _verify_margin(
                {
                    "measured": 0.79,
                    "threshold": 0.8,
                    "comparison": ">=",
                    "margin": 0.0,
                    "passed": True,
                }
            )

    def test_keyframe_png_bytes_dimensions_and_hash_are_bound(self) -> None:
        stream = io.BytesIO()
        Image.new("RGB", (256, 256), (1, 2, 3)).save(stream, format="PNG")
        raw = stream.getvalue()
        payload = {
            "encoding": "png",
            "channels": 3,
            "width": 256,
            "height": 256,
            "image_sha256": hashlib.sha256(raw).hexdigest(),
            "png_base64": base64.b64encode(raw).decode("ascii"),
        }
        _verify_rendered_image(payload, expected_size=256)
        payload["image_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash drifted"):
            _verify_rendered_image(payload, expected_size=256)


if __name__ == "__main__":
    unittest.main()

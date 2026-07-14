from __future__ import annotations

import unittest

import numpy as np

from scenesmith.robot_lab.grasp_evidence import (
    KEYFRAME_IMAGE_SIZE,
    encode_png_image,
    validate_rendered_keyframes,
)


class GraspEvidenceTests(unittest.TestCase):
    def test_png_encoding_is_self_validating(self) -> None:
        image = np.zeros(
            (KEYFRAME_IMAGE_SIZE, KEYFRAME_IMAGE_SIZE, 3), dtype=np.uint8
        )
        encoded = encode_png_image(image, image_size=KEYFRAME_IMAGE_SIZE)
        keyframes = [
            {"phase": phase, "frame_index": index, "images": {"top": encoded, "wrist": encoded}}
            for index, phase in enumerate(("pregrasp", "close", "grasp_hold"))
        ]
        validate_rendered_keyframes(keyframes)

    def test_keyframe_contract_rejects_fewer_than_three_frames(self) -> None:
        with self.assertRaisesRegex(ValueError, "3-5"):
            validate_rendered_keyframes([])


if __name__ == "__main__":
    unittest.main()

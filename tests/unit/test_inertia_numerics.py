from __future__ import annotations

import math
import unittest
from unittest import mock

import numpy as np

import scenesmith.robot_lab.artifact_contract as artifact_contract

from scenesmith.robot_lab.artifact_contract import (
    symmetric_eigenvalues,
    validate_inertia_tensor,
)


class InertiaNumericsTests(unittest.TestCase):
    def test_randomized_eigenvalues_match_numpy_across_scales(self):
        rng = np.random.default_rng(3607)
        special_spectra = (
            np.array([-0.75, 0.125, 1.0]),
            np.array([0.5, 0.5, 0.5]),
            np.array([1.0, 1.0 + 1e-12, 2.0]),
            np.array([0.0, 1e-12, 1.0]),
        )
        for scale in (1e-240, 1.0, 1e240):
            for case in range(24):
                rotation, _ = np.linalg.qr(rng.normal(size=(3, 3)))
                if np.linalg.det(rotation) < 0.0:
                    rotation[:, 0] *= -1.0
                spectrum = (
                    special_spectra[case]
                    if case < len(special_spectra)
                    else np.sort(rng.uniform(-1.0, 1.0, size=3))
                )
                matrix = rotation @ np.diag(scale * spectrum) @ rotation.T
                expected = np.linalg.eigvalsh(matrix)
                actual = symmetric_eigenvalues(matrix.tolist(), label=f"random case {case}")
                np.testing.assert_allclose(
                    actual,
                    expected,
                    rtol=5e-12,
                    atol=scale * 5e-13,
                )
                self.assertEqual(
                    actual,
                    symmetric_eigenvalues(matrix.tolist(), label=f"random case {case}"),
                )

    def test_physical_inertia_is_rotation_and_scale_invariant(self):
        rotation = np.array(
            [
                [0.36, -0.48, 0.8],
                [0.8, 0.60, 0.0],
                [-0.48, 0.64, 0.60],
            ]
        )
        np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-15)
        self.assertGreater(np.linalg.det(rotation), 0.0)
        for scale in (1e-250, 1.0, 1e250):
            moments = scale * np.array([2.0, 3.0, 4.0])
            rotated = rotation @ np.diag(moments) @ rotation.T
            validate_inertia_tensor(rotated.tolist(), label="rotated physical inertia")
            np.testing.assert_allclose(
                symmetric_eigenvalues(rotated.tolist(), label="rotated physical inertia"),
                moments,
                rtol=5e-13,
                atol=scale * 5e-14,
            )

    def test_scale_relative_symmetry_accepts_roundoff_but_rejects_drift(self):
        for scale in (1e-220, 1.0, 1e220):
            roundoff = [
                [2.0 * scale, (0.25 + 2.5e-11) * scale, 0.0],
                [(0.25 - 2.5e-11) * scale, 2.0 * scale, 0.0],
                [0.0, 0.0, 2.0 * scale],
            ]
            validate_inertia_tensor(roundoff, label="roundoff inertia")
            np.testing.assert_allclose(
                symmetric_eigenvalues(roundoff, label="roundoff inertia"),
                np.array([1.75, 2.0, 2.25]) * scale,
                rtol=1e-13,
                atol=scale * 1e-13,
            )
            drifted = [row[:] for row in roundoff]
            drifted[0][1] += 5e-9 * scale
            with self.assertRaisesRegex(ValueError, "symmetric"):
                validate_inertia_tensor(drifted, label="drifted inertia")

    def test_triangle_tolerance_is_relative_across_scales(self):
        for scale in (1e-240, 1.0, 1e240):
            validate_inertia_tensor(
                [
                    [scale, 0.0, 0.0],
                    [0.0, scale, 0.0],
                    [0.0, 0.0, 2.0 * scale],
                ],
                label="boundary triangle inertia",
            )
            with self.assertRaisesRegex(ValueError, "principal moments"):
                validate_inertia_tensor(
                    [
                        [scale, 0.0, 0.0],
                        [0.0, scale, 0.0],
                        [0.0, 0.0, (2.0 + 1e-8) * scale],
                    ],
                    label="invalid triangle inertia",
                )

    def test_near_singular_psd_is_accepted_and_relative_negative_is_rejected(self):
        rotation = np.array(
            [
                [0.0, 1.0, 0.0],
                [2**-0.5, 0.0, -2**-0.5],
                [-2**-0.5, 0.0, -2**-0.5],
            ]
        )
        near_singular = rotation @ np.diag([1e-16, 1.0, 1.0]) @ rotation.T
        validate_inertia_tensor(near_singular.tolist(), label="near-singular inertia")
        for scale in (1e-240, 1.0, 1e240):
            slightly_indefinite = [
                [-2e-10 * scale, 0.0, 0.0],
                [0.0, scale, 0.0],
                [0.0, 0.0, scale],
            ]
            with self.assertRaisesRegex(ValueError, "positive semidefinite"):
                validate_inertia_tensor(
                    slightly_indefinite,
                    label="slightly indefinite inertia",
                )

    def test_zero_signed_zero_and_repeated_eigenvalues_are_stable(self):
        zeros = symmetric_eigenvalues(
            [[-0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, -0.0]],
            label="signed zero inertia",
        )
        self.assertEqual(zeros, [0.0, 0.0, 0.0])
        self.assertTrue(all(math.copysign(1.0, value) == 1.0 for value in zeros))
        self.assertEqual(
            symmetric_eigenvalues(
                [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]],
                label="repeated inertia",
            ),
            [2.0, 2.0, 2.0],
        )

    def test_non_finite_inputs_and_eigen_results_fail_closed(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError,
                "finite number",
            ):
                validate_inertia_tensor(
                    [[value, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    label="non-finite inertia",
                )
        maximum = float.fromhex("0x1.fffffffffffffp+1023")
        with self.assertRaisesRegex(ValueError, "non-finite eigenvalues"):
            symmetric_eigenvalues(
                [[maximum, maximum, maximum]] * 3,
                label="overflowing eigensystem",
            )

    def test_iteration_limit_and_bad_residual_fail_closed(self):
        with mock.patch.object(artifact_contract, "JACOBI_MAX_ITERATIONS", 0):
            with self.assertRaisesRegex(ValueError, "did not converge"):
                symmetric_eigenvalues(
                    [[1.0, 0.25, 0.0], [0.25, 2.0, 0.0], [0.0, 0.0, 3.0]],
                    label="iteration-limited inertia",
                )
        with mock.patch.object(
            artifact_contract,
            "_jacobi_eigendecomposition",
            return_value=([0.0, 0.0, 0.0], np.eye(3).tolist()),
        ):
            with self.assertRaisesRegex(ValueError, "residual exceeded tolerance"):
                symmetric_eigenvalues(
                    [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]],
                    label="bad residual inertia",
                )

    def test_relative_tolerance_must_be_finite_positive_and_less_than_one(self):
        matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        for tolerance in (0.0, -1e-10, math.nan, math.inf, 1.0):
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                symmetric_eigenvalues(
                    matrix,
                    label="invalid tolerance inertia",
                    tolerance=tolerance,
                )


if __name__ == "__main__":
    unittest.main()

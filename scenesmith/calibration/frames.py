"""Small rigid-transform helpers for emitting frames to sim formats.

Kept dependency-light (numpy only) so the exporters do not pull in a robotics
stack. Conventions match the consumers: quaternions are ``(w, x, y, z)`` for
MuJoCo, and roll-pitch-yaw is the URDF fixed-axis convention
``R = Rz(yaw) Ry(pitch) Rx(roll)``.
"""

from __future__ import annotations

import numpy as np


def rotation_to_quaternion(R: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation matrix to a ``(w, x, y, z)`` quaternion."""
    R = np.asarray(R, dtype=float)
    trace = np.trace(R)
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    else:
        i = int(np.argmax(np.diag(R)))
        if i == 0:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif i == 1:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def rotation_to_rpy(R: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation to URDF fixed-axis ``(roll, pitch, yaw)``."""
    R = np.asarray(R, dtype=float)
    sy = -R[2, 0]
    sy = float(np.clip(sy, -1.0, 1.0))
    pitch = np.arcsin(sy)
    if abs(sy) < 1.0 - 1e-9:
        roll = np.arctan2(R[2, 1], R[2, 2])
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:  # Gimbal lock.
        roll = np.arctan2(-R[1, 2], R[1, 1])
        yaw = 0.0
    return np.array([roll, pitch, yaw])


def fmt(values, places: int = 8) -> str:
    """Format a vector as a space-separated string for XML attributes."""
    return " ".join(f"{float(v):.{places}g}" for v in np.asarray(values).ravel())

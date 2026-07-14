"""Parametric, self-verifying calibration targets for the SO-101 workcell.

A single :class:`~scenesmith.calibration.spec.CalibrationTargetSpec` drives every
artifact: parametric CAD, exact mass properties, MuJoCo/URDF sim assets, a bill
of materials, a fiducial coordinate table, and a printable acceptance sheet.
The ground-truth mass, center of mass, and inertia are computed by exact signed
superposition and independently cross-checked (Monte-Carlo, and optionally
MuJoCo and trimesh) so the physical brick and its simulator twin share one
verified source of truth -- the ``sim`` <-> real ``link``.
"""

from __future__ import annotations

from scenesmith.calibration.configurations import (
    Cartridge,
    Configuration,
    ResolvedTarget,
    resolve_target,
    standard_kit,
)
from scenesmith.calibration.mass_properties import MassProperties, PrincipalInertia
from scenesmith.calibration.spec import CalibrationTargetSpec, default_so101_target

__all__ = [
    "CalibrationTargetSpec",
    "default_so101_target",
    "Configuration",
    "Cartridge",
    "ResolvedTarget",
    "resolve_target",
    "standard_kit",
    "MassProperties",
    "PrincipalInertia",
]

__version__ = "0.1.0"

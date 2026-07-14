"""Parametric, self-verifying calibration targets for the SO-101 workcell.

A single parametric spec drives every artifact: CAD geometry, exact mass
properties, MuJoCo/URDF sim assets, a bill of materials, a fiducial coordinate
table, a printable acceptance sheet, and an as-built receipt template. The
ground-truth mass, center of mass, and inertia are computed by exact signed
superposition and independently cross-checked (Monte-Carlo, and optionally
MuJoCo and trimesh) so the physical target and its simulator twin share one
verified source of truth -- the ``sim`` <-> real ``link``.

Two designs are provided:

* :class:`~scenesmith.calibration.wcw1.Wcw1Spec` -- the recommended Workcell
  Calibration Witness: precision bearing-ball cartridges (C0-C4), flat grasp
  faces with a tag-free contact band, five AprilTags, solid-print standard.
* :class:`~scenesmith.calibration.spec.CalibrationTargetSpec` -- the earlier
  slug-socket "calbrick" design.
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
from scenesmith.calibration.receipt import (
    CalibrationArtifactReceipt,
    apply_receipt,
    blank_receipt,
)
from scenesmith.calibration.spec import CalibrationTargetSpec, default_so101_target
from scenesmith.calibration.wcw1 import (
    Wcw1Configuration,
    Wcw1Spec,
    default_wcw1_target,
    resolve_wcw1,
    wcw1_kit,
)

__all__ = [
    "CalibrationTargetSpec",
    "default_so101_target",
    "Configuration",
    "Cartridge",
    "ResolvedTarget",
    "resolve_target",
    "standard_kit",
    "Wcw1Spec",
    "Wcw1Configuration",
    "default_wcw1_target",
    "wcw1_kit",
    "resolve_wcw1",
    "CalibrationArtifactReceipt",
    "blank_receipt",
    "apply_receipt",
    "MassProperties",
    "PrincipalInertia",
]

__version__ = "0.2.0"

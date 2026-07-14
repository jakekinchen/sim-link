"""Independent cross-checks of a target's analytic mass properties.

The analytic model composes closed-form primitive inertias with the
parallel-axis theorem. That algebra is where a sign or a Steiner-term bug would
hide, so it is checked three independent ways:

* **Monte-Carlo** (always available): brute-force integration of the identical
  signed-density field. Validates the closed-form inertia and parallel-axis
  math without reusing any of it.
* **trimesh** (optional): mesh-based volume integration (Mirtich's algorithm)
  of every primitive, combined by the same signed algebra. Validates the
  closed-form primitive inertias against a different integrator.
* **MuJoCo** (optional): round-trips the *emitted* MJCF and reads back the mass,
  center of mass, and principal inertia the simulator actually receives.

Agreement across independent methods is what lets the printed brick and its
simulator twin share one trusted ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scenesmith.calibration.configurations import ResolvedTarget
from scenesmith.calibration.mass_properties import MassProperties, combine_all
from scenesmith.calibration.primitives import Primitive


@dataclass
class VerifyResult:
    """Outcome of one cross-check against the analytic model."""

    method: str
    available: bool
    mass_rel_err: float = float("nan")
    com_err_mm: float = float("nan")
    inertia_rel_err: float = float("nan")
    passed: bool = False
    detail: str = ""

    def summary(self) -> str:
        if not self.available:
            return f"{self.method:11s}: unavailable ({self.detail})"
        flag = "PASS" if self.passed else "FAIL"
        return (
            f"{self.method:11s}: {flag}  "
            f"mass {self.mass_rel_err:.2e}  "
            f"com {self.com_err_mm:.2e} mm  "
            f"inertia {self.inertia_rel_err:.2e}"
        )


def _compare(
    reference: MassProperties, other: MassProperties
) -> tuple[float, float, float]:
    """Return (mass rel err, CoM abs err mm, inertia rel Frobenius err)."""
    mass_err = abs(other.mass - reference.mass) / abs(reference.mass)
    com_err = float(np.linalg.norm(other.com - reference.com)) * 1e3
    ref_I = reference.inertia_com
    inertia_err = float(np.linalg.norm(other.inertia_com - ref_I)) / float(
        np.linalg.norm(ref_I)
    )
    return mass_err, com_err, inertia_err


# --------------------------------------------------------------------------- #
# Monte-Carlo.
# --------------------------------------------------------------------------- #


def _aabb(primitives: list[Primitive]) -> tuple[np.ndarray, np.ndarray]:
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    for p in primitives:
        c = p.center
        if p.kind == "box":
            half = np.array([p.params["dx"], p.params["dy"], p.params["dz"]]) / 2
        elif p.kind in ("cylinder", "tube"):
            r = p.params["radius"]
            half = np.array([r, r, r])
            half[p.params["axis"]] = p.params["length"] / 2
        else:  # sphere
            half = np.full(3, p.params["radius"])
        lo = np.minimum(lo, c - half)
        hi = np.maximum(hi, c + half)
    return lo, hi


def verify_montecarlo(
    target: ResolvedTarget,
    n_samples: int = 500_000,
    seed: int = 0,
    chunk: int = 100_000,
    mass_tol: float | None = None,
    com_tol_mm: float | None = None,
    inertia_tol: float | None = None,
) -> VerifyResult:
    """Monte-Carlo integration of the signed-density field.

    Tolerances default to ``None``, in which case they scale as ``1/sqrt(N)`` to
    track the sampler's statistical error -- a fixed threshold would flag or miss
    failures depending only on the sample budget. Pass explicit tolerances to
    override. Bases are calibrated at N=500k with comfortable (~3x) margin over
    the observed error across seeds.
    """
    scale = (500_000.0 / n_samples) ** 0.5
    if mass_tol is None:
        mass_tol = 0.02 * scale
    if com_tol_mm is None:
        com_tol_mm = 0.6 * scale
    if inertia_tol is None:
        inertia_tol = 0.03 * scale
    prims = target.all_primitives
    lo, hi = _aabb(prims)
    box_vol = float(np.prod(hi - lo))
    rng = np.random.default_rng(seed)

    total_mass = 0.0
    first_moment = np.zeros(3)
    inertia_origin = np.zeros((3, 3))
    eye = np.eye(3)
    done = 0
    while done < n_samples:
        m = min(chunk, n_samples - done)
        pts = rng.uniform(lo, hi, size=(m, 3))
        density = np.zeros(m)
        for p in prims:
            density += np.where(p.contains(pts), p.density, 0.0)
        dm = density * box_vol / n_samples
        total_mass += float(dm.sum())
        first_moment += (dm[:, None] * pts).sum(axis=0)
        r2 = np.einsum("ij,ij->i", pts, pts)
        inertia_origin += np.einsum("i,jk->jk", dm * r2, eye) - np.einsum(
            "i,ij,ik->jk", dm, pts, pts
        )
        done += m

    est = MassProperties(total_mass, first_moment, inertia_origin)
    mass_err, com_err, inertia_err = _compare(target.mass_properties, est)
    passed = mass_err < mass_tol and com_err < com_tol_mm and inertia_err < inertia_tol
    return VerifyResult(
        "montecarlo",
        True,
        mass_err,
        com_err,
        inertia_err,
        passed,
        detail=f"n={n_samples}",
    )


# --------------------------------------------------------------------------- #
# trimesh (optional).
# --------------------------------------------------------------------------- #


def primitive_to_trimesh(primitive: Primitive, segments: int = 48):
    """Build a trimesh mesh for one primitive (unit density)."""
    import trimesh

    p = primitive.params
    if primitive.kind == "box":
        mesh = trimesh.creation.box(extents=[p["dx"], p["dy"], p["dz"]])
    elif primitive.kind == "cylinder":
        mesh = trimesh.creation.cylinder(
            radius=p["radius"], height=p["length"], sections=segments
        )
        mesh.apply_transform(_axis_transform(p["axis"]))
    elif primitive.kind == "tube":
        mesh = trimesh.creation.annulus(
            r_min=p["inner_radius"],
            r_max=p["radius"],
            height=p["length"],
            sections=segments,
        )
        mesh.apply_transform(_axis_transform(p["axis"]))
    elif primitive.kind == "sphere":
        # subdivisions=4 keeps the icosphere volume within ~0.03% of the true
        # sphere so ball-heavy targets stay inside the 1e-3 cross-check tol.
        mesh = trimesh.creation.icosphere(radius=p["radius"], subdivisions=4)
    else:  # pragma: no cover
        raise ValueError(primitive.kind)
    mesh.apply_translation(primitive.center)
    return mesh


def _axis_transform(axis: int) -> np.ndarray:
    """Rotate the default +z extrusion axis onto the requested axis."""
    T = np.eye(4)
    if axis == 0:  # z -> x
        T[:3, :3] = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
    elif axis == 1:  # z -> y
        T[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    return T


def verify_trimesh(target: ResolvedTarget, tol: float = 1e-3) -> VerifyResult:
    """Mesh-integration cross-check via trimesh (if installed)."""
    try:
        import trimesh  # noqa: F401
    except Exception as exc:  # pragma: no cover - optional dependency
        return VerifyResult("trimesh", False, detail=str(exc))

    bodies = []
    for p in target.all_primitives:
        mesh = primitive_to_trimesh(p, segments=target.spec.triangulation_segments)
        sign = -1.0 if p.density < 0 else 1.0
        mesh.density = abs(p.density)
        mp = MassProperties.from_centroid(
            sign * float(mesh.mass),
            np.asarray(mesh.center_mass, dtype=float),
            sign * np.asarray(mesh.moment_inertia, dtype=float),
        )
        bodies.append(mp)
    est = combine_all(bodies)
    mass_err, com_err, inertia_err = _compare(target.mass_properties, est)
    passed = mass_err < tol and inertia_err < tol and com_err < 0.05
    return VerifyResult(
        "trimesh",
        True,
        mass_err,
        com_err,
        inertia_err,
        passed,
        detail="mesh integration",
    )


# --------------------------------------------------------------------------- #
# MuJoCo (optional).
# --------------------------------------------------------------------------- #


def verify_mujoco(target: ResolvedTarget, tol: float = 1e-4) -> VerifyResult:
    """Round-trip the emitted MJCF and compare the inertia MuJoCo receives."""
    try:
        import mujoco
    except Exception as exc:  # pragma: no cover - optional dependency
        return VerifyResult("mujoco", False, detail=str(exc))

    from scenesmith.calibration.export_mjcf import to_mjcf_string

    xml = to_mjcf_string(target, include_scene=False, freejoint=False)
    model = mujoco.MjModel.from_xml_string(xml)
    body_name = f"{target.spec.name}_{target.config.name}"
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)

    ref = target.mass_properties
    mass = float(model.body_mass[bid])
    com = np.asarray(model.body_ipos[bid], dtype=float)
    principal = np.sort(np.asarray(model.body_inertia[bid], dtype=float))

    mass_err = abs(mass - ref.mass) / abs(ref.mass)
    com_err = float(np.linalg.norm(com - ref.com)) * 1e3
    ref_principal = np.sort(ref.principal_axes().moments)
    inertia_err = float(
        np.linalg.norm(principal - ref_principal) / np.linalg.norm(ref_principal)
    )
    passed = mass_err < tol and inertia_err < tol and com_err < 1e-3
    return VerifyResult(
        "mujoco",
        True,
        mass_err,
        com_err,
        inertia_err,
        passed,
        detail="MJCF round-trip",
    )


def verify_all(target: ResolvedTarget, mc_samples: int = 500_000) -> list[VerifyResult]:
    """Run every available cross-check and return their results."""
    return [
        verify_montecarlo(target, n_samples=mc_samples),
        verify_trimesh(target),
        verify_mujoco(target),
    ]

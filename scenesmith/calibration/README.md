# SO-101 Calibration Workcell — parametric target kit

A parametric, self-verifying generator for a reproducible 3D-printed calibration
target ("calbrick") for the self-calibrating SO-101 arm. One spec drives every
artifact, so the physical brick and its simulator twin share a single, verified
ground truth — the *sim ↔ real link* the workcell needs.

This is the "build a small versioned calibration kit, not just an STL" idea,
made concrete: instead of hoping a printed benchmark object has the mass
properties you assume, you **compute** mass, center of mass, and inertia by exact
signed superposition, **cross-check** them three independent ways, and **emit**
the sim assets, print files, BOM, fiducial table, and an acceptance sheet from
the same source.

## Why not just reuse an existing object?

Fiducial Exoskeletons, FMB, adjustable-inertia wheels, etc. each cover a *piece*
(fiducials, or grasp geometry, or variable inertia), but none is an all-in-one
workcell target with **traceable** mass properties, controlled grasp geometry,
fiducials, and replaceable contact surfaces. More importantly, a printed
benchmark's *actual* density and inertia are unknown — FDM infill alone can move
mass by tens of percent. So the useful artifact is not a mesh; it is a
**parametric model plus a measurement loop** that pins the numbers to the
physical part.

## What this generator produces

```
python -m scenesmith.calibration --out dist/calbrick --verify --watertight --step
```

For a content-hashed revision directory:

| Artifact | Purpose |
|---|---|
| `calibration_target.json` | Machine-readable ground truth: per-config mass/CoM/inertia, fiducial poses, tag→CoM vectors, coupons, tolerances. Consumed by both the real pipeline and the simulator. |
| `acceptance.md` | Printable QA sheet: predicted values, tolerances, and the measure/weigh/back-calc procedure. |
| `mjcf/<config>.xml`, `<config>_scene.xml` | MuJoCo assets with the exact analytic inertial + named sites; the scene variant is a drop/sys-ID rig. |
| `urdf/<config>.urdf` | Drake/ROS asset with fiducial + grasp frames as named links. |
| `bom/<config>.csv` | Traceable bill of materials — every gram as a labeled part. |
| `fiducials.csv` | Exact AprilTag poses in the body frame. |
| `stl/<config>_preview.stl` | Dependency-free preview mesh. |
| `stl/shell_watertight.stl` | Watertight print mesh (needs trimesh+manifold3d). |
| `shell.step` | True parametric CAD for slicing (needs build123d). |

## Design (parametric, in `spec.py`)

- **Hollow shell** with a **grasp rib** (jaw-spaced for the SO-101 gripper) that
  carries the top AprilTag; two more tags on orthogonal side faces.
- A **3×3 socket grid** holding steel **cartridge slugs**. The loadout, not the
  shell, sets the mass distribution.
- **Replaceable friction coupons** on contact faces — friction is a property of
  the *contact pair*, so its coefficients live on swappable coupons keyed by
  counter-surface, never baked into the object.

## The three standard configurations (`configurations.py`)

| Config | What it isolates |
|---|---|
| `centered` | Baseline: cartridges packed at the center — planar CoM on-axis, low inertia. |
| `offset` | A **known off-axis CoM** (mass at the +x socket). |
| `high_inertia` | **Same total mass** as `centered`, moved to the corners — unchanged planar CoM, markedly larger inertia. Isolates the inertia term from the mass term. |

`centered` and `high_inertia` are mass-matched by construction, so an estimator
that nails mass but misjudges inertia is exposed directly.

## Exact + verified mass properties

Mass properties are computed as an exact **signed superposition** of primitive
solids (hollow shell = outer `+ρ` ⊕ cavity `−ρ`; pockets and bores are more
negative primitives; slugs and coupons are positive). Every contribution is a
labeled row, so the BOM *is* the mass model. The result is checked three
independent ways (`verify.py`):

1. **Monte-Carlo** integration of the identical signed-density field (numpy).
2. **trimesh** mesh-volume integration of each primitive (Mirtich), combined by
   the same algebra — a different integrator.
3. **MuJoCo** round-trip of the emitted MJCF — the inertia the simulator
   actually receives.

They agree to ~1e-3 (MC, statistical), ~1e-4 (trimesh), and ~1e-9 (MuJoCo).

## The measurement loop (what makes it real)

Nominal density is only a starting guess. The workflow closes the loop:

1. Print the bare shell; the sheet predicts its net plastic mass.
2. Weigh it and feed the reading back:
   `spec.with_measured_shell_mass(grams, shell_solid_volume_m3)`.
3. Weigh the slugs: `spec.with_measured_slug_mass(grams)`.
4. Regenerate — every asset and the ground-truth bundle now reflect the *as-built*
   part, traceable via the spec content hash.

## Dependencies

The core (spec, mass properties, verification, MJCF/URDF/BOM/STL preview) needs
only **numpy**. `trimesh`+`manifold3d` enable the watertight STL and the mesh
cross-check; `mujoco` enables the round-trip check; `build123d` enables STEP.
All optional paths degrade gracefully.

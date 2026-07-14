# SO-101 Calibration Workcell — parametric target kit

A parametric, self-verifying generator for reproducible 3D-printed calibration
targets for the self-calibrating SO-101 arm. One spec drives every artifact, so
the physical target and its simulator twin share a single, verified ground
truth — the *sim ↔ real link* the workcell needs.

The deliverable standard is **CAD plus a receipt, not an STL**: the model
computes mass, center of mass, and inertia by exact signed superposition,
cross-checks them three independent ways, and the simulator inertials are
regenerated from *measured* as-built values, never from nominal slicer density.

## Designs

### WCW-1 (recommended) — the Workcell Calibration Witness

```
python -m scenesmith.calibration --out dist/wcw1 --metrology --watertight
```

A 40 × 60 × 65 mm body (40 mm is the grasp thickness between flat, parallel
gripper faces) with:

- **Precision bearing-ball cartridges.** 20 mm G25 AISI 52100 chrome-steel
  balls (ISO 3290-1): certified diameter, orientation-independent inertia,
  self-locating, ~32.7 g nominal — with the *measured* mass entering the model
  via the receipt. Buy ~10, select a matched set; record supplier/grade/lot.
- **A tag-free 18 mm contact band** on both grasp faces — the gripper touches
  bare reference PLA, never a marker. Five AprilTag 36h11 fiducials: top, both
  side faces, and one small tag above the band on each grasp face. No tag on
  the sliding bottom.
- **Keyed cartridges C0–C4** that isolate one physical term per pair:

| Config | Balls | What it isolates |
|---|---|---|
| C0 | — | Printed shell; perception / light-payload baseline |
| C1 | 1 @ y=0 | Known centered payload |
| C2 | 1 @ y=+15 | **CoM shift at identical total mass** (Δ CoM ≈ 3.7 mm)* |
| C3 | 2 @ y=±11 | Centered mass, lower rotational inertia |
| C4 | 2 @ y=±15 | **Same mass AND same CoM as C3, ~8–11% higher inertia** |

\* The model accounts for the seat void moving with the ball — the naive
`m·d/M` estimate overshoots by ~19%.

- **Solid printing standard**: explicit CAD shell, full walls, 100% fill for
  printed solid regions — no slicer sparse infill, so geometry-based inertia is
  meaningful. Reference build: Bambu A1 (Mini) + AMS Lite, 0.4 mm nozzle,
  0.20 mm layers, PLA Basic; any printer is conformant if the part passes the
  same acceptance checks.
- **Metrology extras** (`--metrology`): a separate 100 × 75 mm D405
  depth-characterization plate (0°/30°/45° planes, 10 mm step, 12/24 mm
  vertical cylinders, horizontal half-cylinder, hemisphere — depth behavior is
  reported per feature and incidence, never as one number) and a stepped
  38/40/42 mm grip-fit gauge to verify the gripper span empirically before the
  full print. These stay **off** the manipulable body: depth targets want
  curves and wedges; a graspable object wants flat faces.

Modeling idealizations (absorbed by the receipt): ball seats are modeled as
exact spherical voids (physical carriers use a 3-point cradle + retainer and
are weighed individually); the flush lid is modeled as part of the closed
shell; edge chamfers and the orientation notch are unmodeled.

### calbrick (legacy) — slug-socket brick

```
python -m scenesmith.calibration --design calbrick --out dist/calbrick
```

The earlier design: 3×3 socket grid of steel slugs, grasp rib, bonded friction
coupons. Kept for comparison; WCW-1's ball cartridges and flat grasp faces are
metrologically stronger.

## What a kit directory contains

| Artifact | Purpose |
|---|---|
| `calibration_target.json` | Machine-readable ground truth: per-config mass/CoM/inertia, fiducial poses, tag→CoM vectors, tolerances. Consumed by both the real pipeline and the simulator. |
| `receipt_template.json` | The as-built record to fill in: printer, slicer profile, filament lots, ball supplier/grade, measured dimensions and masses. `apply_receipt()` regenerates the model from it. |
| `acceptance.md` | Printable QA sheet: predicted values, tolerances, weigh/balance procedures. |
| `mjcf/`, `urdf/` | MuJoCo / Drake / ROS assets with the exact analytic inertial and named `tag_*`, `grasp`, `com` frames. `*_scene.xml` adds a floor + freejoint for drop/sys-ID runs. |
| `bom/` | Per-config traceable bill of materials — every gram is a labeled row. |
| `fiducials.csv` | Exact AprilTag poses in the body frame. |
| `stl/` | Preview meshes + watertight print mesh (trimesh). |
| `metrology/` | Depth plate + grip gauge STLs and feature manifests. |

## Exact + verified mass properties

Mass properties are an exact **signed superposition** of primitives (shell =
outer `+ρ` ⊕ cavity `−ρ`; recesses and seat voids negative; balls/slugs
positive), verified three independent ways (`verify.py`):

1. **Monte-Carlo** integration of the identical signed-density field
   (tolerances scale as `1/√N`);
2. **trimesh** mesh-volume integration per primitive (a different integrator);
3. **MuJoCo** round-trip of the emitted MJCF — the inertia the simulator
   actually receives.

Agreement: ~1e-3 (MC), ~1e-4 (trimesh), ~1e-9 (MuJoCo).

## The measurement loop

1. Print the grip gauge; confirm the gripper spans 40 mm.
2. Print body + lid + all carriers in one job; weigh everything per the
   acceptance sheet; weigh and select the matched ball set.
3. Fill in `receipt_template.json` → `apply_receipt(spec, receipt)` →
   regenerate. Every asset now reflects the as-built part, traceable via the
   spec content hash.
4. Balance-check the centered configs (C0/C1) on a knife edge (±1 mm);
   optionally bifilar-pendulum the yaw inertia.

Friction note: coefficients are **pair properties**. The printed PLA face is
the standardized half; the gripper/table are the site-specific halves. Fit
*effective contact parameters* per pair from push/lift probes — never claim a
universal PLA friction coefficient.

## Dependencies

Core (spec, mass properties, MC verification, MJCF/URDF/BOM/receipt) needs only
**numpy**. `trimesh`+`manifold3d` add watertight STLs, the mesh cross-check,
and metrology parts; `mujoco` adds the round-trip check; `build123d` adds STEP
(calbrick only, for now). All optional paths degrade gracefully.

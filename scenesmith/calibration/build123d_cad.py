"""Optional true-parametric CAD via build123d (STEP + watertight STL).

This is the production path: it builds a real B-rep solid with proper boolean
operations from the *same* :class:`CalibrationTargetSpec`, so the STEP handed to
a slicer matches the physics model feature for feature. It is imported lazily and
degrades gracefully -- the runnable core (mass properties, MJCF/URDF, verifiers)
never depends on build123d or OpenCascade being installed.

Note on assembly: the modeled shell is a closed hollow box. A physical unit
needs a way to insert cartridges -- print the base face (-z) as a separate
friction-coupon lid, or add a parametric access port here. The added lid is the
same material and mass whether modeled integrally or bonded, so the ground-truth
mass model is unaffected.
"""

from __future__ import annotations

from pathlib import Path

from scenesmith.calibration.spec import CalibrationTargetSpec


def available() -> bool:
    """Return True if build123d can be imported."""
    try:
        import build123d  # noqa: F401

        return True
    except Exception:
        return False


def build_shell(spec: CalibrationTargetSpec):
    """Build the printable shell B-rep (dimensions in millimeters).

    Returns:
        A ``build123d`` ``Part`` (solid). Raises ImportError if build123d is
        not installed.
    """
    from build123d import Axis, Box, BuildPart, Cylinder, Locations, Mode

    L, W, H = spec.length_mm, spec.width_mm, spec.height_mm
    t = spec.wall_mm
    ci_x, ci_y, ci_z = spec.cavity_extents_mm()
    sg = spec.sockets
    r_bore = sg.bore_diameter_mm / 2
    r_guide = r_bore + sg.guide_wall_mm
    cavity_floor_z = -H / 2 + t
    floor_z = cavity_floor_z + sg.floor_clearance_mm
    tube_center_z = floor_z + sg.depth_mm / 2

    with BuildPart() as part:
        Box(L, W, H)
        Box(ci_x, ci_y, ci_z, mode=Mode.SUBTRACT)  # cavity

        # Grasp rib on +z.
        if spec.grasp.face == "+z":
            with Locations((0, 0, H / 2 + spec.grasp.height_mm / 2)):
                Box(spec.grasp.length_mm, spec.grasp.width_mm, spec.grasp.height_mm)

        # Cartridge guide tubes.
        for _i, _j, x, y in sg.positions_mm():
            with Locations((x, y, tube_center_z)):
                Cylinder(radius=r_guide, height=sg.depth_mm)
                Cylinder(radius=r_bore, height=sg.depth_mm, mode=Mode.SUBTRACT)

        # Fiducial recesses.
        for fid in spec.fiducials:
            _add_recess(spec, fid, Box, Cylinder, Locations, Mode, Axis)

    return part.part


def _add_recess(spec, fid, Box, Cylinder, Locations, Mode, Axis):
    """Carve one fiducial recess in-place (called inside a BuildPart context)."""
    H = spec.height_mm
    half = {
        "x": spec.length_mm / 2,
        "y": spec.width_mm / 2,
        "z": spec.height_mm / 2,
    }[fid.face[1]]
    sign = 1.0 if fid.face[0] == "+" else -1.0
    extra = spec.grasp.height_mm if spec.grasp.face == fid.face else 0.0
    surface = sign * (half + extra)
    pocket = fid.tag_size_mm + 2 * fid.quiet_zone_mm
    depth = fid.recess_depth_mm

    axis = fid.face[1]
    center = {"x": 0.0, "y": 0.0, "z": 0.0}
    center[axis] = surface - sign * depth / 2
    dims = {"x": pocket, "y": pocket, "z": pocket}
    dims[axis] = depth
    with Locations((center["x"], center["y"], center["z"])):
        Box(dims["x"], dims["y"], dims["z"], mode=Mode.SUBTRACT)


def export_cad(
    spec: CalibrationTargetSpec, step_path: str | Path, stl_path=None
) -> None:
    """Export the shell to STEP (and optionally STL)."""
    from build123d import export_step, export_stl

    solid = build_shell(spec)
    export_step(solid, str(step_path))
    if stl_path is not None:
        export_stl(solid, str(stl_path))

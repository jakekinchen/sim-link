"""Assemble a calibration target's plastic shell, frames, and socket layout.

The shell is expressed as *signed* primitives so its mass properties are exact
by superposition (outer solid, minus cavity, plus guide tubes and grasp rib,
minus fiducial recesses). The same primitive list drives the STL surface, so the
printed mesh and the physics model can never disagree.

This module owns only the geometry that is fixed once the shell is printed.
Interchangeable cartridge loadouts live in :mod:`configurations`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scenesmith.calibration import primitives as prim
from scenesmith.calibration.materials import get_coupon, get_material
from scenesmith.calibration.primitives import Axis, Primitive
from scenesmith.calibration.spec import MM, CalibrationTargetSpec

# Outward normal and in-plane (u -> tag x, v -> tag y) basis for each face.
# Chosen so that [u, v, normal] forms a right-handed frame.
_FACE_BASIS: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {
    "+z": (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])),
    "-z": (np.array([1.0, 0, 0]), np.array([0, -1.0, 0]), np.array([0, 0, -1.0])),
    "+x": (np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), np.array([1.0, 0, 0])),
    "-x": (np.array([0, -1.0, 0]), np.array([0, 0, 1.0]), np.array([-1.0, 0, 0])),
    "+y": (np.array([-1.0, 0, 0]), np.array([0, 0, 1.0]), np.array([0, 1.0, 0])),
    "-y": (np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), np.array([0, -1.0, 0])),
}


def _face_token(face: str) -> str:
    """Filesystem/XML-safe token for a face, e.g. '+z' -> 'pz', '-x' -> 'nx'."""
    return ("p" if face[0] == "+" else "n") + face[1]


def _face_axis_index(face: str) -> int:
    return {"x": 0, "y": 1, "z": 2}[face[1]]


def _face_sign(face: str) -> float:
    return 1.0 if face[0] == "+" else -1.0


@dataclass
class TargetGeometry:
    """Resolved geometry of a printed shell (all lengths in meters)."""

    spec: CalibrationTargetSpec
    shell_primitives: list[Primitive]
    coupon_primitives: list[Primitive]
    tag_frames: dict[str, dict]
    grasp_frame: np.ndarray
    socket_floor_z: float
    socket_axis: Axis
    socket_positions: dict[tuple[int, int], np.ndarray]

    def shell_solid_volume(self) -> float:
        """Net plastic volume of the bare shell (m**3), coupons excluded."""
        return sum(p.volume for p in self.shell_primitives)


def _face_mount_offset(spec: CalibrationTargetSpec, face: str) -> float:
    """Outward height (m) of the mounting surface, accounting for a grasp rib."""
    if spec.grasp.face == face:
        return spec.grasp.height_mm * MM
    return 0.0


def build_geometry(spec: CalibrationTargetSpec) -> TargetGeometry:
    """Resolve a spec into placed primitives, frames, and socket coordinates."""
    rho = spec.shell_density()
    L, W, H = (v * MM for v in (spec.length_mm, spec.width_mm, spec.height_mm))
    t = spec.wall_mm * MM
    ci_x, ci_y, ci_z = (v * MM for v in spec.cavity_extents_mm())

    shell: list[Primitive] = []
    # Hollow box = outer solid plastic minus the cavity (air, negative density).
    shell.append(prim.box((0, 0, 0), L, W, H, rho, "shell_outer"))
    shell.append(prim.box((0, 0, 0), ci_x, ci_y, ci_z, -rho, "shell_cavity"))

    # Grasp rib (positive plastic boss) on its face.
    g = spec.grasp
    if g.face == "+z":
        rib_center = (0.0, 0.0, H / 2 + g.height_mm * MM / 2)
        shell.append(
            prim.box(
                rib_center,
                g.length_mm * MM,
                g.width_mm * MM,
                g.height_mm * MM,
                rho,
                "grasp_rib",
            )
        )
    grasp_frame = _grasp_frame(spec, H)

    # Cartridge guide tubes: thin plastic annuli that locate the slugs.
    sg = spec.sockets
    r_bore = sg.bore_diameter_mm * MM / 2
    r_guide = r_bore + sg.guide_wall_mm * MM
    cavity_floor_z = -H / 2 + t
    floor_z = cavity_floor_z + sg.floor_clearance_mm * MM
    depth = sg.depth_mm * MM
    tube_center_z = floor_z + depth / 2
    socket_positions: dict[tuple[int, int], np.ndarray] = {}
    for i, j, x_mm, y_mm in sg.positions_mm():
        x, y = x_mm * MM, y_mm * MM
        socket_positions[(i, j)] = np.array([x, y, floor_z])
        shell.append(
            prim.tube(
                (x, y, tube_center_z),
                r_guide,
                r_bore,
                depth,
                Axis.Z,
                rho,
                f"guide_{i}{j}",
            )
        )

    # Fiducial recesses (negative plastic) and their frames.
    tag_frames: dict[str, dict] = {}
    for fid in spec.fiducials:
        frame, recess = _fiducial(spec, fid, (L, W, H), rho)
        shell.append(recess)
        tag_frames[fid.name] = frame

    # Replaceable friction coupons (own material, bonded to a face).
    coupons: list[Primitive] = []
    for mount in spec.coupons:
        coupons.append(_coupon(spec, mount, (L, W, H)))

    return TargetGeometry(
        spec=spec,
        shell_primitives=shell,
        coupon_primitives=coupons,
        tag_frames=tag_frames,
        grasp_frame=grasp_frame,
        socket_floor_z=floor_z,
        socket_axis=Axis.Z,
        socket_positions=socket_positions,
    )


def _grasp_frame(spec: CalibrationTargetSpec, H: float) -> np.ndarray:
    """Grasp frame: origin at the rib's grip line, +z is the approach axis."""
    g = spec.grasp
    frame = np.eye(4)
    # Approach from above: tool z points down (-body z); x stays along body +x.
    frame[:3, 0] = [1.0, 0.0, 0.0]
    frame[:3, 1] = [0.0, -1.0, 0.0]
    frame[:3, 2] = [0.0, 0.0, -1.0]
    frame[:3, 3] = [0.0, 0.0, H / 2 + g.height_mm * MM / 2]
    return frame


def _fiducial(spec, fid, outer, rho) -> tuple[dict, Primitive]:
    L, W, H = outer
    half = np.array([L, W, H]) / 2.0
    u, v, n = _FACE_BASIS[fid.face]
    axis = _face_axis_index(fid.face)
    sign = _face_sign(fid.face)

    # Outer mounting surface along the face normal (may sit on a grasp rib).
    surface = sign * half[axis] + sign * _face_mount_offset(spec, fid.face)
    center_on_face = np.zeros(3)
    center_on_face[axis] = surface

    # Tag frame: origin on the surface, z along outward normal.
    frame = np.eye(4)
    frame[:3, 0] = u
    frame[:3, 1] = v
    frame[:3, 2] = n
    frame[:3, 3] = center_on_face

    # Recess: a shallow negative box carved inward from the surface.
    pocket = (fid.tag_size_mm + 2 * fid.quiet_zone_mm) * MM
    depth = fid.recess_depth_mm * MM
    recess_center = center_on_face - n * (depth / 2)
    dims = [pocket, pocket, pocket]
    dims[axis] = depth
    recess = prim.box(
        tuple(recess_center), dims[0], dims[1], dims[2], -rho, f"recess_{fid.name}"
    )
    info = {
        "name": fid.name,
        "face": fid.face,
        "tag_id": fid.tag_id,
        "family": fid.family,
        "tag_size_mm": fid.tag_size_mm,
        "transform": frame,
    }
    return info, recess


def _coupon(spec, mount, outer) -> Primitive:
    L, W, H = outer
    half = np.array([L, W, H]) / 2.0
    coupon = get_coupon(mount.coupon)
    rho = get_material(coupon.material).density
    axis = _face_axis_index(mount.face)
    sign = _face_sign(mount.face)
    thick = coupon.thickness_mm * MM
    w, h = (s * MM for s in mount.size_mm)

    center = np.zeros(3)
    center[axis] = sign * (half[axis] + thick / 2)
    dims = [0.0, 0.0, 0.0]
    in_plane = [a for a in range(3) if a != axis]
    dims[in_plane[0]] = w
    dims[in_plane[1]] = h
    dims[axis] = thick
    # Label: "<coupon_key>_<facetoken>" (coupon_key already carries a 'coupon_'
    # prefix), single trailing token so the BOM can recover the coupon key.
    return prim.box(
        tuple(center),
        dims[0],
        dims[1],
        dims[2],
        rho,
        f"{mount.coupon}_{_face_token(mount.face)}",
    )

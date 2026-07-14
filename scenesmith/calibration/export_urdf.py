"""Export a resolved calibration target to URDF (Drake / ROS friendly).

The base link carries the exact analytic inertial. Fiducial and grasp frames are
emitted as massless links joined by fixed joints so downstream tools (Drake,
ROS/tf) can reference ``tag_top``, ``grasp``, etc. by name. Visual/collision use
primitive boxes and cylinders that mirror the physics model.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from xml.dom import minidom

import numpy as np

from scenesmith.calibration.configurations import ResolvedTarget
from scenesmith.calibration.frames import fmt, rotation_to_rpy
from scenesmith.calibration.mass_properties import inertia_to_sixtuple
from scenesmith.calibration.primitives import Primitive

_RGBA = {
    "plastic": "0.85 0.85 0.87 1",
    "steel": "0.30 0.32 0.36 1",
    "coupon": "0.20 0.55 0.85 1",
}


def _origin(elem: ET.Element, xyz, rpy=(0, 0, 0)) -> None:
    ET.SubElement(elem, "origin", xyz=fmt(xyz), rpy=fmt(rpy))


def _geometry(parent: ET.Element, primitive: Primitive) -> bool:
    p = primitive.params
    geom = ET.SubElement(parent, "geometry")
    if primitive.kind == "box":
        ET.SubElement(geom, "box", size=fmt([p["dx"], p["dy"], p["dz"]]))
    elif primitive.kind == "cylinder":
        ET.SubElement(
            geom, "cylinder", radius=f"{p['radius']:.8g}", length=f"{p['length']:.8g}"
        )
    elif primitive.kind == "sphere":
        ET.SubElement(geom, "sphere", radius=f"{p['radius']:.8g}")
    else:
        parent.remove(geom)
        return False
    return True


def build_urdf_tree(target: ResolvedTarget) -> ET.Element:
    """Build the URDF XML tree for a resolved target."""
    spec = target.spec
    mp = target.mass_properties
    robot_name = f"{spec.name}_{target.config.name}"
    robot = ET.Element("robot", name=robot_name)

    base = ET.SubElement(robot, "link", name="base")

    inertial = ET.SubElement(base, "inertial")
    _origin(inertial, mp.com)
    ET.SubElement(inertial, "mass", value=f"{mp.mass:.10g}")
    six = inertia_to_sixtuple(mp.inertia_com)
    ET.SubElement(
        inertial,
        "inertia",
        ixx=f"{six['ixx']:.10g}",
        iyy=f"{six['iyy']:.10g}",
        izz=f"{six['izz']:.10g}",
        ixy=f"{six['ixy']:.10g}",
        ixz=f"{six['ixz']:.10g}",
        iyz=f"{six['iyz']:.10g}",
    )

    for primitive in target.all_primitives:
        label = primitive.label
        if label.startswith(("shell_cavity", "recess_", "guide_", "void_")):
            continue
        color = (
            "steel"
            if label.startswith(("slug_", "ball_"))
            else ("coupon" if label.startswith("coupon_") else "plastic")
        )
        visual = ET.SubElement(base, "visual", name=f"vis_{label}")
        _origin(visual, primitive.center)
        if not _geometry(visual, primitive):
            base.remove(visual)
            continue
        mat = ET.SubElement(visual, "material", name=f"{label}_mat")
        ET.SubElement(mat, "color", rgba=_RGBA[color])
        # Collision: external solids only (skip internal slugs/balls/carriers).
        if not label.startswith(("slug_", "ball_", "carrier")):
            collision = ET.SubElement(base, "collision", name=f"col_{label}")
            _origin(collision, primitive.center)
            _geometry(collision, primitive)

    # Frames as massless fixed links.
    def add_frame(name: str, T: np.ndarray) -> None:
        link = ET.SubElement(robot, "link", name=name)
        # A tiny massless inertial keeps some URDF parsers happy.
        inertial = ET.SubElement(link, "inertial")
        ET.SubElement(inertial, "mass", value="0")
        ET.SubElement(
            inertial, "inertia", ixx="0", iyy="0", izz="0", ixy="0", ixz="0", iyz="0"
        )
        joint = ET.SubElement(robot, "joint", name=f"{name}_fixed", type="fixed")
        ET.SubElement(joint, "parent", link="base")
        ET.SubElement(joint, "child", link=name)
        ET.SubElement(
            joint, "origin", xyz=fmt(T[:3, 3]), rpy=fmt(rotation_to_rpy(T[:3, :3]))
        )

    for name, info in target.geometry.tag_frames.items():
        add_frame(f"tag_{name}", info["transform"])
    add_frame("grasp", target.geometry.grasp_frame)
    return robot


def to_urdf_string(target: ResolvedTarget) -> str:
    """Return a pretty-printed URDF XML string."""
    tree = build_urdf_tree(target)
    rough = ET.tostring(tree, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")

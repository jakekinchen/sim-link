"""Export a resolved calibration target to MuJoCo MJCF.

The emitted body carries an *explicit* ``<inertial>`` computed by exact
superposition, so the simulator twin holds the same ground-truth mass, center of
mass, and inertia as the physical brick -- MuJoCo does not re-derive them from
geoms. Geoms are primitive boxes/cylinders for fast, exact collision and visual;
each fiducial, the grasp line, and the center of mass are emitted as named
``<site>`` frames so perception and control can reference them directly.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from xml.dom import minidom

import numpy as np

from scenesmith.calibration.configurations import ResolvedTarget
from scenesmith.calibration.frames import fmt
from scenesmith.calibration.mass_properties import inertia_to_sixtuple
from scenesmith.calibration.primitives import Primitive

_MATERIAL_RGBA = {
    "plastic": "0.85 0.85 0.87 1",
    "steel": "0.30 0.32 0.36 1",
    "coupon": "0.20 0.55 0.85 1",
    "coupon2": "0.90 0.55 0.20 1",
}


def _geom_for(primitive: Primitive) -> dict | None:
    """Map a positive primitive to MJCF geom attributes, or None to skip."""
    label = primitive.label
    if label.startswith(("shell_cavity", "recess_", "guide_", "void_")):
        return None  # captured by the explicit inertial, not a solid geom
    p = primitive.params
    if primitive.kind == "box":
        attrs = {
            "type": "box",
            "size": fmt(np.array([p["dx"], p["dy"], p["dz"]]) / 2.0),
            "pos": fmt(primitive.center),
        }
    elif primitive.kind == "cylinder":
        attrs = {
            "type": "cylinder",
            "size": fmt([p["radius"], p["length"] / 2.0]),
            "pos": fmt(primitive.center),
        }
    elif primitive.kind == "sphere":
        attrs = {
            "type": "sphere",
            "size": fmt([p["radius"]]),
            "pos": fmt(primitive.center),
        }
    else:
        return None
    if label.startswith(("slug_", "ball_")):
        # Internal metal inserts: visual only, collisions handled by the shell.
        attrs.update(material="steel", group="2", contype="0", conaffinity="0")
    elif label.startswith("carrier"):
        attrs.update(material="plastic", group="2", contype="0", conaffinity="0")
    elif label.startswith(("shell_outer", "grasp_rib")):
        attrs.update(material="plastic", group="0")
    elif label.startswith("coupon_"):
        mat = (
            "coupon2"
            if primitive.center[0] > 1e-6 or primitive.center[1] > 1e-6
            else "coupon"
        )
        attrs.update(material=mat, group="0")
    attrs["name"] = label
    return attrs


def build_mjcf_tree(
    target: ResolvedTarget,
    include_scene: bool = False,
    freejoint: bool = False,
) -> ET.Element:
    """Build the MJCF XML tree for a resolved target."""
    spec = target.spec
    mp = target.mass_properties
    body_name = f"{spec.name}_{target.config.name}"

    mujoco = ET.Element("mujoco", model=body_name)
    ET.SubElement(mujoco, "compiler", angle="radian", autolimits="true")
    ET.SubElement(mujoco, "option", integrator="implicitfast")

    asset = ET.SubElement(mujoco, "asset")
    for name, rgba in _MATERIAL_RGBA.items():
        ET.SubElement(asset, "material", name=name, rgba=rgba)
    if include_scene:
        ET.SubElement(
            asset,
            "texture",
            type="skybox",
            builtin="gradient",
            rgb1="0.3 0.5 0.7",
            rgb2="0 0 0",
            width="32",
            height="32",
        )

    world = ET.SubElement(mujoco, "worldbody")
    if include_scene:
        ET.SubElement(world, "light", pos="0 0 1", dir="0 0 -1", diffuse="0.8 0.8 0.8")
        ET.SubElement(
            world,
            "geom",
            name="floor",
            type="plane",
            size="1 1 0.05",
            pos="0 0 0",
            rgba="0.4 0.4 0.4 1",
        )

    # Lift the body so its lowest point sits on z=0 when a scene is included.
    zoff = 0.0
    if include_scene:
        zoff = spec.height_mm * 1e-3 / 2.0 + 0.001
    body = ET.SubElement(world, "body", name=body_name, pos=fmt([0, 0, zoff]))
    if freejoint:
        ET.SubElement(body, "freejoint", name=f"{body_name}_free")

    six = inertia_to_sixtuple(mp.inertia_com)
    ET.SubElement(
        body,
        "inertial",
        pos=fmt(mp.com),
        mass=f"{mp.mass:.10g}",
        fullinertia=fmt(
            [six["ixx"], six["iyy"], six["izz"], six["ixy"], six["ixz"], six["iyz"]]
        ),
    )

    for primitive in target.all_primitives:
        attrs = _geom_for(primitive)
        if attrs is not None:
            ET.SubElement(body, "geom", **attrs)

    # Fiducial, grasp, and center-of-mass frames as named sites.
    for name, info in target.geometry.tag_frames.items():
        T = info["transform"]
        ET.SubElement(
            body,
            "site",
            name=f"tag_{name}",
            pos=fmt(T[:3, 3]),
            xyaxes=fmt(np.concatenate([T[:3, 0], T[:3, 1]])),
            size="0.002",
            rgba="1 0 0 1",
        )
    G = target.geometry.grasp_frame
    ET.SubElement(
        body,
        "site",
        name="grasp",
        pos=fmt(G[:3, 3]),
        xyaxes=fmt(np.concatenate([G[:3, 0], G[:3, 1]])),
        size="0.002",
        rgba="0 1 0 1",
    )
    ET.SubElement(
        body, "site", name="com", pos=fmt(mp.com), size="0.003", rgba="1 1 0 1"
    )
    return mujoco


def to_mjcf_string(
    target: ResolvedTarget, include_scene: bool = False, freejoint: bool = False
) -> str:
    """Return a pretty-printed MJCF XML string."""
    tree = build_mjcf_tree(target, include_scene=include_scene, freejoint=freejoint)
    rough = ET.tostring(tree, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")

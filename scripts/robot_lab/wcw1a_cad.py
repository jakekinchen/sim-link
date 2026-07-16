#!/usr/bin/env python3
"""Generate the WCW-1A printable solids and engineering renders in Blender.

Run through Blender, not CPython::

    blender --background --python scripts/robot_lab/wcw1a_cad.py -- \
        --output release/WCW-1A_print_package \
        --tag-dir release/WCW-1A_print_package/tags

The geometry uses millimetres directly and exports unit-scale STL meshes.  The
body is printed top-down as an open shell.  Each cartridge is printed on its
closed -x face so the ball wells are vertical, then closed by a separately
printed sliding spring retainer.  No ball is trapped during printing.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.wcw1a_spec import Wcw1aSpec  # noqa: E402


SPEC = Wcw1aSpec()
EPS = 0.02


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_transform(obj: bpy.types.Object) -> None:
    activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def box(
    name: str,
    dimensions: tuple[float, float, float],
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    apply_transform(obj)
    if bevel > 0.0:
        modifier = obj.modifiers.new(name="manufacturing_chamfer", type="BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.affect = "EDGES"
        activate(obj)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def cylinder(
    name: str,
    radius: float,
    depth: float,
    location: tuple[float, float, float],
    axis: str = "Z",
    vertices: int = 96,
) -> bpy.types.Object:
    rotation = {
        "X": (0.0, math.pi / 2.0, 0.0),
        "Y": (math.pi / 2.0, 0.0, 0.0),
        "Z": (0.0, 0.0, 0.0),
    }[axis]
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    apply_transform(obj)
    return obj


def sphere(
    name: str,
    radius: float,
    location: tuple[float, float, float],
    segments: int = 96,
    rings: int = 64,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        radius=radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    apply_transform(obj)
    return obj


def triangular_rib(
    name: str,
    x_length: float,
    y_center: float,
    y_width: float,
    z_base: float,
    z_peak: float,
) -> bpy.types.Object:
    x0, x1 = -x_length / 2.0, x_length / 2.0
    y0, y1, ym = y_center - y_width / 2.0, y_center + y_width / 2.0, y_center
    vertices = [
        (x0, y0, z_base),
        (x0, y1, z_base),
        (x0, ym, z_peak),
        (x1, y0, z_base),
        (x1, y1, z_base),
        (x1, ym, z_peak),
    ]
    faces = [
        (0, 3, 4, 1),
        (0, 2, 5, 3),
        (1, 4, 5, 2),
        (0, 1, 2),
        (3, 5, 4),
    ]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def conical_bore_cutter(
    name: str,
    apex_x: float,
    open_x: float,
    end_x: float,
    radius: float,
    y_center: float,
    z_center: float = 0.0,
    segments: int = 96,
) -> bpy.types.Object:
    """One manifold cutter containing a cone and constant-diameter bore."""
    vertices = [(apex_x, y_center, z_center)]
    for x_value in (open_x, end_x):
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            vertices.append(
                (
                    x_value,
                    y_center + radius * math.cos(angle),
                    z_center + radius * math.sin(angle),
                )
            )
    faces = []
    open_start = 1
    end_start = 1 + segments
    for index in range(segments):
        next_index = (index + 1) % segments
        faces.append((0, open_start + next_index, open_start + index))
        faces.append(
            (
                open_start + index,
                open_start + next_index,
                end_start + next_index,
                end_start + index,
            )
        )
    faces.append(tuple(end_start + index for index in range(segments)))
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=True)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def boolean(target: bpy.types.Object, tool: bpy.types.Object, operation: str) -> bpy.types.Object:
    modifier = target.modifiers.new(name=f"{operation.lower()}_{tool.name}", type="BOOLEAN")
    modifier.operation = operation
    modifier.solver = "EXACT"
    modifier.object = tool
    activate(target)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tool, do_unlink=True)
    return target


def union(target: bpy.types.Object, *parts: bpy.types.Object) -> bpy.types.Object:
    for part in parts:
        boolean(target, part, "UNION")
    return target


def difference(target: bpy.types.Object, *cutters: bpy.types.Object) -> bpy.types.Object:
    for cutter in cutters:
        boolean(target, cutter, "DIFFERENCE")
    return target


def clean_mesh(obj: bpy.types.Object) -> None:
    activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mesh = obj.data
    mesh.validate(verbose=False, clean_customdata=True)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def mesh_stats(obj: bpy.types.Object) -> dict:
    clean_mesh(obj)
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    boundary = sum(1 for edge in bm.edges if edge.is_boundary)
    volume = abs(bm.calc_volume(signed=True))
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    face_vertices = [frozenset(vertex.index for vertex in face.verts) for face in bm.faces]
    bvh = BVHTree.FromBMesh(bm, epsilon=1e-7)
    self_intersections = sum(
        1
        for first, second in bvh.overlap(bvh)
        if first < second and face_vertices[first].isdisjoint(face_vertices[second])
    )
    bm.free()
    world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    mins = [min(v[i] for v in world_corners) for i in range(3)]
    maxs = [max(v[i] for v in world_corners) for i in range(3)]
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "boundary_edges": boundary,
        "non_manifold_edges": non_manifold,
        "self_intersection_pairs": self_intersections,
        "watertight_manifold": boundary == 0 and non_manifold == 0 and self_intersections == 0,
        "bounds_min_mm": [round(v, 6) for v in mins],
        "bounds_max_mm": [round(v, 6) for v in maxs],
        "dimensions_mm": [round(maxs[i] - mins[i], 6) for i in range(3)],
        "volume_mm3": round(volume, 6),
    }


def export_stl(obj: bpy.types.Object, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean_mesh(obj)
    activate(obj)
    bpy.ops.wm.stl_export(
        filepath=str(path),
        export_selected_objects=True,
        apply_modifiers=True,
        ascii_format=False,
        global_scale=1.0,
    )
    return mesh_stats(obj)


def build_body() -> bpy.types.Object:
    spec = SPEC
    body = box(
        "WCW-1A_body",
        spec.body_dimensions_mm,
        bevel=spec.body_edge_chamfer_mm,
    )
    cavity_top = spec.body_z_mm / 2.0 - spec.body_roof_mm
    cavity_bottom = -spec.body_z_mm / 2.0 - 1.0
    cavity = box(
        "body_open_cavity",
        (spec.body_cavity_x_mm, spec.body_cavity_y_mm, cavity_top - cavity_bottom),
        (0.0, 0.0, (cavity_top + cavity_bottom) / 2.0),
    )
    difference(body, cavity)

    # Asymmetric -x/+y rail keys both the lid plug and every cartridge.
    key_rail = box(
        "body_key_rail",
        (2.2, 2.4, 30.8),
        (-16.7, 26.6, -17.1),
    )
    union(body, key_rail)

    # Four small ledges stop the cartridge at z=-1.7 without a large bridge.
    stop_parts: list[bpy.types.Object] = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            stop_parts.append(
                box(
                    f"carrier_stop_{sx}_{sy}",
                    (4.8, 4.8, 2.0),
                    (sx * 15.4, sy * 25.4, -0.7),
                )
            )
    union(body, *stop_parts)

    # Internal reliefs receive the lid's rounded detent beads.
    detent_cutters = [
        box("lid_detent_pocket_py", (10.0, 1.4, 2.2), (0.0, 27.5, -28.4)),
        box("lid_detent_pocket_ny", (10.0, 1.4, 2.2), (0.0, -27.5, -28.4)),
    ]
    difference(body, *detent_cutters)
    clean_mesh(body)
    return body


def build_lid() -> bpy.types.Object:
    spec = SPEC
    lid = box(
        "WCW-1A_bottom_lid",
        (spec.lid_flange_x_mm, spec.lid_flange_y_mm, spec.lid_flange_thickness_mm),
        (0.0, 0.0, 0.0),
        bevel=0.8,
    )
    plug_z = spec.lid_flange_thickness_mm / 2.0 + spec.lid_plug_height_mm / 2.0
    plug = box(
        "lid_keyed_plug",
        (spec.lid_plug_x_mm, spec.lid_plug_y_mm, spec.lid_plug_height_mm),
        (0.0, 0.0, plug_z),
        bevel=0.35,
    )
    union(lid, plug)
    key_notch = box(
        "lid_key_notch",
        (3.1, 3.2, 3.0),
        (-15.9, 25.9, plug_z + 0.2),
    )
    difference(lid, key_notch)

    bead_depth = 8.0
    bead_radius = 0.75
    beads = [
        cylinder("lid_detent_py", bead_radius, bead_depth, (0.0, 27.0, 2.65), axis="X"),
        cylinder("lid_detent_ny", bead_radius, bead_depth, (0.0, -27.0, 2.65), axis="X"),
    ]
    union(lid, *beads)

    plug_top = spec.lid_flange_thickness_mm / 2.0 + spec.lid_plug_height_mm
    ribs = [
        triangular_rib(f"lid_crush_rib_{index}", 24.0, y, 1.2, plug_top - EPS, 4.8)
        for index, y in enumerate((-15.0, 0.0, 15.0))
    ]
    union(lid, *ribs)
    clean_mesh(lid)
    return lid


def build_carrier(config_name: str, seats_y_mm: tuple[float, ...]) -> bpy.types.Object:
    spec = SPEC
    center_x = (spec.carrier_x_min_mm + spec.carrier_x_max_mm) / 2.0
    carrier = box(
        f"WCW-1A_{config_name}_carrier",
        (
            spec.carrier_x_max_mm - spec.carrier_x_min_mm,
            spec.carrier_y_mm,
            spec.carrier_z_mm,
        ),
        (center_x, 0.0, 0.0),
        bevel=0.8,
    )
    key_notch = box(
        f"{config_name}_key_notch",
        (3.0, 3.2, spec.carrier_z_mm + 1.0),
        (-15.7, 25.9, 0.0),
    )
    difference(carrier, key_notch)

    pocket_radius = spec.ball_pocket_diameter_mm / 2.0
    # A 45-degree cone tangent to the nominal 20 mm sphere at x=-r/sqrt(2)
    # self-centres the ball.  The cone opens into the 20.8 mm access bore and
    # grows at one millimetre of radius per millimetre of print height, avoiding
    # the near-horizontal underside of a spherical printed cavity.
    cone_apex_x = -math.sqrt(2.0) * (spec.ball_nominal_diameter_mm / 2.0)
    cone_open_x = cone_apex_x + pocket_radius
    for index, y_mm in enumerate(seats_y_mm):
        bore_end_x = spec.carrier_x_max_mm + 0.75
        cutter = conical_bore_cutter(
            f"{config_name}_conical_bore_{index}",
            cone_apex_x,
            cone_open_x,
            bore_end_x,
            pocket_radius,
            y_mm,
        )
        difference(carrier, cutter)

    # L-shaped rails capture a 1.6 mm retainer with 0.2 mm total slide gap.
    rail_parts: list[bpy.types.Object] = []
    for sy in (-1.0, 1.0):
        rail_parts.append(
            box(
                f"{config_name}_rail_spacer_{sy}",
                (2.7, 2.2, 25.0),
                (15.15, sy * 26.1, 0.0),
            )
        )
        rail_parts.append(
            box(
                f"{config_name}_rail_lip_{sy}",
                (0.7, 1.7, 25.0),
                (16.15, sy * 25.25, 0.0),
                bevel=0.15,
            )
        )
        rail_parts.append(
            box(
                f"{config_name}_rail_top_stop_{sy}",
                (2.5, 1.7, 0.65),
                (15.2, sy * 25.25, 12.15),
            )
        )
    union(carrier, *rail_parts)
    clean_mesh(carrier)
    return carrier


def build_retainer(config_name: str, seats_y_mm: tuple[float, ...], code_count: int) -> bpy.types.Object:
    spec = SPEC
    retainer = box(
        f"WCW-1A_{config_name}_ball_retainer",
        (spec.retainer_plate_thickness_mm, 49.6, 24.0),
        (14.9, 0.0, 0.0),
        bevel=0.25,
    )

    for index, y_mm in enumerate(seats_y_mm):
        # U-slot creates an 8 mm wide, 16 mm long cantilever tongue fixed at +z.
        slot_cutters = [
            box(
                f"{config_name}_tongue_left_{index}",
                (2.4, 0.7, 16.3),
                (14.9, y_mm - 4.2, 0.1),
            ),
            box(
                f"{config_name}_tongue_right_{index}",
                (2.4, 0.7, 16.3),
                (14.9, y_mm + 4.2, 0.1),
            ),
            box(
                f"{config_name}_tongue_end_{index}",
                (2.4, 8.8, 0.7),
                (14.9, y_mm, -8.05),
            ),
        ]
        difference(retainer, *slot_cutters)
        boss = cylinder(
            f"{config_name}_spring_boss_{index}",
            3.0,
            4.4,
            (12.0, y_mm, 0.0),
            axis="X",
        )
        union(retainer, boss)

    # One through-hole means C0, two means C1, ... five means C4.
    for index in range(code_count):
        code_hole = cylinder(
            f"{config_name}_identity_hole_{index}",
            1.0,
            2.4,
            (14.9, -22.0, -8.0 + index * 4.0),
            axis="X",
            vertices=64,
        )
        difference(retainer, code_hole)

    # Small rounded edge bead gives a removable 0.1 mm rail detent.
    detent = sphere(f"{config_name}_retainer_detent", 0.35, (14.9, 24.75, -10.0), segments=48, rings=32)
    union(retainer, detent)
    clean_mesh(retainer)
    return retainer


def add_engraved_text(target: bpy.types.Object, text: str, x: float, y: float) -> None:
    curve = bpy.data.curves.new(name=f"label_{text}", type="FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 3.3
    curve.extrude = 0.35
    obj = bpy.data.objects.new(f"label_{text}", curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, 1.72)
    activate(obj)
    bpy.ops.object.convert(target="MESH")
    difference(target, obj)


def build_fit_coupon() -> bpy.types.Object:
    coupon = box("WCW-1A_ball_fit_coupon", (90.0, 38.0, 4.0), bevel=1.2)
    centers = (-30.0, 0.0, 30.0)
    for center_x, diameter in zip(centers, SPEC.fit_coupon_pocket_diameters_mm):
        hole = cylinder(
            f"coupon_pocket_{diameter:.1f}",
            diameter / 2.0,
            5.0,
            (center_x, 3.0, 0.0),
            axis="Z",
        )
        difference(coupon, hole)
        add_engraved_text(coupon, f"{diameter:.1f}", center_x, -15.0)
    clean_mesh(coupon)
    return coupon


def material(name: str, color: tuple[float, float, float, float], metallic: float = 0.0, roughness: float = 0.55) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def image_material(name: str, image_path: Path) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    image = nodes.new("ShaderNodeTexImage")
    image.image = bpy.data.images.load(str(image_path), check_existing=True)
    image.interpolation = "Closest"
    links.new(image.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = 0.65
    return mat


def textured_quad(
    name: str,
    center: Vector,
    right: Vector,
    up: Vector,
    size: float,
    image_path: Path,
) -> bpy.types.Object:
    half = size / 2.0
    corners = [
        center - right * half - up * half,
        center + right * half - up * half,
        center + right * half + up * half,
        center - right * half + up * half,
    ]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata([tuple(v) for v in corners], [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_coords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for loop, uv in zip(mesh.polygons[0].loop_indices, uv_coords):
        uv_layer.data[loop].uv = uv
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(image_material(f"{name}_mat", image_path))
    return obj


def add_tag_planes(tag_dir: Path) -> list[bpy.types.Object]:
    planes: list[bpy.types.Object] = []
    for tag in SPEC.tags:
        image_path = tag_dir / f"WCW-1A_tag36h11_ID{tag.tag_id}_{int(tag.full_label_mm)}mm.png"
        if not image_path.exists():
            continue
        if tag.face == "+z":
            center, right, up = Vector((0, 0, 32.53)), Vector((1, 0, 0)), Vector((0, 1, 0))
        elif tag.face == "+y":
            center, right, up = Vector((0, 30.03, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1))
        elif tag.face == "-y":
            center, right, up = Vector((0, -30.03, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))
        elif tag.face == "+x":
            center, right, up = Vector((20.03, 0, tag.center_z_mm)), Vector((0, 1, 0)), Vector((0, 0, 1))
        else:
            center, right, up = Vector((-20.03, 0, tag.center_z_mm)), Vector((0, -1, 0)), Vector((0, 0, 1))
        planes.append(textured_quad(f"tag_{tag.tag_id}_{tag.face}", center, right, up, tag.full_label_mm, image_path))
    return planes


def duplicate_object(obj: bpy.types.Object, name: str) -> bpy.types.Object:
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()
    duplicate.name = name
    bpy.context.collection.objects.link(duplicate)
    return duplicate


def hide_all(objects: list[bpy.types.Object]) -> None:
    for obj in objects:
        obj.hide_render = True


def show(obj: bpy.types.Object, location: tuple[float, float, float] | None = None) -> None:
    obj.hide_render = False
    if location is not None:
        obj.location = location


def look_at(camera: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_render(output_path: Path, camera_location: tuple[float, float, float], target: tuple[float, float, float], orthographic_scale: float | None = None) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_path)
    scene.render.film_transparent = False
    scene.world.color = (0.12, 0.14, 0.18)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 1.35

    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.object
    camera.data.lens = 58
    if orthographic_scale is not None:
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = orthographic_scale
    look_at(camera, target)
    scene.camera = camera

    for location, energy, size in [
        ((80, -90, 130), 2600, 70),
        ((-100, -40, 60), 1800, 55),
        ((20, 120, 90), 2100, 60),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, target)


def render_scene(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def clear_cameras_and_lights() -> None:
    for obj in list(bpy.data.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)


def assign_mat(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def build_renders(
    output_dir: Path,
    body: bpy.types.Object,
    lid: bpy.types.Object,
    carriers: dict[str, bpy.types.Object],
    retainers: dict[str, bpy.types.Object],
    tag_dir: Path,
) -> None:
    renders = output_dir / "renders"
    all_geom = [body, lid, *carriers.values(), *retainers.values()]
    white = material("matte_white_pla", (0.82, 0.84, 0.86, 1.0), roughness=0.72)
    gray = material("lid_gray_pla", (0.25, 0.28, 0.32, 1.0), roughness=0.7)
    blue = material("carrier_blue_pla", (0.08, 0.28, 0.52, 1.0), roughness=0.66)
    orange = material("retainer_orange_pla", (0.72, 0.24, 0.06, 1.0), roughness=0.68)
    steel = material("bearing_steel", (0.68, 0.72, 0.78, 1.0), metallic=0.82, roughness=0.18)
    assign_mat(body, white)
    assign_mat(lid, gray)
    for obj in carriers.values():
        assign_mat(obj, blue)
    for obj in retainers.values():
        assign_mat(obj, orange)

    # Assembled exterior with all five unique tag labels visible across views.
    hide_all(all_geom)
    show(body, (0.0, 0.0, 0.0))
    show(lid, (0.0, 0.0, SPEC.lid_assembly_z_mm))
    tag_planes = add_tag_planes(tag_dir)
    setup_render(renders / "WCW-1A_assembled.png", (115, -145, 110), (0, 0, 0))
    render_scene(renders / "WCW-1A_assembled.png")
    clear_cameras_and_lights()

    # Exploded C4 stack: body, carrier, spring retainer, balls, lid.
    for plane in tag_planes:
        plane.hide_render = True
    hide_all(all_geom)
    show(body, (0.0, 0.0, 45.0))
    show(carriers["C4"], (0.0, 0.0, -10.0))
    show(retainers["C4"], (35.0, 0.0, -10.0))
    show(lid, (0.0, 0.0, -55.0))
    render_balls: list[bpy.types.Object] = []
    for index, y_mm in enumerate(SPEC.configuration_seats_y_mm["C4"]):
        ball = sphere(f"exploded_ball_{index}", SPEC.ball_nominal_diameter_mm / 2.0, (-35.0, y_mm, -10.0), segments=64, rings=48)
        assign_mat(ball, steel)
        render_balls.append(ball)
    setup_render(renders / "WCW-1A_exploded.png", (150, -190, 115), (0, 0, -3))
    render_scene(renders / "WCW-1A_exploded.png")
    clear_cameras_and_lights()

    # All cartridges, retainers offset forward, and their installed balls.
    hide_all(all_geom + render_balls)
    cartridge_balls: list[bpy.types.Object] = []
    x_positions = (-120.0, -60.0, 0.0, 60.0, 120.0)
    for x_pos, name in zip(x_positions, ("C0", "C1", "C2", "C3", "C4")):
        carrier = carriers[name]
        retainer = retainers[name]
        carrier.rotation_euler.z = -math.pi / 2.0
        retainer.rotation_euler.z = -math.pi / 2.0
        show(carrier, (x_pos, 0.0, 0.0))
        show(retainer, (x_pos, -38.0, 0.0))
        for index, y_mm in enumerate(SPEC.configuration_seats_y_mm[name]):
            ball = sphere(f"{name}_display_ball_{index}", 10.0, (x_pos + y_mm, 0.0, 0.0), segments=48, rings=32)
            assign_mat(ball, steel)
            cartridge_balls.append(ball)
    setup_render(renders / "WCW-1A_all_cartridges.png", (0, -320, 110), (0, -8, 0), orthographic_scale=310)
    render_scene(renders / "WCW-1A_all_cartridges.png")
    clear_cameras_and_lights()

    # Section cut through y=0 shows the body, C1 spherical seat, ball, spring
    # boss, key rail, bottom lid, and crush ribs.
    hide_all(all_geom + render_balls + cartridge_balls)
    section_body = duplicate_object(body, "section_body")
    section_carrier = duplicate_object(carriers["C1"], "section_carrier")
    section_retainer = duplicate_object(retainers["C1"], "section_retainer")
    for obj, z_shift in ((section_body, 0.0), (section_carrier, SPEC.cartridge_assembly_z_mm), (section_retainer, SPEC.cartridge_assembly_z_mm)):
        obj.location = (0.0, 0.0, z_shift)
        obj.rotation_euler = (0.0, 0.0, 0.0)
        cutter = box(f"{obj.name}_halfspace", (200, 200, 200), (0, 100.05, 0))
        cutter.location.z -= z_shift
        difference(obj, cutter)
        obj.hide_render = False
    section_lid = duplicate_object(lid, "section_lid")
    section_lid.location = (0.0, 0.0, SPEC.lid_assembly_z_mm)
    cutter = box("section_lid_halfspace", (200, 200, 200), (0, 100.05, -SPEC.lid_assembly_z_mm))
    difference(section_lid, cutter)
    section_lid.hide_render = False
    section_ball = sphere("section_ball", 10.0, (0.0, 0.0, SPEC.cartridge_assembly_z_mm), segments=64, rings=48)
    assign_mat(section_ball, steel)
    assign_mat(section_body, white)
    assign_mat(section_lid, gray)
    assign_mat(section_carrier, blue)
    assign_mat(section_retainer, orange)
    setup_render(renders / "WCW-1A_ball_retention_section.png", (120, 165, 45), (0, 0, -8))
    render_scene(renders / "WCW-1A_ball_retention_section.png")
    clear_cameras_and_lights()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tag-dir", type=Path, required=True)
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    if SPEC.validate():
        raise RuntimeError(f"invalid WCW-1A spec: {SPEC.validate()}")
    reset_scene()
    stl_dir = args.output / "stl"
    validation_dir = args.output / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)

    body = build_body()
    lid = build_lid()
    carriers: dict[str, bpy.types.Object] = {}
    retainers: dict[str, bpy.types.Object] = {}
    build_stats: dict[str, dict] = {}

    build_stats["stl/WCW-1A_R1_body_top-down.stl"] = export_stl(
        body, stl_dir / "WCW-1A_R1_body_top-down.stl"
    )
    build_stats["stl/WCW-1A_R1_bottom-lid_outer-face-down.stl"] = export_stl(
        lid, stl_dir / "WCW-1A_R1_bottom-lid_outer-face-down.stl"
    )

    for config_index, (name, seats) in enumerate(SPEC.configuration_seats_y_mm.items()):
        carrier = build_carrier(name, seats)
        retainer = build_retainer(name, seats, config_index + 1)
        carriers[name] = carrier
        retainers[name] = retainer
        carrier_name = f"stl/WCW-1A_R1_{name}_carrier_print-minus-x-face-down.stl"
        retainer_name = f"stl/WCW-1A_R1_{name}_ball-retainer_exterior-face-down.stl"
        build_stats[carrier_name] = export_stl(carrier, args.output / carrier_name)
        build_stats[retainer_name] = export_stl(retainer, args.output / retainer_name)

    coupon = build_fit_coupon()
    coupon_name = "stl/WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl"
    build_stats[coupon_name] = export_stl(coupon, args.output / coupon_name)
    coupon.hide_render = True

    build_renders(args.output, body, lid, carriers, retainers, args.tag_dir)

    payload = {
        "schema_version": "scenesmith.wcw1a_blender_build.v1",
        "spec_identity_sha256": SPEC.identity_sha256(),
        "units": "mm",
        "blender_version": bpy.app.version_string,
        "meshes": build_stats,
    }
    (validation_dir / "BLENDER_BUILD_VALIDATION.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

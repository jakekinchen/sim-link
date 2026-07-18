#!/usr/bin/env python3
"""Blender renderer for SO-101 gripper release inspection images."""

from __future__ import annotations

import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def reset() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name: str, color: tuple[float, float, float, float]):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = color
    value.roughness = 0.62
    return value


def import_and_split(path: Path, color) -> list:
    bpy.ops.wm.stl_import(filepath=str(path))
    obj = bpy.context.active_object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    objects = list(bpy.context.selected_objects)
    for value in objects:
        value.data.materials.clear()
        value.data.materials.append(color)
    return objects


def bounds(objects: list) -> tuple[Vector, Vector]:
    minimum = Vector((math.inf, math.inf, math.inf))
    maximum = Vector((-math.inf, -math.inf, -math.inf))
    for obj in objects:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            for axis in range(3):
                minimum[axis] = min(minimum[axis], point[axis])
                maximum[axis] = max(maximum[axis], point[axis])
    return minimum, maximum


def add_bed() -> object:
    bpy.ops.mesh.primitive_cube_add(location=(110, 110, -1.25), scale=(110, 110, 1.0))
    bed = bpy.context.active_object
    bed.name = "AD5X 220mm build plate"
    bed.data.materials.append(material("Bed", (0.68, 0.71, 0.76, 1.0)))
    return bed


def add_lights(center: Vector, extent: float) -> None:
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.82, 0.84, 0.88)
    for location, energy in (
        (center + Vector((0.7, -0.8, 1.8)) * extent, 1100),
        (center + Vector((-1.4, 0.4, 1.0)) * extent, 650),
    ):
        light_data = bpy.data.lights.new("Area", "AREA")
        light_data.energy = energy
        light_data.size = extent
        light = bpy.data.objects.new("Area", light_data)
        bpy.context.collection.objects.link(light)
        light.location = location


def render(objects: list, output: Path, top: bool) -> None:
    minimum, maximum = bounds(objects)
    center = (minimum + maximum) / 2
    extent = max(maximum - minimum)
    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    if top:
        camera.location = Vector((110, 110, 330))
        camera.rotation_euler = (0, 0, 0)
        camera.rotation_euler = (Vector((110, 110, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = 242
    else:
        camera.location = center + Vector((1.45, -1.7, 1.2)) * extent
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = extent * 1.45
    add_lights(center, max(extent, 40))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "rim.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.background_type = "WORLD"
    scene.display.shading.show_shadows = not top
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)


def plate(release: Path, stl_name: str, output_name: str, mat_name: str, color) -> None:
    reset()
    objects = import_and_split(release / "fallback_stl" / stl_name, material(mat_name, color))
    bed = add_bed()
    render(objects + [bed], release / "renders" / output_name, top=True)


def overview(release: Path) -> None:
    reset()
    objects = import_and_split(
        release / "source/upstream/SO101_soft_fin_upstream.stl",
        material("Temporary", (0.7, 0.7, 0.7, 1.0)),
    )
    for obj in objects:
        faces = len(obj.data.polygons)
        obj.data.materials.clear()
        if faces == 3480:
            obj.data.materials.append(material("TPU 95A", (0.08, 0.36, 0.88, 1.0)))
        elif faces in (39690, 18714):
            obj.data.materials.append(material("PLA bases", (0.55, 0.60, 0.68, 1.0)))
        else:
            raise RuntimeError(f"unexpected separated render face count: {faces}")
    render(objects, release / "renders/SO101_R1_components_overview.png", top=False)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 1:
        raise SystemExit("usage: blender --background --python render_so101_gripper_release.py -- RELEASE_DIR")
    release = Path(args[0]).resolve()
    plate(
        release,
        "SO101_R1_AD5X_plate01_PLA_gripper-bases_batch.stl",
        "SO101_R1_AD5X_plate01_PLA_layout.png",
        "PLA bases",
        (0.55, 0.60, 0.68, 1.0),
    )
    plate(
        release,
        "SO101_R1_AD5X_plate02_TPU95A_soft-fin_batch.stl",
        "SO101_R1_AD5X_plate02_TPU95A_layout.png",
        "TPU 95A",
        (0.08, 0.36, 0.88, 1.0),
    )
    overview(release)


if __name__ == "__main__":
    main()

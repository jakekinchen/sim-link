"""Generate and verify arranged WCW-1A standard-3MF print plates.

The individual STL files remain the geometry source of truth.  This module
rotates each mesh into its documented support-free print orientation, normalizes
it to z=0, and writes independent named mesh objects plus build translations to
a standard unit-millimetre 3MF package.  No slicer or printer profile is
embedded; Bambu Studio should be set to the actual printer before slicing.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Iterable
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageDraw, ImageFont


CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
MODEL_RELATIONSHIP = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
XML_NS = "http://www.w3.org/XML/1998/namespace"


@dataclass(frozen=True)
class Part:
    key: str
    label: str
    stl_name: str
    orientation: str


@dataclass(frozen=True)
class Placement:
    part_key: str
    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class Plate:
    key: str
    filename: str
    title: str
    bed_x_mm: float
    bed_y_mm: float
    minimum_edge_margin_mm: float
    minimum_spacing_mm: float
    placements: tuple[Placement, ...]
    route: str
    job_number: int


def _part(key: str, label: str, stl_name: str, orientation: str) -> Part:
    return Part(key, label, stl_name, orientation)


PARTS: dict[str, Part] = {
    "body": _part("body", "Body", "WCW-1A_R1_body_top-down.stl", "top_face_down"),
    "lid": _part("lid", "Bottom lid", "WCW-1A_R1_bottom-lid_outer-face-down.stl", "minus_z_face_down"),
    "coupon": _part("coupon", "Ball-fit coupon", "WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl", "minus_z_face_down"),
}
for _config in ("C0", "C1", "C2", "C3", "C4"):
    PARTS[f"{_config}_carrier"] = _part(
        f"{_config}_carrier",
        f"{_config} carrier",
        f"WCW-1A_R1_{_config}_carrier_print-minus-x-face-down.stl",
        "minus_x_face_down",
    )
    PARTS[f"{_config}_retainer"] = _part(
        f"{_config}_retainer",
        f"{_config} retainer",
        f"WCW-1A_R1_{_config}_ball-retainer_exterior-face-down.stl",
        "plus_x_face_down",
    )


PRODUCTION_PART_KEYS = (
    "body",
    "lid",
    "C0_carrier",
    "C0_retainer",
    "C1_carrier",
    "C1_retainer",
    "C2_carrier",
    "C2_retainer",
    "C3_carrier",
    "C3_retainer",
    "C4_carrier",
    "C4_retainer",
)


PLATES: tuple[Plate, ...] = (
    Plate(
        key="universal_coupon",
        filename="WCW-1A_R1_Bambu_plate00_fit-coupon_fits180mm.3mf",
        title="WCW-1A fit coupon - fits 180 mm and larger plates",
        bed_x_mm=180.0,
        bed_y_mm=180.0,
        minimum_edge_margin_mm=8.0,
        minimum_spacing_mm=6.0,
        placements=(Placement("coupon", 45.0, 71.0),),
        route="universal_preflight",
        job_number=0,
    ),
    Plate(
        key="bambu_256_full_kit",
        filename="WCW-1A_R1_Bambu_256mm_plate01_full-production-kit.3mf",
        title="WCW-1A complete 12-part production kit - 256 mm plate",
        bed_x_mm=256.0,
        bed_y_mm=256.0,
        minimum_edge_margin_mm=10.0,
        minimum_spacing_mm=10.0,
        placements=(
            Placement("body", 10.0, 10.0),
            Placement("lid", 60.0, 10.0),
            Placement("C0_carrier", 109.4, 10.0),
            Placement("C0_retainer", 45.0, 80.0),
            Placement("C1_carrier", 144.4, 10.0),
            Placement("C1_retainer", 79.0, 80.0),
            Placement("C2_carrier", 179.4, 10.0),
            Placement("C2_retainer", 113.0, 80.0),
            Placement("C3_carrier", 214.4, 10.0),
            Placement("C3_retainer", 147.0, 80.0),
            Placement("C4_carrier", 10.0, 80.0),
            Placement("C4_retainer", 181.0, 80.0),
        ),
        route="primary_256mm",
        job_number=1,
    ),
    Plate(
        key="bambu_180_c1_fit",
        filename="WCW-1A_R1_Bambu_180mm_plate01_C1-fit-check.3mf",
        title="WCW-1A C1 carrier and retainer fit check - 180 mm plate",
        bed_x_mm=180.0,
        bed_y_mm=180.0,
        minimum_edge_margin_mm=8.0,
        minimum_spacing_mm=6.0,
        placements=(
            Placement("C1_carrier", 57.0, 62.8),
            Placement("C1_retainer", 98.0, 65.05),
        ),
        route="fallback_180mm",
        job_number=1,
    ),
    Plate(
        key="bambu_180_remaining",
        filename="WCW-1A_R1_Bambu_180mm_plate02_remaining-hardware.3mf",
        title="WCW-1A remaining carriers, retainers, and lid - 180 mm plate",
        bed_x_mm=180.0,
        bed_y_mm=180.0,
        minimum_edge_margin_mm=8.0,
        minimum_spacing_mm=6.0,
        placements=(
            Placement("C0_carrier", 8.0, 10.0),
            Placement("C2_carrier", 39.0, 10.0),
            Placement("C3_carrier", 70.0, 10.0),
            Placement("C4_carrier", 101.0, 10.0),
            Placement("lid", 132.0, 8.0),
            Placement("C0_retainer", 8.0, 74.0),
            Placement("C2_retainer", 38.0, 74.0),
            Placement("C3_retainer", 68.0, 74.0),
            Placement("C4_retainer", 98.0, 74.0),
        ),
        route="fallback_180mm",
        job_number=2,
    ),
    Plate(
        key="bambu_180_body",
        filename="WCW-1A_R1_Bambu_180mm_plate03_body.3mf",
        title="WCW-1A body - 180 mm plate",
        bed_x_mm=180.0,
        bed_y_mm=180.0,
        minimum_edge_margin_mm=8.0,
        minimum_spacing_mm=6.0,
        placements=(Placement("body", 70.0, 60.0),),
        route="fallback_180mm",
        job_number=3,
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_binary_stl(path: Path) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"short STL: {path}")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + triangle_count * 50:
        raise RuntimeError(f"invalid binary STL length: {path}")
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    vertex_map: dict[tuple[int, int, int], int] = {}
    for triangle in range(triangle_count):
        values = struct.unpack_from("<12fH", data, 84 + triangle * 50)
        face = []
        for offset in (3, 6, 9):
            point = tuple(float(value) for value in values[offset : offset + 3])
            if not all(math.isfinite(value) for value in point):
                raise RuntimeError(f"non-finite STL vertex: {path}")
            key = tuple(int(round(value * 100000.0)) for value in point)
            index = vertex_map.get(key)
            if index is None:
                index = len(vertices)
                vertex_map[key] = index
                vertices.append(point)
            face.append(index)
        if len(set(face)) != 3:
            raise RuntimeError(f"degenerate STL triangle: {path}")
        faces.append(tuple(face))
    return vertices, faces


def orient_point(point: tuple[float, float, float], orientation: str) -> tuple[float, float, float]:
    x, y, z = point
    if orientation == "minus_z_face_down":
        return x, y, z
    if orientation == "top_face_down":
        return x, -y, -z
    if orientation == "minus_x_face_down":
        return -z, y, x
    if orientation == "plus_x_face_down":
        return z, y, -x
    raise ValueError(f"unknown orientation: {orientation}")


def oriented_mesh(path: Path, orientation: str) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]], tuple[float, float, float]]:
    source_vertices, faces = read_binary_stl(path)
    transformed = [orient_point(point, orientation) for point in source_vertices]
    mins = tuple(min(point[axis] for point in transformed) for axis in range(3))
    normalized = [tuple(point[axis] - mins[axis] for axis in range(3)) for point in transformed]
    maxs = tuple(max(point[axis] for point in normalized) for axis in range(3))
    if min(point[2] for point in normalized) < -1e-7:
        raise RuntimeError(f"orientation failed to place {path.name} at z=0")
    return normalized, faces, maxs


def _float(value: float) -> str:
    rounded = 0.0 if abs(value) < 5e-10 else value
    return f"{rounded:.6f}".rstrip("0").rstrip(".") or "0"


def _content_types_xml() -> bytes:
    root = ET.Element(f"{{{CONTENT_TYPES_NS}}}Types")
    ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Default", Extension="rels", ContentType="application/vnd.openxmlformats-package.relationships+xml")
    ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Default", Extension="model", ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml")
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _relationships_xml() -> bytes:
    root = ET.Element(f"{{{RELATIONSHIPS_NS}}}Relationships")
    ET.SubElement(root, f"{{{RELATIONSHIPS_NS}}}Relationship", Target="/3D/3dmodel.model", Id="rel-1", Type=MODEL_RELATIONSHIP)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _model_xml(plate: Plate, meshes: dict[str, tuple[list[tuple[float, float, float]], list[tuple[int, int, int]], tuple[float, float, float]]]) -> bytes:
    ET.register_namespace("", CORE_NS)
    root = ET.Element(f"{{{CORE_NS}}}model", {"unit": "millimeter", f"{{{XML_NS}}}lang": "en-US"})
    for name, value in (
        ("Title", plate.title),
        ("Designer", "SceneSmith WCW-1A release generator"),
        ("Description", f"Arranged standard 3MF; declared bed {plate.bed_x_mm:.0f} x {plate.bed_y_mm:.0f} mm. Select the actual printer profile before slicing."),
    ):
        element = ET.SubElement(root, f"{{{CORE_NS}}}metadata", name=name)
        element.text = value
    resources = ET.SubElement(root, f"{{{CORE_NS}}}resources")
    build = ET.SubElement(root, f"{{{CORE_NS}}}build")
    for object_id, placement in enumerate(plate.placements, start=1):
        part = PARTS[placement.part_key]
        vertices, faces, _ = meshes[part.key]
        obj = ET.SubElement(resources, f"{{{CORE_NS}}}object", id=str(object_id), name=part.label, type="model")
        mesh = ET.SubElement(obj, f"{{{CORE_NS}}}mesh")
        xml_vertices = ET.SubElement(mesh, f"{{{CORE_NS}}}vertices")
        for x, y, z in vertices:
            ET.SubElement(xml_vertices, f"{{{CORE_NS}}}vertex", x=_float(x), y=_float(y), z=_float(z))
        xml_triangles = ET.SubElement(mesh, f"{{{CORE_NS}}}triangles")
        for v1, v2, v3 in faces:
            ET.SubElement(xml_triangles, f"{{{CORE_NS}}}triangle", v1=str(v1), v2=str(v2), v3=str(v3))
        transform = f"1 0 0 0 1 0 0 0 1 {_float(placement.x_mm)} {_float(placement.y_mm)} 0"
        ET.SubElement(build, f"{{{CORE_NS}}}item", objectid=str(object_id), transform=transform, partnumber=part.key)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_3mf(stl_dir: Path, plate: Plate, output: Path) -> None:
    meshes = {
        key: oriented_mesh(stl_dir / PARTS[key].stl_name, PARTS[key].orientation)
        for key in {placement.part_key for placement in plate.placements}
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _relationships_xml())
        archive.writestr("3D/3dmodel.model", _model_xml(plate, meshes))


def _bounds(vertices: Iterable[tuple[float, float, float]]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    points = list(vertices)
    return (
        tuple(min(point[axis] for point in points) for axis in range(3)),
        tuple(max(point[axis] for point in points) for axis in range(3)),
    )


def _rectangle_spacing(left: dict, right: dict) -> float:
    gap_x = max(left["min_x"] - right["max_x"], right["min_x"] - left["max_x"], 0.0)
    gap_y = max(left["min_y"] - right["max_y"], right["min_y"] - left["max_y"], 0.0)
    return math.hypot(gap_x, gap_y)


def validate_3mf(path: Path, plate: Plate, stl_dir: Path) -> dict:
    with zipfile.ZipFile(path, "r") as archive:
        names = sorted(archive.namelist())
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"3MF CRC failure in {path.name}: {bad}")
        expected_entries = ["3D/3dmodel.model", "[Content_Types].xml", "_rels/.rels"]
        if names != expected_entries:
            raise RuntimeError(f"unexpected 3MF package entries in {path.name}: {names}")
        content_types = ET.fromstring(archive.read("[Content_Types].xml"))
        relationships = ET.fromstring(archive.read("_rels/.rels"))
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    if content_types.tag != f"{{{CONTENT_TYPES_NS}}}Types":
        raise RuntimeError(f"invalid OPC content types root: {path}")
    relationship = relationships.find(f"{{{RELATIONSHIPS_NS}}}Relationship")
    if relationship is None or relationship.attrib.get("Type") != MODEL_RELATIONSHIP:
        raise RuntimeError(f"missing 3MF model relationship: {path}")
    if model.attrib.get("unit") != "millimeter":
        raise RuntimeError(f"3MF units drifted: {path}")

    objects = {element.attrib["id"]: element for element in model.findall(f".//{{{CORE_NS}}}object")}
    build_items = model.findall(f".//{{{CORE_NS}}}build/{{{CORE_NS}}}item")
    if len(objects) != len(plate.placements) or len(build_items) != len(plate.placements):
        raise RuntimeError(f"3MF part count drift: {path}")

    records = []
    for placement, item in zip(plate.placements, build_items):
        part = PARTS[placement.part_key]
        obj = objects[item.attrib["objectid"]]
        if obj.attrib.get("name") != part.label or item.attrib.get("partnumber") != part.key:
            raise RuntimeError(f"3MF object identity drift: {path} {part.key}")
        transform = [float(value) for value in item.attrib.get("transform", "").split()]
        if len(transform) != 12 or transform[:9] != [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]:
            raise RuntimeError(f"unexpected build transform: {path} {part.key}")
        if abs(transform[9] - placement.x_mm) > 1e-6 or abs(transform[10] - placement.y_mm) > 1e-6 or abs(transform[11]) > 1e-6:
            raise RuntimeError(f"build translation drift: {path} {part.key}")
        vertices = [
            (float(vertex.attrib["x"]), float(vertex.attrib["y"]), float(vertex.attrib["z"]))
            for vertex in obj.findall(f".//{{{CORE_NS}}}vertex")
        ]
        if not vertices or not all(math.isfinite(value) for vertex in vertices for value in vertex):
            raise RuntimeError(f"non-finite/empty 3MF mesh: {path} {part.key}")
        triangles = obj.findall(f".//{{{CORE_NS}}}triangle")
        for triangle in triangles:
            indices = [int(triangle.attrib[key]) for key in ("v1", "v2", "v3")]
            if len(set(indices)) != 3 or min(indices) < 0 or max(indices) >= len(vertices):
                raise RuntimeError(f"invalid 3MF triangle: {path} {part.key}")
        local_min, local_max = _bounds(vertices)
        source_vertices, source_faces, expected_dimensions = oriented_mesh(stl_dir / part.stl_name, part.orientation)
        if len(vertices) != len(source_vertices) or len(triangles) != len(source_faces):
            raise RuntimeError(f"3MF/source mesh count drift: {path} {part.key}")
        dimensions = tuple(local_max[axis] - local_min[axis] for axis in range(3))
        if any(abs(dimensions[axis] - expected_dimensions[axis]) > 2e-5 for axis in range(3)):
            raise RuntimeError(f"3MF/source bounds drift: {path} {part.key}")
        min_x = placement.x_mm + local_min[0]
        min_y = placement.y_mm + local_min[1]
        min_z = local_min[2]
        max_x = placement.x_mm + local_max[0]
        max_y = placement.y_mm + local_max[1]
        max_z = local_max[2]
        if abs(min_z) > 1e-6 or min_x < -1e-6 or min_y < -1e-6 or max_x > plate.bed_x_mm + 1e-6 or max_y > plate.bed_y_mm + 1e-6:
            raise RuntimeError(f"3MF object outside bed or above z=0: {path} {part.key}")
        records.append(
            {
                "part_key": part.key,
                "label": part.label,
                "source_stl": f"stl/{part.stl_name}",
                "source_stl_sha256": sha256(stl_dir / part.stl_name),
                "source_orientation": part.orientation,
                "vertex_count": len(vertices),
                "triangle_count": len(triangles),
                "plate_bounds_mm": {
                    "min": [min_x, min_y, min_z],
                    "max": [max_x, max_y, max_z],
                    "dimensions": list(dimensions),
                },
                "min_x": min_x,
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
            }
        )

    pair_spacings = []
    for first_index, first in enumerate(records):
        for second in records[first_index + 1 :]:
            spacing = _rectangle_spacing(first, second)
            if spacing < plate.minimum_spacing_mm - 1e-4:
                raise RuntimeError(f"3MF objects too close: {path.name} {first['part_key']} {second['part_key']} {spacing}")
            pair_spacings.append(spacing)
    edge_margins = [
        min(record["min_x"], record["min_y"], plate.bed_x_mm - record["max_x"], plate.bed_y_mm - record["max_y"])
        for record in records
    ]
    if min(edge_margins) < plate.minimum_edge_margin_mm - 1e-4:
        raise RuntimeError(f"3MF edge margin too small: {path.name}")
    clean_records = [
        {key: value for key, value in record.items() if key not in {"min_x", "min_y", "max_x", "max_y"}}
        for record in records
    ]
    return {
        "key": plate.key,
        "file": f"plates/{path.name}",
        "title": plate.title,
        "route": plate.route,
        "job_number": plate.job_number,
        "format": "3MF Core standard OPC package",
        "units": "millimeter",
        "bed_mm": [plate.bed_x_mm, plate.bed_y_mm],
        "object_count": len(records),
        "objects": clean_records,
        "minimum_edge_margin_required_mm": plate.minimum_edge_margin_mm,
        "minimum_edge_margin_actual_mm": min(edge_margins),
        "minimum_pairwise_spacing_required_mm": plate.minimum_spacing_mm,
        "minimum_pairwise_spacing_actual_mm": min(pair_spacings) if pair_spacings else None,
        "all_objects_at_z0": True,
        "all_objects_within_declared_bed": True,
        "all_triangle_indices_valid": True,
        "source_stl_counts_and_bounds_match": True,
        "opc_entries": ["3D/3dmodel.model", "[Content_Types].xml", "_rels/.rels"],
        "crc_test_passed": True,
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }


def render_plate_map(record: dict, three_mf_path: Path, output: Path) -> None:
    bed_x, bed_y = record["bed_mm"]
    canvas = 1100
    margin = 145
    bed_pixels = 820
    scale = bed_pixels / max(bed_x, bed_y)
    image = Image.new("RGB", (canvas, canvas), "white")
    draw = ImageDraw.Draw(image)
    title_size = 30
    title_font = ImageFont.load_default(size=title_size)
    while draw.textbbox((0, 0), record["title"], font=title_font)[2] > canvas - 100 and title_size > 18:
        title_size -= 2
        title_font = ImageFont.load_default(size=title_size)
    body_font = ImageFont.load_default(size=18)
    small_font = ImageFont.load_default(size=15)
    draw.text((50, 35), record["title"], fill="black", font=title_font)
    draw.text((50, 82), f"Declared bed: {bed_x:.0f} x {bed_y:.0f} mm | objects: {record['object_count']} | standard 3MF", fill=(40, 45, 55), font=body_font)
    x0, y0 = margin, margin
    draw.rectangle((x0, y0, x0 + bed_x * scale, y0 + bed_y * scale), outline=(30, 35, 45), width=5, fill=(241, 243, 246))
    for grid in range(10, int(max(bed_x, bed_y)), 10):
        if grid < bed_x:
            x = x0 + grid * scale
            draw.line((x, y0, x, y0 + bed_y * scale), fill=(218, 222, 228), width=1)
        if grid < bed_y:
            y = y0 + grid * scale
            draw.line((x0, y0 + bed_y * scale - y, x0 + bed_x * scale, y0 + bed_y * scale - y), fill=(218, 222, 228), width=1)
    palette = {
        "body": (225, 229, 235),
        "lid": (92, 103, 120),
        "carrier": (55, 124, 182),
        "retainer": (223, 114, 52),
        "coupon": (96, 169, 120),
    }
    with zipfile.ZipFile(three_mf_path, "r") as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    object_elements = {element.attrib["id"]: element for element in model.findall(f".//{{{CORE_NS}}}object")}
    projected_meshes = {}
    for item in model.findall(f".//{{{CORE_NS}}}build/{{{CORE_NS}}}item"):
        obj = object_elements[item.attrib["objectid"]]
        transform = [float(value) for value in item.attrib["transform"].split()]
        vertices = [
            (float(vertex.attrib["x"]) + transform[9], float(vertex.attrib["y"]) + transform[10])
            for vertex in obj.findall(f".//{{{CORE_NS}}}vertex")
        ]
        triangles = [
            tuple(int(triangle.attrib[key]) for key in ("v1", "v2", "v3"))
            for triangle in obj.findall(f".//{{{CORE_NS}}}triangle")
        ]
        projected_meshes[item.attrib["partnumber"]] = (vertices, triangles)
    for obj in record["objects"]:
        part_key = obj["part_key"]
        kind = "carrier" if part_key.endswith("carrier") else "retainer" if part_key.endswith("retainer") else part_key
        color = palette[kind]
        minimum = obj["plate_bounds_mm"]["min"]
        maximum = obj["plate_bounds_mm"]["max"]
        left = x0 + minimum[0] * scale
        right = x0 + maximum[0] * scale
        top = y0 + (bed_y - maximum[1]) * scale
        bottom = y0 + (bed_y - minimum[1]) * scale
        vertices, triangles = projected_meshes[part_key]
        for triangle in triangles:
            points = [
                (x0 + vertices[index][0] * scale, y0 + (bed_y - vertices[index][1]) * scale)
                for index in triangle
            ]
            draw.polygon(points, fill=color)
        draw.rounded_rectangle((left, top, right, bottom), radius=7, fill=None, outline=(25, 30, 38), width=3)
        label = obj["label"]
        box = draw.textbbox((0, 0), label, font=small_font)
        draw.text(((left + right - (box[2] - box[0])) / 2, (top + bottom - (box[3] - box[1])) / 2), label, fill="white" if kind in {"lid", "carrier", "retainer"} else "black", font=small_font)
    draw.text((50, 1010), "Top view only. Objects are already rotated support-free and placed at z=0; select the actual printer profile before slicing.", fill=(35, 40, 48), font=small_font)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, dpi=(180, 180), optimize=True)


def validate_plate_contract() -> list[str]:
    errors = []
    primary = next(plate for plate in PLATES if plate.key == "bambu_256_full_kit")
    if tuple(placement.part_key for placement in primary.placements) != PRODUCTION_PART_KEYS:
        errors.append("256 mm full-kit plate is not the exact ordered production-part set")
    fallback = [plate for plate in PLATES if plate.route in {"universal_preflight", "fallback_180mm"}]
    fallback_keys = [placement.part_key for plate in fallback for placement in plate.placements]
    if fallback_keys.count("coupon") != 1:
        errors.append("180 mm route does not contain exactly one coupon")
    for key in PRODUCTION_PART_KEYS:
        if fallback_keys.count(key) != 1:
            errors.append(f"180 mm route does not contain exactly one {key}")
    if set(PARTS) != set(PRODUCTION_PART_KEYS) | {"coupon"}:
        errors.append("part registry drifted")
    return errors


def build_batched_plate_assets(root: Path) -> dict:
    errors = validate_plate_contract()
    if errors:
        raise RuntimeError(f"invalid WCW-1A plate contract: {errors}")
    stl_dir = root / "stl"
    plate_dir = root / "plates"
    records = []
    for plate in PLATES:
        path = plate_dir / plate.filename
        write_3mf(stl_dir, plate, path)
        record = validate_3mf(path, plate, stl_dir)
        preview = root / "renders" / f"{Path(plate.filename).stem}_layout.png"
        render_plate_map(record, path, preview)
        record["layout_render"] = f"renders/{preview.name}"
        records.append(record)
    primary = next(record for record in records if record["key"] == "bambu_256_full_kit")
    fallback = [record for record in records if record["route"] in {"universal_preflight", "fallback_180mm"}]
    return {
        "schema_version": "scenesmith.wcw1a_batched_plate_validation.v1",
        "package_revision": "WCW-1A-R1.1-batched",
        "three_mf_core_namespace": CORE_NS,
        "bambu_studio_local_open_test": "not_run_bambu_studio_not_installed",
        "slicer_profile_embedded": False,
        "actual_printer_profile_must_be_selected_before_slicing": True,
        "primary_256mm_route": {
            "print_job_count_including_coupon": 2,
            "production_plate_object_count": primary["object_count"],
            "plates": ["universal_coupon", "bambu_256_full_kit"],
        },
        "fallback_180mm_route": {
            "print_job_count_including_coupon": 4,
            "all_parts_exactly_once": True,
            "plates": [record["key"] for record in fallback],
        },
        "plates": records,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("release_dir", type=Path)
    args = parser.parse_args()
    result = build_batched_plate_assets(args.release_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

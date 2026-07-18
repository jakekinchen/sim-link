#!/usr/bin/env python3
"""Build and verify the SO-101 AD5X split-material gripper release.

The upstream XLeRobot STL is a print-layout mesh containing three disconnected
watertight bodies.  The upstream XLeRobot 0.3.0 3MF assigns the two high-face-
count bodies to PLA and the 3,480-face Fin-Ray body to TPU.  This builder splits
only at disconnected components, preserves triangle geometry and z=0 print
orientation, and writes one standard 3MF plus one fallback batch STL per
material.  It does not embed a slicer profile or G-code.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE = REPO_ROOT / "release/SO101_R1_AD5X_compliant_gripper"
DEFAULT_ZIP = REPO_ROOT / "release/SO101_R1_AD5X_Compliant_Gripper_Print_Package.zip"

UPSTREAM_REPOSITORY = "https://github.com/Vector-Wangel/XLeRobot"
UPSTREAM_COMMIT = "51ca0ec31bdb48713b94bacdba828bf8d889296b"
UPSTREAM_STL_SHA256 = "4125201fffaca5f9e5ee354a11ff80328c08e7ccb4676661442a937b7a79b121"
UPSTREAM_STEP_SHA256 = "d90d2434f6920be1643963c6c1ba2dc1935a7ed84683ab01e07ee4bc132f4816"
UPSTREAM_LICENSE_SHA256 = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
UPSTREAM_3MF_SHA256 = "4b41ae03895144ffff0a22b0d1a76e02d4ff0db0bc5ff0066ab528df8ce4fa4d"

BED_X_MM = 220.0
BED_Y_MM = 220.0
MIN_EDGE_MARGIN_MM = 10.0
MIN_OBJECT_SPACING_MM = 12.0

CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
MODEL_RELATIONSHIP = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
XML_NS = "http://www.w3.org/XML/1998/namespace"


@dataclass(frozen=True)
class Triangle:
    normal: tuple[float, float, float]
    vertices: tuple[tuple[float, float, float], ...]
    attribute: int = 0


@dataclass(frozen=True)
class ComponentSpec:
    key: str
    label: str
    material: str
    triangle_count: int
    upstream_extruder: int
    density_g_cm3: float


SPECS_BY_TRIANGLE_COUNT = {
    39690: ComponentSpec(
        "fixed_base",
        "SO-101 fixed gripper base",
        "PLA or PLA+",
        39690,
        1,
        1.24,
    ),
    18714: ComponentSpec(
        "moving_base",
        "SO-101 moving gripper base",
        "PLA or PLA+",
        18714,
        1,
        1.24,
    ),
    3480: ComponentSpec(
        "soft_fin",
        "SO-101 Fin-Ray soft finger",
        "TPU 95A",
        3480,
        3,
        1.21,
    ),
}


@dataclass
class Component:
    spec: ComponentSpec
    triangles: list[Triangle]
    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]
    source_geometry_sha256: str
    manifold_edge_count: int
    boundary_edge_count: int
    nonmanifold_edge_count: int
    inconsistent_winding_edge_count: int
    signed_volume_mm3: float
    volume_mm3: float
    minimum_triangle_area_mm2: float
    submicron_area_triangle_count: int

    @property
    def dimensions(self) -> tuple[float, float, float]:
        return tuple(self.maximum[i] - self.minimum[i] for i in range(3))

    @property
    def normalized_triangles(self) -> list[Triangle]:
        return [
            Triangle(
                triangle.normal,
                tuple(
                    tuple(vertex[axis] - self.minimum[axis] for axis in range(3))
                    for vertex in triangle.vertices
                ),
                triangle.attribute,
            )
            for triangle in self.triangles
        ]


@dataclass(frozen=True)
class Placement:
    component_key: str
    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class Plate:
    key: str
    filename: str
    fallback_stl: str
    title: str
    material: str
    placements: tuple[Placement, ...]


PLATES = (
    Plate(
        "plate01_pla_bases",
        "SO101_R1_AD5X_plate01_PLA_gripper-bases.3mf",
        "SO101_R1_AD5X_plate01_PLA_gripper-bases_batch.stl",
        "SO-101 compliant gripper - PLA bases",
        "PLA or PLA+",
        (
            Placement("fixed_base", 58.668, 85.708),
            Placement("moving_base", 125.668, 99.834),
        ),
    ),
    Plate(
        "plate02_tpu_soft_fin",
        "SO101_R1_AD5X_plate02_TPU95A_soft-fin.3mf",
        "SO101_R1_AD5X_plate02_TPU95A_soft-fin_batch.stl",
        "SO-101 compliant gripper - TPU 95A Fin-Ray finger",
        "TPU 95A",
        (Placement("soft_fin", 76.408, 97.906),),
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _geometry_sha(triangles: list[Triangle]) -> str:
    digest = hashlib.sha256()
    for triangle in triangles:
        for vertex in triangle.vertices:
            digest.update(struct.pack("<3f", *vertex))
    return digest.hexdigest()


def read_binary_stl(path: Path) -> list[Triangle]:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"STL is too short: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise RuntimeError(f"STL binary length/count mismatch: {path}")
    triangles: list[Triangle] = []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * index)
        normal = tuple(float(value) for value in values[:3])
        vertices = tuple(
            tuple(float(value) for value in values[offset : offset + 3])
            for offset in (3, 6, 9)
        )
        if not all(math.isfinite(value) for vertex in vertices for value in vertex):
            raise RuntimeError(f"non-finite STL coordinate at triangle {index}: {path}")
        triangles.append(Triangle(normal, vertices, int(values[-1])))
    return triangles


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(a[i] - b[i] for i in range(3))


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(a[i] * b[i] for i in range(3))


def _vertex_key(vertex: tuple[float, float, float]) -> bytes:
    return struct.pack("<3f", *vertex)


def _mesh_properties(triangles: list[Triangle]) -> dict:
    edge_counts: Counter[tuple[bytes, bytes]] = Counter()
    edge_direction_balance: Counter[tuple[bytes, bytes]] = Counter()
    zero_area_cross_squared_epsilon = 1e-24
    minimum_triangle_area = math.inf
    submicron_area_triangle_count = 0
    signed_volume = 0.0
    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    for index, triangle in enumerate(triangles):
        a, b, c = triangle.vertices
        cross = _cross(_sub(b, a), _sub(c, a))
        cross_squared = _dot(cross, cross)
        if cross_squared <= zero_area_cross_squared_epsilon:
            raise RuntimeError(f"zero-area triangle in {len(triangles)}-triangle component at {index}")
        triangle_area = math.sqrt(cross_squared) / 2.0
        minimum_triangle_area = min(minimum_triangle_area, triangle_area)
        submicron_area_triangle_count += triangle_area < 1e-6
        signed_volume += _dot(a, _cross(b, c)) / 6.0
        keys = [_vertex_key(vertex) for vertex in triangle.vertices]
        for first, second in ((0, 1), (1, 2), (2, 0)):
            ordered = (keys[first], keys[second])
            undirected = tuple(sorted(ordered))
            edge_counts[undirected] += 1
            edge_direction_balance[undirected] += 1 if ordered == undirected else -1
        for vertex in triangle.vertices:
            for axis in range(3):
                minimum[axis] = min(minimum[axis], vertex[axis])
                maximum[axis] = max(maximum[axis], vertex[axis])
    return {
        "minimum": tuple(minimum),
        "maximum": tuple(maximum),
        "manifold_edge_count": sum(count == 2 for count in edge_counts.values()),
        "boundary_edge_count": sum(count == 1 for count in edge_counts.values()),
        "nonmanifold_edge_count": sum(count > 2 for count in edge_counts.values()),
        "inconsistent_winding_edge_count": sum(
            count == 2 and edge_direction_balance[edge] != 0
            for edge, count in edge_counts.items()
        ),
        "signed_volume_mm3": signed_volume,
        "volume_mm3": abs(signed_volume),
        "minimum_triangle_area_mm2": minimum_triangle_area,
        "submicron_area_triangle_count": submicron_area_triangle_count,
    }


def split_components(triangles: list[Triangle]) -> dict[str, Component]:
    parent = list(range(len(triangles)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    first_triangle_for_vertex: dict[bytes, int] = {}
    for index, triangle in enumerate(triangles):
        for vertex in triangle.vertices:
            key = _vertex_key(vertex)
            previous = first_triangle_for_vertex.setdefault(key, index)
            union(index, previous)

    grouped: defaultdict[int, list[Triangle]] = defaultdict(list)
    for index, triangle in enumerate(triangles):
        grouped[find(index)].append(triangle)
    if len(grouped) != 3:
        raise RuntimeError(f"expected 3 disconnected upstream components, found {len(grouped)}")

    result: dict[str, Component] = {}
    for group in grouped.values():
        spec = SPECS_BY_TRIANGLE_COUNT.get(len(group))
        if spec is None:
            raise RuntimeError(f"unexpected upstream component triangle count: {len(group)}")
        properties = _mesh_properties(group)
        component = Component(
            spec=spec,
            triangles=group,
            minimum=properties["minimum"],
            maximum=properties["maximum"],
            source_geometry_sha256=_geometry_sha(group),
            manifold_edge_count=properties["manifold_edge_count"],
            boundary_edge_count=properties["boundary_edge_count"],
            nonmanifold_edge_count=properties["nonmanifold_edge_count"],
            inconsistent_winding_edge_count=properties["inconsistent_winding_edge_count"],
            signed_volume_mm3=properties["signed_volume_mm3"],
            volume_mm3=properties["volume_mm3"],
            minimum_triangle_area_mm2=properties["minimum_triangle_area_mm2"],
            submicron_area_triangle_count=properties["submicron_area_triangle_count"],
        )
        if component.boundary_edge_count or component.nonmanifold_edge_count:
            raise RuntimeError(f"upstream component is not watertight/manifold: {spec.key}")
        if component.inconsistent_winding_edge_count or component.signed_volume_mm3 <= 0:
            raise RuntimeError(f"upstream component winding/normals are inconsistent or inverted: {spec.key}")
        if abs(component.minimum[2]) > 1e-6:
            raise RuntimeError(f"upstream print orientation is not at z=0: {spec.key}")
        result[spec.key] = component
    if set(result) != {spec.key for spec in SPECS_BY_TRIANGLE_COUNT.values()}:
        raise RuntimeError("upstream component registry mismatch")
    return result


def _translated_triangle(triangle: Triangle, translation: tuple[float, float, float]) -> Triangle:
    return Triangle(
        triangle.normal,
        tuple(
            tuple(vertex[axis] + translation[axis] for axis in range(3))
            for vertex in triangle.vertices
        ),
        triangle.attribute,
    )


def write_binary_stl(path: Path, triangles: list[Triangle], title: str) -> None:
    header = title.encode("ascii", "replace")[:80].ljust(80, b"\0")
    with path.open("wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(triangles)))
        for triangle in triangles:
            values = (*triangle.normal, *(value for vertex in triangle.vertices for value in vertex), triangle.attribute)
            handle.write(struct.pack("<12fH", *values))


def _component_mesh(component: Component) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    vertex_indices: dict[bytes, int] = {}
    for triangle in component.normalized_triangles:
        face = []
        for vertex in triangle.vertices:
            key = _vertex_key(vertex)
            if key not in vertex_indices:
                vertex_indices[key] = len(vertices)
                vertices.append(vertex)
            face.append(vertex_indices[key])
        faces.append(tuple(face))
    return vertices, faces


def _float(value: float) -> str:
    value = 0.0 if abs(value) < 5e-10 else value
    return f"{value:.9g}"


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


def _model_xml(plate: Plate, components: dict[str, Component]) -> bytes:
    ET.register_namespace("", CORE_NS)
    root = ET.Element(f"{{{CORE_NS}}}model", {"unit": "millimeter", f"{{{XML_NS}}}lang": "en-US"})
    for name, value in (
        ("Title", plate.title),
        ("Designer", "SceneSmith geometry-preserving XLeRobot release adapter"),
        ("Description", f"AD5X 220 x 220 mm geometry-only plate; material {plate.material}; select the printer and filament profile before slicing."),
        ("Copyright", "Derived from XLeRobot under Apache-2.0; upstream commit recorded in SOURCE_PROVENANCE.md"),
    ):
        metadata = ET.SubElement(root, f"{{{CORE_NS}}}metadata", name=name)
        metadata.text = value
    resources = ET.SubElement(root, f"{{{CORE_NS}}}resources")
    build = ET.SubElement(root, f"{{{CORE_NS}}}build")
    for object_id, placement in enumerate(plate.placements, start=1):
        component = components[placement.component_key]
        vertices, faces = _component_mesh(component)
        obj = ET.SubElement(
            resources,
            f"{{{CORE_NS}}}object",
            id=str(object_id),
            name=component.spec.label,
            partnumber=component.spec.key,
            type="model",
        )
        mesh = ET.SubElement(obj, f"{{{CORE_NS}}}mesh")
        xml_vertices = ET.SubElement(mesh, f"{{{CORE_NS}}}vertices")
        for x, y, z in vertices:
            ET.SubElement(xml_vertices, f"{{{CORE_NS}}}vertex", x=_float(x), y=_float(y), z=_float(z))
        xml_triangles = ET.SubElement(mesh, f"{{{CORE_NS}}}triangles")
        for v1, v2, v3 in faces:
            ET.SubElement(xml_triangles, f"{{{CORE_NS}}}triangle", v1=str(v1), v2=str(v2), v3=str(v3))
        transform = f"1 0 0 0 1 0 0 0 1 {_float(placement.x_mm)} {_float(placement.y_mm)} 0"
        ET.SubElement(build, f"{{{CORE_NS}}}item", objectid=str(object_id), transform=transform, partnumber=component.spec.key)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_3mf(path: Path, plate: Plate, components: dict[str, Component]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _relationships_xml())
        archive.writestr("3D/3dmodel.model", _model_xml(plate, components))


def _batch_triangles(plate: Plate, components: dict[str, Component]) -> list[Triangle]:
    result: list[Triangle] = []
    for placement in plate.placements:
        component = components[placement.component_key]
        translation = (placement.x_mm, placement.y_mm, 0.0)
        result.extend(_translated_triangle(triangle, translation) for triangle in component.normalized_triangles)
    return result


def _bbox_spacing(left: dict, right: dict) -> float:
    gap_x = max(left["min"][0] - right["max"][0], right["min"][0] - left["max"][0], 0.0)
    gap_y = max(left["min"][1] - right["max"][1], right["min"][1] - left["max"][1], 0.0)
    return math.hypot(gap_x, gap_y)


def validate_3mf(path: Path, plate: Plate, components: dict[str, Component]) -> dict:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f"3MF CRC failure: {path}")
        if sorted(archive.namelist()) != ["3D/3dmodel.model", "[Content_Types].xml", "_rels/.rels"]:
            raise RuntimeError(f"unexpected 3MF entries: {path}")
        content_types = ET.fromstring(archive.read("[Content_Types].xml"))
        relationships = ET.fromstring(archive.read("_rels/.rels"))
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    if content_types.tag != f"{{{CONTENT_TYPES_NS}}}Types":
        raise RuntimeError(f"invalid 3MF content-types root: {path}")
    relationship = relationships.find(f"{{{RELATIONSHIPS_NS}}}Relationship")
    if relationship is None or relationship.attrib.get("Type") != MODEL_RELATIONSHIP:
        raise RuntimeError(f"missing 3MF model relationship: {path}")
    if model.attrib.get("unit") != "millimeter":
        raise RuntimeError(f"3MF unit is not millimeter: {path}")
    objects = {obj.attrib["id"]: obj for obj in model.findall(f".//{{{CORE_NS}}}object")}
    items = model.findall(f".//{{{CORE_NS}}}build/{{{CORE_NS}}}item")
    if len(objects) != len(plate.placements) or len(items) != len(plate.placements):
        raise RuntimeError(f"3MF object/build count mismatch: {path}")
    records = []
    for placement, item in zip(plate.placements, items):
        component = components[placement.component_key]
        obj = objects[item.attrib["objectid"]]
        if obj.attrib.get("partnumber") != component.spec.key or obj.attrib.get("name") != component.spec.label:
            raise RuntimeError(f"3MF identity mismatch: {path} {component.spec.key}")
        transform = [float(value) for value in item.attrib["transform"].split()]
        if transform[:9] != [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0] or len(transform) != 12:
            raise RuntimeError(f"3MF contains non-translation transform: {path}")
        if max(abs(transform[9] - placement.x_mm), abs(transform[10] - placement.y_mm), abs(transform[11])) > 1e-6:
            raise RuntimeError(f"3MF placement drift: {path} {component.spec.key}")
        vertices = [
            (float(vertex.attrib["x"]), float(vertex.attrib["y"]), float(vertex.attrib["z"]))
            for vertex in obj.findall(f".//{{{CORE_NS}}}vertex")
        ]
        triangles = [
            tuple(int(triangle.attrib[key]) for key in ("v1", "v2", "v3"))
            for triangle in obj.findall(f".//{{{CORE_NS}}}triangle")
        ]
        expected_vertices, expected_faces = _component_mesh(component)
        if len(vertices) != len(expected_vertices) or len(triangles) != len(expected_faces):
            raise RuntimeError(f"3MF/source mesh count drift: {path} {component.spec.key}")
        if triangles != expected_faces:
            raise RuntimeError(f"3MF/source face-index drift: {path} {component.spec.key}")
        if any(abs(vertices[i][axis] - expected_vertices[i][axis]) > 2e-5 for i in range(len(vertices)) for axis in range(3)):
            raise RuntimeError(f"3MF/source coordinate drift: {path} {component.spec.key}")
        if any(len(set(face)) != 3 or min(face) < 0 or max(face) >= len(vertices) for face in triangles):
            raise RuntimeError(f"3MF invalid triangle index: {path} {component.spec.key}")
        minimum = [
            placement.x_mm + min(vertex[0] for vertex in vertices),
            placement.y_mm + min(vertex[1] for vertex in vertices),
            min(vertex[2] for vertex in vertices),
        ]
        maximum = [placement.x_mm + max(vertex[0] for vertex in vertices), placement.y_mm + max(vertex[1] for vertex in vertices), max(vertex[2] for vertex in vertices)]
        edge_margin = min(minimum[0], minimum[1], BED_X_MM - maximum[0], BED_Y_MM - maximum[1])
        if abs(minimum[2]) > 1e-6 or edge_margin < MIN_EDGE_MARGIN_MM - 1e-4:
            raise RuntimeError(f"3MF object is outside z=0/bed contract: {path} {component.spec.key}")
        records.append(
            {
                "component": component.spec.key,
                "label": component.spec.label,
                "material": component.spec.material,
                "triangle_count": len(triangles),
                "vertex_count": len(vertices),
                "source_geometry_sha256": component.source_geometry_sha256,
                "plate_bounds_mm": {"min": minimum, "max": maximum},
                "edge_margin_mm": edge_margin,
            }
        )
    spacings = [
        _bbox_spacing(left["plate_bounds_mm"], right["plate_bounds_mm"])
        for index, left in enumerate(records)
        for right in records[index + 1 :]
    ]
    if spacings and min(spacings) < MIN_OBJECT_SPACING_MM - 1e-4:
        raise RuntimeError(f"3MF object spacing is too small: {path}")
    return {
        "file": f"plates/{path.name}",
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "format": "3MF Core standard OPC package",
        "units": "millimeter",
        "declared_bed_mm": [BED_X_MM, BED_Y_MM],
        "material": plate.material,
        "object_count": len(records),
        "objects": records,
        "minimum_actual_edge_margin_mm": min(record["edge_margin_mm"] for record in records),
        "minimum_actual_object_spacing_mm": min(spacings) if spacings else None,
        "all_objects_at_z0": True,
        "all_objects_within_bed": True,
        "source_counts_faces_and_coordinates_match": True,
        "crc_test_passed": True,
        "slicer_profile_embedded": False,
    }


def validate_batch_stl(path: Path, plate: Plate, components: dict[str, Component]) -> dict:
    triangles = read_binary_stl(path)
    counts = []
    parent = list(range(len(triangles)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    seen: dict[bytes, int] = {}
    for index, triangle in enumerate(triangles):
        for vertex in triangle.vertices:
            key = _vertex_key(vertex)
            previous = seen.setdefault(key, index)
            union(index, previous)
    groups: defaultdict[int, list[Triangle]] = defaultdict(list)
    for index, triangle in enumerate(triangles):
        groups[find(index)].append(triangle)
    expected_counts = sorted(components[p.component_key].spec.triangle_count for p in plate.placements)
    actual_counts = sorted(len(group) for group in groups.values())
    if actual_counts != expected_counts:
        raise RuntimeError(f"fallback STL disconnected-component drift: {path} {actual_counts}")
    for group in groups.values():
        properties = _mesh_properties(group)
        if properties["boundary_edge_count"] or properties["nonmanifold_edge_count"]:
            raise RuntimeError(f"fallback STL is not watertight/manifold: {path}")
        if properties["inconsistent_winding_edge_count"] or properties["signed_volume_mm3"] <= 0:
            raise RuntimeError(f"fallback STL component winding/normals are inconsistent or inverted: {path}")
        if abs(properties["minimum"][2]) > 1e-6:
            raise RuntimeError(f"fallback STL component is not at z=0: {path}")
        counts.append(
            {
                "triangle_count": len(group),
                "volume_mm3": properties["volume_mm3"],
                "dimensions_mm": [properties["maximum"][i] - properties["minimum"][i] for i in range(3)],
                "bounds_mm": {"min": list(properties["minimum"]), "max": list(properties["maximum"])},
                "minimum_triangle_area_mm2": properties["minimum_triangle_area_mm2"],
                "submicron_area_triangle_count": properties["submicron_area_triangle_count"],
                "inconsistent_winding_edge_count": properties["inconsistent_winding_edge_count"],
                "signed_volume_mm3": properties["signed_volume_mm3"],
                "watertight": True,
                "manifold": True,
                "consistently_outward_wound": True,
            }
        )
    minimum_z = min(vertex[2] for triangle in triangles for vertex in triangle.vertices)
    maximum_x = max(vertex[0] for triangle in triangles for vertex in triangle.vertices)
    maximum_y = max(vertex[1] for triangle in triangles for vertex in triangle.vertices)
    minimum_x = min(vertex[0] for triangle in triangles for vertex in triangle.vertices)
    minimum_y = min(vertex[1] for triangle in triangles for vertex in triangle.vertices)
    if abs(minimum_z) > 1e-6 or min(minimum_x, minimum_y) < 0 or maximum_x > BED_X_MM or maximum_y > BED_Y_MM:
        raise RuntimeError(f"fallback STL lies outside plate contract: {path}")
    return {
        "file": f"fallback_stl/{path.name}",
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "units": "millimeter",
        "component_count": len(groups),
        "expected_triangle_counts": expected_counts,
        "components": sorted(counts, key=lambda record: record["triangle_count"], reverse=True),
        "all_components_watertight_and_manifold": True,
        "all_components_at_z0": True,
        "all_components_within_220mm_bed": True,
    }


def write_plate_svg(path: Path, plate: Plate, components: dict[str, Component]) -> None:
    scale = 3.2
    size = int(BED_X_MM * scale)
    colors = {"PLA or PLA+": "#8f99a8", "TPU 95A": "#2f7fd5"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size + 80}" height="{size + 150}" viewBox="0 0 {size + 80} {size + 150}">',
        '<rect width="100%" height="100%" fill="#f7f8fa"/>',
        f'<text x="40" y="38" font-family="sans-serif" font-size="22" font-weight="700">{plate.title}</text>',
        f'<text x="40" y="65" font-family="sans-serif" font-size="15">AD5X 220 x 220 mm | {plate.material} | geometry-only 3MF | no supports</text>',
        f'<rect x="40" y="90" width="{size}" height="{size}" fill="#e8ebef" stroke="#262b33" stroke-width="3"/>',
    ]
    for grid in range(10, 220, 10):
        position = 40 + grid * scale
        parts.append(f'<line x1="{position}" y1="90" x2="{position}" y2="{90 + size}" stroke="#cfd4dc" stroke-width="0.7"/>')
        parts.append(f'<line x1="40" y1="{90 + size - grid * scale}" x2="{40 + size}" y2="{90 + size - grid * scale}" stroke="#cfd4dc" stroke-width="0.7"/>')
    for placement in plate.placements:
        component = components[placement.component_key]
        width, height, _ = component.dimensions
        x = 40 + placement.x_mm * scale
        y = 90 + size - (placement.y_mm + height) * scale
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width * scale:.2f}" height="{height * scale:.2f}" rx="5" fill="{colors[plate.material]}" stroke="#20242a" stroke-width="2"/>')
        parts.append(f'<text x="{x + width * scale / 2:.2f}" y="{y + height * scale / 2:.2f}" text-anchor="middle" dominant-baseline="middle" font-family="sans-serif" font-size="12" fill="white">{component.spec.key}</text>')
    parts.append(f'<text x="40" y="{size + 125}" font-family="sans-serif" font-size="14">Already arranged at 100% scale and z=0. Do not auto-orient or auto-arrange.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _component_record(component: Component) -> dict:
    return {
        "key": component.spec.key,
        "label": component.spec.label,
        "material": component.spec.material,
        "upstream_extruder": component.spec.upstream_extruder,
        "triangle_count": component.spec.triangle_count,
        "dimensions_mm": list(component.dimensions),
        "source_bounds_mm": {"min": list(component.minimum), "max": list(component.maximum)},
        "source_geometry_sha256": component.source_geometry_sha256,
        "volume_mm3": component.volume_mm3,
        "estimated_mass_g": component.volume_mm3 / 1000.0 * component.spec.density_g_cm3,
        "minimum_triangle_area_mm2": component.minimum_triangle_area_mm2,
        "submicron_area_triangle_count": component.submicron_area_triangle_count,
        "manifold_edge_count": component.manifold_edge_count,
        "boundary_edge_count": component.boundary_edge_count,
        "nonmanifold_edge_count": component.nonmanifold_edge_count,
        "inconsistent_winding_edge_count": component.inconsistent_winding_edge_count,
        "signed_volume_mm3": component.signed_volume_mm3,
        "watertight": component.boundary_edge_count == 0,
        "manifold": component.nonmanifold_edge_count == 0,
        "consistently_outward_wound": component.inconsistent_winding_edge_count == 0 and component.signed_volume_mm3 > 0,
        "z0_print_orientation_preserved": abs(component.minimum[2]) <= 1e-6,
    }


def _write_docs(release: Path, components: dict[str, Component]) -> None:
    pla_mass = sum(c.volume_mm3 / 1000.0 * c.spec.density_g_cm3 for c in components.values() if c.spec.material == "PLA or PLA+")
    tpu_mass = sum(c.volume_mm3 / 1000.0 * c.spec.density_g_cm3 for c in components.values() if c.spec.material == "TPU 95A")
    readme = f"""# SO-101 compliant gripper - FlashForge AD5X print handoff

There are exactly **two print jobs**. Open the two numbered 3MF files in order.
The objects are already split by material, oriented, centered, and arranged for
the AD5X 220 x 220 mm bed. Do not split, rotate, scale, or auto-arrange them.

## Job 1 - rigid bases

- File: `plates/{PLATES[0].filename}`
- Material: ordinary PLA or PLA+; any color
- Copies: one plate, containing both required base pieces
- AD5X/default nozzle: 0.4 mm
- Layer height: 0.20 mm
- Walls: 2 (the upstream XLeRobot project setting)
- Top/bottom: 5 top, 3 bottom
- Infill: 15% grid
- Supports: off
- Scale: 100%
- Approximate solid-model mass before slicer infill: {pla_mass:.1f} g

## Job 2 - soft finger

- File: `plates/{PLATES[1].filename}`
- Material: TPU around Shore 95A. If the spool is substantially softer or
  harder, pause and tell Jake before printing.
- Copies: one plate, containing the complete Fin-Ray finger
- AD5X/default nozzle: 0.4 mm
- Layer height: 0.20 mm
- Walls: 2
- Infill: 15% grid
- Supports: off; the upstream design explicitly avoids TPU supports
- Scale: 100%
- Use the spool manufacturer's temperature plus your tuned AD5X TPU flow,
  speed, and retraction settings. Those are intentionally not embedded.
- Feed TPU through the shortest straight external path; do not route TPU
  through IFS. FlashForge lists TPU 95A as AD5X-compatible but not IFS-compatible.
- A 3 mm brim is optional only if first-layer adhesion is marginal.
- Approximate solid-model mass before slicer infill: {tpu_mass:.1f} g

## What to send back

Please return the three printed pieces loose. Jake will provide the two M3
screws and perform installation/calibration. No assembly work is needed from
the printer.

## Fallback

If a 3MF does not open correctly, import the correspondingly named file in
`fallback_stl/`. Each fallback STL is already arranged as the same complete
material plate.

## Important calibration note

This compliant gripper changes the robot's contact surfaces and compliance.
It must be measured and added to SimLink before any calibrated real-to-simulation
or grasp result is claimed. Printing the parts does not itself verify physical
fit, grip performance, or robot calibration.
"""
    (release / "README_PRINTING.md").write_text(readme, encoding="utf-8")

    assembly = """# Assembly notes for Jake

Zane only needs to print and return the three loose parts.

The release contains two rigid PLA bases plus one TPU Fin-Ray finger. The
upstream design uses two additional M3 screws to fasten the TPU element to the
two bases. The upstream source does not freeze screw length; select the shortest
screw that achieves full thread engagement without bottoming or protruding.
Do not ask the printer to guess the length.

Before installing on the robot:

1. Compare every mounting hole and interface against the removed stock SO-101
   components without powering the arm.
2. Deburr only loose strings or elephant-foot flash; do not sand contact or
   mounting geometry to force a fit.
3. Confirm the TPU element seats symmetrically and moves without rubbing the
   wrist shell or camera.
4. Measure open/closed aperture, fingertip stand-off, and pad centerline.
5. Update the SimLink mesh/contact model and recalibrate gripper closure before
   any calibrated robot use.

Two M3 screws and optional 3M TB641 gripping material are owner-supplied and
are not part of this print package.
"""
    (release / "ASSEMBLY_FOR_JAKE.md").write_text(assembly, encoding="utf-8")

    provenance = f"""# Source provenance

- Upstream: `{UPSTREAM_REPOSITORY}`
- Pinned commit: `{UPSTREAM_COMMIT}`
- License: Apache License 2.0 (included as `upstream/LICENSE_XLeRobot_Apache-2.0.txt`)
- Combined upstream STL: `hardware/SO101_soft_fin.stl`
- Editable TPU-finger source: `hardware/step/soft_gripper_finger.step`
- Upstream all-robot project used only to verify material assignment:
  `hardware/XLeRobot_0_3_0.3mf`

The upstream combined STL contains three disconnected bodies. The pinned
XLeRobot 3MF assigns its 39,690- and 18,714-face gripper bodies to extruder 1
(PLA), and its 3,480-face soft-finger body to extruder 3 (TPU). This release
splits only on those disconnected boundaries, applies translation-only plate
placement, and does not rescale, remesh, decimate, smooth, or repair triangles.

## Frozen source hashes

- `SO101_soft_fin.stl`: `{UPSTREAM_STL_SHA256}`
- `soft_gripper_finger.step`: `{UPSTREAM_STEP_SHA256}`
- `LICENSE`: `{UPSTREAM_LICENSE_SHA256}`
- upstream `XLeRobot_0_3_0.3mf` audit copy: `{UPSTREAM_3MF_SHA256}`
"""
    (release / "source/SOURCE_PROVENANCE.md").write_text(provenance, encoding="utf-8")

    assignment = {
        "schema_version": "scenesmith.xlerobot_gripper_material_assignment.v1",
        "upstream_repository": UPSTREAM_REPOSITORY,
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_3mf_path": "hardware/XLeRobot_0_3_0.3mf",
        "upstream_3mf_sha256": UPSTREAM_3MF_SHA256,
        "audit_method": "parsed Metadata/model_settings.config and matched disconnected component face counts",
        "filament_type_array_prefix": ["PLA", "PLA", "TPU"],
        "assignments": [
            {"face_count": 39690, "upstream_object_id": 62, "extruder": 1, "material": "PLA"},
            {"face_count": 18714, "upstream_object_id": 64, "extruder": 1, "material": "PLA"},
            {"face_count": 3480, "upstream_object_id": 66, "extruder": 3, "material": "TPU"},
        ],
    }
    (release / "source/UPSTREAM_ASSIGNMENT_EVIDENCE.json").write_text(json.dumps(assignment, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render(release: Path) -> None:
    blender = shutil.which("blender")
    renderer = REPO_ROOT / "scripts/render_so101_gripper_release.py"
    if blender is None:
        raise RuntimeError("Blender is required for release render verification")
    subprocess.run(
        [blender, "--background", "--python", str(renderer), "--", str(release)],
        cwd=REPO_ROOT,
        check=True,
    )


def _write_manifest(release: Path) -> dict:
    excluded = {"MANIFEST.json", "MANIFEST.sha256"}
    files = [path for path in sorted(release.rglob("*")) if path.is_file() and path.relative_to(release).as_posix() not in excluded]
    entries = [
        {"file": path.relative_to(release).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in files
    ]
    manifest = {
        "schema_version": "scenesmith.so101_ad5x_gripper_manifest.v1",
        "package_revision": "SO101-compliant-gripper-R1-AD5X",
        "file_count_excluding_manifest_files": len(entries),
        "files": entries,
    }
    manifest_path = release / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [f"{sha256(manifest_path)}  MANIFEST.json"]
    lines.extend(f"{entry['sha256']}  {entry['file']}" for entry in entries)
    (release / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def _write_zip(release: Path, output_zip: Path, manifest: dict) -> dict:
    expected = [entry["file"] for entry in manifest["files"]] + ["MANIFEST.json", "MANIFEST.sha256"]
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(expected):
            archive.write(release / relative, f"SO101_R1_AD5X_compliant_gripper/{relative}")
    with zipfile.ZipFile(output_zip) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"release ZIP CRC failure: {bad}")
        actual = sorted(name for name in archive.namelist() if not name.endswith("/"))
        required = sorted(f"SO101_R1_AD5X_compliant_gripper/{relative}" for relative in expected)
        if actual != required:
            raise RuntimeError("release ZIP content mismatch")
        embedded_manifest = json.loads(archive.read("SO101_R1_AD5X_compliant_gripper/MANIFEST.json"))
        if embedded_manifest != manifest:
            raise RuntimeError("release ZIP embedded manifest mismatch")
    return {
        "path": output_zip.relative_to(REPO_ROOT).as_posix(),
        "sha256": sha256(output_zip),
        "size_bytes": output_zip.stat().st_size,
        "crc_test_passed": True,
        "content_list_exact": True,
        "embedded_manifest_verified": True,
    }


def build_release(release: Path, output_zip: Path, render: bool = True) -> dict:
    source_dir = release / "source/upstream"
    source_stl = source_dir / "SO101_soft_fin_upstream.stl"
    source_step = source_dir / "soft_gripper_finger_upstream.step"
    license_path = source_dir / "LICENSE_XLeRobot_Apache-2.0.txt"
    expected_hashes = {
        source_stl: UPSTREAM_STL_SHA256,
        source_step: UPSTREAM_STEP_SHA256,
        license_path: UPSTREAM_LICENSE_SHA256,
    }
    for path, expected in expected_hashes.items():
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"missing or drifted pinned upstream source: {path}")

    for directory in (release / "plates", release / "fallback_stl", release / "renders", release / "validation"):
        directory.mkdir(parents=True, exist_ok=True)

    components = split_components(read_binary_stl(source_stl))
    plate_records = []
    fallback_records = []
    for plate in PLATES:
        plate_path = release / "plates" / plate.filename
        fallback_path = release / "fallback_stl" / plate.fallback_stl
        write_3mf(plate_path, plate, components)
        write_binary_stl(fallback_path, _batch_triangles(plate, components), plate.title)
        write_plate_svg(release / "renders" / f"{plate.key}_layout.svg", plate, components)
        plate_records.append(validate_3mf(plate_path, plate, components))
        fallback_records.append(validate_batch_stl(fallback_path, plate, components))

    _write_docs(release, components)
    if render:
        _render(release)

    render_files = [
        release / "renders/SO101_R1_AD5X_plate01_PLA_layout.png",
        release / "renders/SO101_R1_AD5X_plate02_TPU95A_layout.png",
        release / "renders/SO101_R1_components_overview.png",
    ]
    if not all(path.is_file() and path.stat().st_size > 0 for path in render_files):
        raise RuntimeError("required visual-inspection renders are missing")

    validation = {
        "schema_version": "scenesmith.so101_ad5x_gripper_validation.v1",
        "package_revision": "SO101-compliant-gripper-R1-AD5X",
        "source": {
            "repository": UPSTREAM_REPOSITORY,
            "commit": UPSTREAM_COMMIT,
            "combined_stl_sha256": sha256(source_stl),
            "soft_finger_step_sha256": sha256(source_step),
            "license_sha256": sha256(license_path),
            "upstream_3mf_assignment_sha256": UPSTREAM_3MF_SHA256,
        },
        "printer_target": {
            "model": "FlashForge AD5X",
            "build_volume_mm": [220.0, 220.0, 220.0],
            "default_nozzle_mm": 0.4,
            "slicer": "Orca-Flashforge or Orca Slicer",
            "slicer_profile_embedded": False,
            "gcode_embedded": False,
        },
        "components": [_component_record(components[key]) for key in ("fixed_base", "moving_base", "soft_fin")],
        "plates": plate_records,
        "fallback_stls": fallback_records,
        "gates": {
            "pinned_source_hashes_match": True,
            "exactly_three_disconnected_source_components": True,
            "upstream_material_assignment_bound_by_face_count": True,
            "all_source_components_finite_nondegenerate_watertight_manifold": True,
            "source_z0_print_orientation_preserved": True,
            "no_scale_rotation_remesh_or_triangle_repair": True,
            "pla_and_tpu_separated_into_exactly_two_jobs": True,
            "all_release_3mf_files_crc_and_xml_valid": True,
            "all_release_stl_files_open_and_validate": True,
            "all_parts_fit_ad5x_220mm_bed": True,
            "support_free_upstream_intent_preserved": True,
            "visual_renders_generated": True,
            "physical_fit_verified": False,
            "as_printed_grip_verified": False,
            "robot_calibration_updated": False,
        },
        "residual_risks": [
            "Zane confirmed TPU availability but not Shore hardness or spool brand.",
            "Temperatures, flow, retraction, and speed must use the actual spool and tuned AD5X profile.",
            "Upstream specifies two additional M3 screws but does not freeze screw length.",
            "No physical print, fit, grip, or durability test has been completed in this offline release.",
            "Installing the compliant gripper changes contact geometry and requires a new SimLink gripper calibration.",
        ],
    }
    validation_path = release / "validation/PRINT_VALIDATION.json"
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    final_gate = {
        "schema_version": "scenesmith.so101_ad5x_gripper_final_gate.v1",
        "all_required_files_exist": True,
        "all_stls_open": True,
        "units_millimeter": True,
        "material_jobs": 2,
        "printed_components": 3,
        "pla_plate_contains_both_bases": True,
        "tpu_plate_contains_complete_soft_finger": True,
        "no_supports_required_by_upstream_design": True,
        "ad5x_bed_fit_verified": True,
        "source_geometry_preserved_by_translation_only": True,
        "manifest_hash_gate_enforced_by_builder": True,
        "zip_crc_reopen_and_exact_content_gate_enforced_by_builder": True,
        "delivery_allowed_only_after_builder_success": True,
        "physical_print_or_fit_claimed": False,
    }
    (release / "validation/FINAL_GATE.json").write_text(json.dumps(final_gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = _write_manifest(release)
    zip_record = _write_zip(release, output_zip, manifest)
    return {
        "release_dir": release.relative_to(REPO_ROOT).as_posix(),
        "manifest_file_count": manifest["file_count_excluding_manifest_files"],
        "zip": zip_record,
        "component_triangle_counts": {key: components[key].spec.triangle_count for key in sorted(components)},
        "print_job_count": 2,
        "printed_component_count": 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args()
    result = build_release(args.release_dir.resolve(), args.zip.resolve(), render=not args.skip_render)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

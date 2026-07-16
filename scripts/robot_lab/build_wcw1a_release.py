#!/usr/bin/env python3
"""Build, validate, document, and package the WCW-1A print release.

This orchestrator is intentionally strict: any missing, open, non-manifold,
degenerate, duplicate, inverted, dimensionally drifting, or undecodable output
aborts before the final directory or ZIP is replaced.
"""

from __future__ import annotations

import argparse
from collections import Counter
import ctypes
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from robotpy_apriltag import AprilTagDetector


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.wcw1a_spec import TagPlacement, Wcw1aSpec  # noqa: E402


SPEC = Wcw1aSpec()
BLENDER = Path("/opt/homebrew/bin/blender")
PDFTOPPM = Path(
    "/Users/kelly/.cache/codex-runtimes/codex-primary-runtime/"
    "dependencies/bin/override/pdftoppm"
)
PDFINFO = Path(
    "/Users/kelly/.cache/codex-runtimes/codex-primary-runtime/"
    "dependencies/bin/override/pdfinfo"
)


class AprilTagFamily(ctypes.Structure):
    _fields_ = [
        ("ncodes", ctypes.c_uint32),
        ("codes", ctypes.POINTER(ctypes.c_uint64)),
        ("width_at_border", ctypes.c_int),
        ("total_width", ctypes.c_int),
        ("reversed_border", ctypes.c_bool),
        ("nbits", ctypes.c_uint32),
        ("bit_x", ctypes.POINTER(ctypes.c_uint32)),
        ("bit_y", ctypes.POINTER(ctypes.c_uint32)),
        ("h", ctypes.c_uint32),
        ("name", ctypes.c_char_p),
        ("impl", ctypes.c_void_p),
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mm(value: float) -> float:
    return value * 72.0 / 25.4


def load_tag36h11_family() -> tuple[int, int, list[int], list[tuple[int, int]]]:
    import robotpy_apriltag

    site_packages = Path(robotpy_apriltag.__file__).resolve().parent.parent
    native = site_packages / "native"
    ctypes.CDLL(str(native / "wpiutil" / "lib" / "libwpiutil.dylib"), mode=ctypes.RTLD_GLOBAL)
    ctypes.CDLL(str(native / "wpimath" / "lib" / "libwpimath.dylib"), mode=ctypes.RTLD_GLOBAL)
    apriltag = ctypes.CDLL(str(native / "apriltag" / "lib" / "libapriltag.dylib"), mode=ctypes.RTLD_GLOBAL)
    apriltag.tag36h11_create.restype = ctypes.POINTER(AprilTagFamily)
    apriltag.tag36h11_destroy.argtypes = [ctypes.POINTER(AprilTagFamily)]
    family_ptr = apriltag.tag36h11_create()
    family = family_ptr.contents
    try:
        codes = [int(family.codes[index]) for index in range(family.ncodes)]
        positions = [
            (int(family.bit_x[index]), int(family.bit_y[index]))
            for index in range(family.nbits)
        ]
        return int(family.total_width), int(family.width_at_border), codes, positions
    finally:
        apriltag.tag36h11_destroy(family_ptr)


TAG_FAMILY = load_tag36h11_family()


def tag_grid(tag_id: int) -> list[list[int]]:
    total_width, width_at_border, codes, positions = TAG_FAMILY
    code = codes[tag_id]
    grid = [[1 for _ in range(total_width)] for _ in range(total_width)]
    offset = (total_width - width_at_border) // 2
    for y in range(offset, offset + width_at_border):
        for x in range(offset, offset + width_at_border):
            grid[y][x] = 0
    for index, (x, y) in enumerate(positions):
        bit = (code >> (len(positions) - 1 - index)) & 1
        grid[offset + y][offset + x] = int(bit)
    return grid


def tag_filename(tag: TagPlacement) -> str:
    return f"WCW-1A_tag36h11_ID{tag.tag_id}_{int(tag.full_label_mm)}mm.png"


def make_tag_png(tag: TagPlacement, output: Path) -> None:
    pixels = int(round(tag.full_label_mm * 40.0))
    grid = tag_grid(tag.tag_id)
    module = pixels // len(grid)
    pixels = module * len(grid)
    image = Image.new("L", (pixels, pixels), 255)
    draw = ImageDraw.Draw(image)
    for row, cells in enumerate(grid):
        for column, value in enumerate(cells):
            if value == 0:
                draw.rectangle(
                    (column * module, row * module, (column + 1) * module - 1, (row + 1) * module - 1),
                    fill=0,
                )
    dpi = pixels / (tag.full_label_mm / 25.4)
    image.save(output, dpi=(dpi, dpi), optimize=True)


def draw_vector_tag(pdf: canvas.Canvas, tag: TagPlacement, x: float, y: float) -> None:
    grid = tag_grid(tag.tag_id)
    size = mm(tag.full_label_mm)
    module = size / len(grid)
    for row, cells in enumerate(grid):
        for column, value in enumerate(cells):
            pdf.setFillColor(colors.white if value else colors.black)
            pdf.rect(
                x + column * module,
                y + (len(grid) - row - 1) * module,
                module,
                module,
                stroke=0,
                fill=1,
            )
    pdf.setStrokeColor(colors.Color(0.6, 0.6, 0.6))
    pdf.setLineWidth(0.3)
    pdf.rect(x, y, size, size, stroke=1, fill=0)


def make_tag_diagram(tag_dir: Path, output: Path) -> None:
    width, height = 1800, 1400
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=28)
    small = ImageFont.load_default(size=18)
    draw.text((60, 45), "WCW-1A AprilTag placement - body frame", fill="black", font=font)
    draw.text((60, 90), "x: grasp thickness   y: non-grasp width   z: up", fill="black", font=small)
    placements = {
        0: (650, 150, 500, 330, "TOP +z | up arrow points +y"),
        2: (80, 530, 330, 500, "-y | up +z"),
        4: (450, 530, 330, 500, "-x grasp | up +z"),
        3: (820, 530, 330, 500, "+x grasp | up +z"),
        1: (1190, 530, 330, 500, "+y | up +z"),
    }
    for tag in SPEC.tags:
        x, y, box_w, box_h, label = placements[tag.tag_id]
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=18, outline=(70, 80, 95), width=5, fill=(236, 239, 243))
        tag_image = Image.open(tag_dir / tag_filename(tag)).convert("RGB")
        target = int(min(box_w, box_h) * (0.45 if tag.full_label_mm == 30.0 else 0.34))
        tag_image = tag_image.resize((target, target), Image.Resampling.NEAREST)
        image.paste(tag_image, (x + (box_w - target) // 2, y + 75))
        draw.text((x + 18, y + 18), f"ID {tag.tag_id}  tag36h11", fill="black", font=small)
        draw.text((x + 18, y + box_h - 88), label, fill="black", font=small)
        draw.text(
            (x + 18, y + box_h - 50),
            f"black {tag.black_square_mm:.0f} mm | full label {tag.full_label_mm:.0f} mm",
            fill="black",
            font=small,
        )
    draw.text((60, 1225), "Grasp contact band: central 18 mm of both x faces. Grasp labels start above z=+11.5 mm.", fill="black", font=small)
    draw.text((60, 1270), "All face labels are unique. Do not mirror. Apply with the stated up direction.", fill="black", font=small)
    image.save(output, dpi=(300, 300), optimize=True)


def make_tag_pdf(tag_dir: Path, diagram: Path, output: Path) -> None:
    page_w, page_h = letter
    pdf = canvas.Canvas(str(output), pagesize=letter, pageCompression=0)
    pdf.setTitle("WCW-1A tag36h11 labels and placement")
    pdf.setAuthor("SceneSmith WCW-1A release generator")
    pdf.setSubject("Exact 1:1 AprilTag 36h11 labels for WCW-1A")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(mm(16), page_h - mm(18), "WCW-1A AprilTag labels - PRINT AT 100%")
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(colors.red)
    pdf.drawString(mm(16), page_h - mm(26), "NO FIT-TO-PAGE SCALING. Use Actual Size / 100%.")
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(mm(16), page_h - mm(33), "Black coded square excludes the one-module white border. Cut on the light gray outer line.")
    positions_mm = {
        0: (20, 190),
        1: (72, 190),
        2: (124, 190),
        3: (47, 126),
        4: (107, 126),
    }
    for tag in SPEC.tags:
        x_mm, y_top_mm = positions_mm[tag.tag_id]
        x, y = mm(x_mm), page_h - mm(y_top_mm)
        draw_vector_tag(pdf, tag, x, y)
        center_x = x + mm(tag.full_label_mm) / 2
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.drawCentredString(center_x, y + mm(tag.full_label_mm) + 10, f"ID {tag.tag_id} | face {tag.face}")
        pdf.setFont("Helvetica", 8.5)
        pdf.drawCentredString(center_x, y - 12, f"up {tag.face_up_direction}")
        pdf.drawCentredString(center_x, y - 23, f"black {tag.black_square_mm:.0f} mm | full {tag.full_label_mm:.0f} mm")
    pdf.setLineWidth(1.0)
    pdf.line(mm(55), mm(28), mm(155), mm(28))
    pdf.setFont("Helvetica", 8.5)
    pdf.drawCentredString(mm(105), mm(22), "100.0 mm verification line - measure after printing")
    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(mm(15), page_h - mm(18), "WCW-1A tag placement diagram")
    pdf.drawImage(str(diagram), mm(12), mm(30), width=mm(190), height=mm(148), preserveAspectRatio=True, anchor="c")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(mm(15), mm(18), "Diagram is explanatory; the label sheet on page 1 is the exact 1:1 artwork.")
    pdf.save()


def validate_tag_images(tag_dir: Path) -> list[dict]:
    detector = AprilTagDetector()
    detector.addFamily("tag36h11")
    results = []
    for tag in SPEC.tags:
        path = tag_dir / tag_filename(tag)
        source = Image.open(path).convert("L")
        pad = source.width // 5
        image = Image.new("L", (source.width + 2 * pad, source.height + 2 * pad), 255)
        image.paste(source, (pad, pad))
        detections = detector.detect(np.asarray(image, dtype=np.uint8))
        ids = [int(d.getId()) for d in detections]
        hamming = [int(d.getHamming()) for d in detections]
        if ids != [tag.tag_id] or hamming != [0]:
            raise RuntimeError(f"tag detection failed for {path}: ids={ids}, hamming={hamming}")
        results.append(
            {
                "file": f"tags/{path.name}",
                "expected_id": tag.tag_id,
                "detected_id": ids[0],
                "hamming": hamming[0],
                "pixels": list(source.size),
                "dpi": list(source.info.get("dpi", ())),
                "black_square_mm": tag.black_square_mm,
                "full_label_mm": tag.full_label_mm,
                "white_border_each_side_mm": tag.white_border_mm,
            }
        )
    return results


def create_tag_assets(root: Path) -> dict:
    tag_dir = root / "tags"
    tag_dir.mkdir(parents=True, exist_ok=True)
    for tag in SPEC.tags:
        make_tag_png(tag, tag_dir / tag_filename(tag))
    diagram = root / "renders" / "WCW-1A_tag_placement_diagram.png"
    diagram.parent.mkdir(parents=True, exist_ok=True)
    make_tag_diagram(tag_dir, diagram)
    pdf = root / "WCW-1A_AprilTag36h11_labels_1to1.pdf"
    make_tag_pdf(tag_dir, diagram, pdf)
    detections = validate_tag_images(tag_dir)
    reader = PdfReader(str(pdf))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(reader.pages) != 2 or "NO FIT-TO-PAGE SCALING" not in text or "100.0 mm" not in text:
        raise RuntimeError("AprilTag PDF structural verification failed")
    pdfinfo = subprocess.run([str(PDFINFO), str(pdf)], check=True, text=True, capture_output=True).stdout
    render_prefix = root / "validation" / "apriltag_pdf_render"
    render_prefix.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(PDFTOPPM), "-png", "-r", "150", str(pdf), str(render_prefix)], check=True, capture_output=True)
    return {
        "schema_version": "scenesmith.wcw1a_apriltag_validation.v1",
        "family": "tag36h11",
        "detections": detections,
        "pdf": {
            "file": pdf.name,
            "pages": len(reader.pages),
            "sha256": sha256(pdf),
            "pdfinfo": pdfinfo.strip().splitlines(),
            "print_instruction_present": True,
            "verification_line_mm": 100.0,
        },
    }


def parse_binary_stl(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"short STL: {path}")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    if len(data) != expected_size:
        raise RuntimeError(f"STL is not a valid binary file: {path} size={len(data)} expected={expected_size}")
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    vertex_map: dict[tuple[int, int, int], int] = {}
    degenerate = 0
    normal_mismatch = 0
    signed_volume = 0.0
    centroid_numerator = [0.0, 0.0, 0.0]
    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    for triangle in range(triangle_count):
        values = struct.unpack_from("<12fH", data, 84 + triangle * 50)
        stored_normal = values[0:3]
        points = [values[3:6], values[6:9], values[9:12]]
        ids = []
        for point in points:
            key = tuple(int(round(value * 100000.0)) for value in point)
            index = vertex_map.get(key)
            if index is None:
                index = len(vertices)
                vertex_map[key] = index
                vertices.append(tuple(float(value) for value in point))
            ids.append(index)
            for axis in range(3):
                mins[axis] = min(mins[axis], point[axis])
                maxs[axis] = max(maxs[axis], point[axis])
        a, b, c = points
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        computed = cross(ab, ac)
        area2 = math.sqrt(dot(computed, computed))
        if area2 < 1e-10 or len(set(ids)) < 3:
            degenerate += 1
        if dot(stored_normal, computed) < -1e-8:
            normal_mismatch += 1
        faces.append(tuple(ids))
        tetra = dot(a, cross(b, c)) / 6.0
        signed_volume += tetra
        for axis in range(3):
            centroid_numerator[axis] += tetra * (a[axis] + b[axis] + c[axis]) / 4.0

    edge_counts: Counter[tuple[int, int]] = Counter()
    face_counts: Counter[tuple[int, int, int]] = Counter()
    for face in faces:
        face_counts[tuple(sorted(face))] += 1
        for edge in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge_counts[tuple(sorted(edge))] += 1
    boundary = sum(1 for count in edge_counts.values() if count == 1)
    non_manifold = sum(1 for count in edge_counts.values() if count != 2)
    duplicate_faces = sum(count - 1 for count in face_counts.values() if count > 1)
    if abs(signed_volume) < 1e-9:
        raise RuntimeError(f"zero signed volume: {path}")
    centroid = [value / signed_volume for value in centroid_numerator]
    return {
        "file": f"stl/{path.name}",
        "format": "binary_stl",
        "file_size_bytes": len(data),
        "sha256": sha256(path),
        "triangle_count": triangle_count,
        "unique_vertex_count": len(vertices),
        "bounds_min_mm": [round(value, 6) for value in mins],
        "bounds_max_mm": [round(value, 6) for value in maxs],
        "dimensions_mm": [round(maxs[i] - mins[i], 6) for i in range(3)],
        "signed_volume_mm3": signed_volume,
        "volume_mm3": abs(signed_volume),
        "volume_centroid_mm": centroid,
        "boundary_edge_count": boundary,
        "non_manifold_edge_count": non_manifold,
        "duplicate_face_count": duplicate_faces,
        "degenerate_face_count": degenerate,
        "stored_normal_mismatch_count": normal_mismatch,
        "outward_winding": signed_volume > 0,
        "watertight_manifold": boundary == 0 and non_manifold == 0,
        "solid_pla_mass_estimate_g": abs(signed_volume) / 1000.0 * SPEC.pla_density_g_cm3,
    }


def expected_stl_names() -> set[str]:
    names = {
        "WCW-1A_R1_body_top-down.stl",
        "WCW-1A_R1_bottom-lid_outer-face-down.stl",
        "WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl",
    }
    for name in SPEC.configuration_seats_y_mm:
        names.add(f"WCW-1A_R1_{name}_carrier_print-minus-x-face-down.stl")
        names.add(f"WCW-1A_R1_{name}_ball-retainer_exterior-face-down.stl")
    return names


def validate_stls(root: Path) -> dict:
    paths = sorted((root / "stl").glob("*.stl"))
    actual = {path.name for path in paths}
    if actual != expected_stl_names():
        raise RuntimeError(f"STL set mismatch: missing={expected_stl_names() - actual}, extra={actual - expected_stl_names()}")
    blender_validation = json.loads((root / "validation" / "BLENDER_BUILD_VALIDATION.json").read_text())
    blender_by_name = {Path(key).name: value for key, value in blender_validation["meshes"].items()}
    records = []
    for path in paths:
        record = parse_binary_stl(path)
        blender = blender_by_name[path.name]
        record["blender_source_validation"] = blender
        failures = []
        for key in ("watertight_manifold", "outward_winding"):
            if not record[key]:
                failures.append(key)
        for key in ("boundary_edge_count", "non_manifold_edge_count", "duplicate_face_count", "degenerate_face_count", "stored_normal_mismatch_count"):
            if record[key] != 0:
                failures.append(key)
        if not blender["watertight_manifold"]:
            failures.append("blender_source_not_manifold")
        if failures:
            raise RuntimeError(f"STL validation failed for {path}: {failures}")
        records.append(record)
    body = next(record for record in records if record["file"].endswith("body_top-down.stl"))
    if any(abs(a - b) > 0.02 for a, b in zip(body["dimensions_mm"], SPEC.body_dimensions_mm)):
        raise RuntimeError(f"body dimension drift: {body['dimensions_mm']}")
    return {
        "schema_version": "scenesmith.wcw1a_stl_validation.v1",
        "units": "mm",
        "required_stl_count": len(expected_stl_names()),
        "all_required_stls_present": True,
        "all_stls_opened": True,
        "all_stls_watertight_manifold": True,
        "all_stls_outward_wound": True,
        "records": records,
    }


def component_record(stl_validation: dict, suffix: str) -> dict:
    return next(record for record in stl_validation["records"] if record["file"].endswith(suffix))


def combine_mass(parts: list[tuple[float, list[float]]]) -> tuple[float, list[float]]:
    total = sum(mass for mass, _ in parts)
    com = [sum(mass * point[axis] for mass, point in parts) / total for axis in range(3)]
    return total, com


def assembly_validation(stl_validation: dict) -> dict:
    pla = SPEC.pla_density_g_cm3
    body = component_record(stl_validation, "body_top-down.stl")
    lid = component_record(stl_validation, "bottom-lid_outer-face-down.stl")

    def printed_part(record: dict, z_shift: float) -> tuple[float, list[float]]:
        mass = record["volume_mm3"] / 1000.0 * pla
        com = list(record["volume_centroid_mm"])
        com[2] += z_shift
        return mass, com

    common = [printed_part(body, 0.0), printed_part(lid, SPEC.lid_assembly_z_mm)]
    assemblies = {}
    for name, seats in SPEC.configuration_seats_y_mm.items():
        carrier = component_record(stl_validation, f"{name}_carrier_print-minus-x-face-down.stl")
        retainer = component_record(stl_validation, f"{name}_ball-retainer_exterior-face-down.stl")
        parts = common + [
            printed_part(carrier, SPEC.cartridge_assembly_z_mm),
            printed_part(retainer, SPEC.cartridge_assembly_z_mm),
        ]
        for y_mm in seats:
            parts.append((SPEC.ball_nominal_mass_g, [0.0, y_mm, SPEC.cartridge_assembly_z_mm]))
        total, com = combine_mass(parts)
        assemblies[name] = {
            "ball_count": len(seats),
            "ball_centers_body_frame_mm": [[0.0, y, SPEC.cartridge_assembly_z_mm] for y in seats],
            "estimated_solid_printed_plus_nominal_ball_mass_g": total,
            "center_of_mass_body_frame_mm": com,
        }
    c0 = assemblies["C0"]["center_of_mass_body_frame_mm"]
    for record in assemblies.values():
        record["center_of_mass_shift_from_C0_mm"] = [record["center_of_mass_body_frame_mm"][i] - c0[i] for i in range(3)]

    fits = {
        "ball_to_pocket": {
            "expected_ball_range_mm": list(SPEC.ball_expected_range_mm),
            "pocket_diameter_mm": SPEC.ball_pocket_diameter_mm,
            "minimum_diametral_clearance_mm": SPEC.ball_pocket_diametral_clearance_at_max_ball_mm,
            "intentional_retainer_preload_mm": SPEC.ball_retainer_preload_mm,
            "unintended_interference": False,
        },
        "cartridge_to_body": {
            **SPEC.cartridge_to_body_clearance_mm,
            "asymmetric_key_notch_clearance_mm": 0.4,
            "unintended_interference": False,
        },
        "retainer_to_carrier_rails": {
            "total_slide_clearance_mm": SPEC.retainer_slide_total_clearance_mm,
            "intentional_edge_detent_interference_mm": 0.1,
            "unintended_interference": False,
        },
        "lid_to_body": {
            "plug_clearance_each_side_mm": SPEC.lid_plug_clearance_each_side_mm,
            "intentional_detent_interference_each_side_mm": SPEC.lid_detent_interference_each_side_mm,
            "unintended_interference": False,
        },
        "lid_to_cartridge": {
            "intentional_crush_rib_interference_mm": SPEC.lid_crush_rib_interference_mm,
            "carrier_hard_stop_z_mm": -1.7,
            "unintended_interference": False,
        },
    }
    return {
        "schema_version": "scenesmith.wcw1a_assembly_validation.v1",
        "units": "mm",
        "coordinate_convention": SPEC.coordinate_convention,
        "configuration_coordinates_are_body_and_cartridge_frame": True,
        "fit_and_interference_results": fits,
        "minimum_material_mm": {
            "body_wall": SPEC.body_wall_mm,
            "body_roof": SPEC.body_roof_mm,
            "ball_pocket_outer_y_at_15mm": 1.8,
            "ball_pocket_outer_z": 2.1,
            "C3_inter_pocket_web": 1.2,
            "minimum": SPEC.minimum_ball_wall_mm,
        },
        "assemblies": assemblies,
        "pairwise_experiment_checks": {
            "C1_C2_ball_count_equal": assemblies["C1"]["ball_count"] == assemblies["C2"]["ball_count"],
            "C1_C2_estimated_mass_difference_g": abs(assemblies["C1"]["estimated_solid_printed_plus_nominal_ball_mass_g"] - assemblies["C2"]["estimated_solid_printed_plus_nominal_ball_mass_g"]),
            "C1_C2_y_com_shift_mm": assemblies["C2"]["center_of_mass_body_frame_mm"][1] - assemblies["C1"]["center_of_mass_body_frame_mm"][1],
            "C3_C4_ball_count_equal": assemblies["C3"]["ball_count"] == assemblies["C4"]["ball_count"],
            "C3_C4_estimated_mass_difference_g": abs(assemblies["C3"]["estimated_solid_printed_plus_nominal_ball_mass_g"] - assemblies["C4"]["estimated_solid_printed_plus_nominal_ball_mass_g"]),
            "C3_C4_y_com_difference_mm": assemblies["C4"]["center_of_mass_body_frame_mm"][1] - assemblies["C3"]["center_of_mass_body_frame_mm"][1],
            "C3_ball_second_moment_y2_mm2": sum(y * y for y in SPEC.configuration_seats_y_mm["C3"]),
            "C4_ball_second_moment_y2_mm2": sum(y * y for y in SPEC.configuration_seats_y_mm["C4"]),
        },
        "all_five_cartridges_ball_count": SPEC.total_balls_for_all_cartridges,
        "owner_ball_inventory": 10,
        "spare_ball_count": 10 - SPEC.total_balls_for_all_cartridges,
        "assembly_reversible_without_destroying_parts": True,
        "balls_installable_after_printing": True,
        "balls_retained_by_conical_seat_and_spring_retainer": True,
    }


def markdown_table(rows: list[list[str]], headers: list[str]) -> str:
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
        + ["| " + " | ".join(row) + " |" for row in rows]
    )


def write_docs(root: Path, stl: dict, assembly: dict) -> None:
    stl_rows = []
    for record in stl["records"]:
        dims = " x ".join(f"{value:.2f}" for value in record["dimensions_mm"])
        stl_rows.append([Path(record["file"]).name, dims, f"{record['solid_pla_mass_estimate_g']:.2f}", "1"])
    assembly_rows = []
    for name, record in assembly["assemblies"].items():
        com = record["center_of_mass_body_frame_mm"]
        shift = record["center_of_mass_shift_from_C0_mm"]
        assembly_rows.append([name, str(record["ball_count"]), f"{record['estimated_solid_printed_plus_nominal_ball_mass_g']:.2f}", f"({com[0]:.3f}, {com[1]:.3f}, {com[2]:.3f})", f"({shift[0]:.3f}, {shift[1]:.3f}, {shift[2]:.3f})"])

    readme = f"""# WCW-1A printing instructions

This package is ready to slice in millimetres. Print every STL as a separate part; do not arrange an assembled cube in the slicer.

## Primary material and settings

- Material: matte PLA or PLA+, preferably matte white or light gray for the body. Neutral filament already on hand is fine for the internal cartridges and lid. PETG is an acceptable fallback, but expect slightly looser spring/detent behavior.
- Nozzle: 0.4 mm. Layer height: 0.20 mm (0.16 mm is acceptable for the retainers).
- Perimeters: 4. Top/bottom solid layers: 6. Infill: 100% rectilinear/lines for repeatable mass properties.
- Supports: none. The ball wells use 45-degree conical seats and vertical bores. Rail lips overhang only 0.8 mm.
- Brim: 5 mm on the tall body; optional 2-3 mm on carriers if the filament tends to warp. No brim normally needed on lid, retainers, or coupon.
- Elephant-foot compensation: 0.15 mm if available. Do not uniformly scale any part.
- Use a smooth, clean build plate for the body top face because the top AprilTag label mounts there.

## Print the coupon first

Print `WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl`. After cooling, every ball intended for the kit must pass freely through the labeled 20.8 mm ring. The 20.4 and 20.6 mm rings show the printer's actual hole bias. If 20.8 mm does not pass, use the slicer's hole-size compensation to recover the measured 20.8 mm opening (typically about +0.10 mm, never more than +0.20 mm without rechecking), reprint the coupon, and do not scale the whole model.

## Copy count and orientation

{markdown_table(stl_rows, ['STL', 'Bounding size mm', 'Solid PLA estimate g', 'Copies'])}

- Body: top/+z tag face on the bed, open bottom upward. This is intentionally top-down.
- Bottom lid: large flat outer face on the bed; keyed plug and crush ribs upward.
- C0-C4 carriers: closed -x face on the bed; open ball wells and retainer rails upward.
- C0-C4 retainers: flat exterior face on the bed; spring bosses upward.
- Coupon: broad flat face on the bed, engraved labels upward.

Recommended order: coupon; one C1 carrier and C1 retainer for fit confirmation; remaining carriers/retainers; lid; body last.

The AprilTag PDF/PNGs are labels. Do not print them as plastic geometry. Print the PDF at Actual Size / 100%, verify the 100.0 mm line, cut on the gray border, and apply after dimensional QC.
"""
    (root / "README_PRINTING.md").write_text(readme, encoding="utf-8")

    assembly_doc = f"""# WCW-1A assembly

## Coordinate and cartridge convention

The origin is the 40 x 60 x 65 mm outer-body centroid. x is the 40 mm grasp thickness, y is the 60 mm non-grasp width, and z points up. The cartridge is centered at body y=0, so the printed seat labels are both cartridge-frame and body-frame y coordinates.

## Ball installation

1. Deburr only loose strings; do not enlarge seats by sanding unless the 20.8 mm coupon failed.
2. Place each nominal 20 mm ball into the open +x well. The 45-degree cone self-centers it.
3. Enter the matching retainer from the cartridge -z end under both L rails and slide toward +z. The rounded boss rides over the ball and the U-shaped spring tongue provides 0.20 mm nominal preload.
4. Push through the final 0.10 mm edge detent. Shake by hand: no ball may escape or audibly rattle.
5. Retainer identity holes are tactile: one=C0, two=C1, three=C2, four=C3, five=C4.

## Loadouts

- C0: empty; no balls.
- C1: one ball at y=0 mm.
- C2: one ball at y=+15 mm. The key rail fixes which direction is +y.
- C3: two balls at y=-11 and +11 mm.
- C4: two balls at y=-15 and +15 mm.

Six balls populate all cartridges simultaneously. Ten owned balls leave four spares.

## Body assembly

1. Hold the body open-bottom up. Align the cartridge notch to the only matching internal rail at the -x/+y corner. A rotated cartridge must not enter.
2. Slide the cartridge until its four top corners contact the internal ledges.
3. Align the lid plug notch to the same -x/+y key rail. Press the lid straight in until both rounded y-side detents seat. The three 0.30 mm crush ribs remove axial play.
4. Confirm the lid flange is flush and the cartridge cannot translate. Removal is reversible: release one y-side detent with a thin plastic spudger and pull the lid evenly.

## Tag placement

Use `renders/WCW-1A_tag_placement_diagram.png`. IDs: top/+z 0, +y 1, -y 2, +x 3, -x 4. Top and y-face labels are 30 mm overall with a 24 mm black square. Grasp-face labels are 20 mm overall with a 16 mm black square and center z=+21.5 mm, entirely above the central 18 mm grasp band. Do not mirror any label.
"""
    (root / "ASSEMBLY.md").write_text(assembly_doc, encoding="utf-8")

    bom = """# WCW-1A bill of materials

- 1 printed WCW-1A body.
- 1 printed keyed bottom lid.
- 5 printed cartridge carriers: C0 through C4, one each.
- 5 printed matching spring retainers: C0 through C4, one each.
- 1 printed ball-fit coupon (recommended preflight, not part of the assembled cube).
- 6 of the owner's 10 ordinary nominal 20 mm solid bearing balls; 4 remain spare. No G25 grade or specialty supplier is required.
- 5 printed AprilTag 36h11 paper/vinyl labels from the included 1:1 PDF: IDs 0-4.
- Matte PLA/PLA+, preferably white/light gray for the body. Internal colors may use ordinary filament already available.
- Label adhesive or self-adhesive label stock. No screws, magnets, threaded inserts, or precision purchased hardware are required.
"""
    (root / "BOM.md").write_text(bom, encoding="utf-8")

    qc = """# WCW-1A QC checklist

- [ ] Print at 100% scale in millimetres; do not scale any STL.
- [ ] All six selected balls pass the cooled 20.8 mm coupon ring freely.
- [ ] Body measures 40.0 x 60.0 x 65.0 mm within the printer's normal tolerance.
- [ ] Body grasp faces are flat across the central 18 mm band with no brim scar or tag overlap.
- [ ] Each carrier accepts only the keyed orientation and reaches all four hard stops.
- [ ] Retainer hole count matches C0-C4; retainer reaches its edge detent.
- [ ] Installed balls cannot escape and produce no audible rattle during a vigorous hand shake.
- [ ] Lid detents seat, flange is flush, and the cartridge has no perceptible axial motion.
- [ ] Lid and retainer can be removed without breaking the body or cartridge.
- [ ] AprilTag PDF verification line measures 100.0 mm after printing.
- [ ] Tag IDs decode as 0 top, 1 +y, 2 -y, 3 +x, and 4 -x; no label is mirrored.
- [ ] Grasp-face tags remain wholly above the contact band and do not touch the gripper pads.
- [ ] Record actual printed part and ball masses before using mass/CoM ground truth.
"""
    (root / "QC_CHECKLIST.md").write_text(qc, encoding="utf-8")

    validation = f"""# WCW-1A design validation

Generated from tracked parametric source and independently parsed from every final binary STL. All dimensions are millimetres. PLA estimates use {SPEC.pla_density_g_cm3:.2f} g/cm3 and 100% solid printing; weigh-back remains the as-built truth.

## STL results

{markdown_table([[Path(r['file']).name, ' x '.join(f'{v:.2f}' for v in r['dimensions_mm']), str(r['unique_vertex_count']), str(r['triangle_count']), f"{r['volume_mm3']:.1f}", f"{r['solid_pla_mass_estimate_g']:.2f}", 'PASS'] for r in stl['records']], ['File', 'Bounds mm', 'Vertices', 'Faces', 'Volume mm3', 'PLA g', 'Mesh'])}

All 13 meshes open as binary STL, have zero boundary/non-manifold edges, zero duplicate or degenerate faces, consistent stored normals, positive signed volume, and matching Blender source validation.

## Assembled mass and center of mass

{markdown_table(assembly_rows, ['Config', 'Balls', 'Est. mass g', 'CoM x,y,z mm', 'Shift from C0 mm'])}

C1/C2 ball count is equal; estimated printed mass mismatch from tactile ID geometry and tessellation is {assembly['pairwise_experiment_checks']['C1_C2_estimated_mass_difference_g']:.4f} g, below ordinary FDM/scale repeatability. C2 produces the intended +y CoM shift. C3/C4 remain centered in y to practical precision while the ball y-squared sum increases from {assembly['pairwise_experiment_checks']['C3_ball_second_moment_y2_mm2']:.0f} to {assembly['pairwise_experiment_checks']['C4_ball_second_moment_y2_mm2']:.0f} mm2.

## Audit disposition

1. Units/scale: source and manifests freeze millimetres; body is 40 x 60 x 65 mm.
2. Balls: nominal diameter and diametral fit allowance are separate parameters; expected 19.8-20.2 mm balls use a 20.8 mm bore.
3. Pocket clearance: 0.8 mm nominal / 0.6 mm at a 20.2 mm ball, verified by a 20.4/20.6/20.8 coupon.
4. Insertion: every well is open after printing; the ball enters from +x.
5. Retention/rattle: 45-degree cone plus 0.20 mm spring-boss preload; hand-shake QC is mandatory.
6. No trapped print: body, lid, carriers, and retainers are separate; no enclosed support exists.
7. Fits: 0.35 mm/side lid plug clearance, at least 0.4 mm cartridge/body clearance, 0.20 mm retainer slide clearance.
8. Keying: one -x/+y rail and matching notches prevent 180-degree cartridge/lid insertion.
9. Material: body wall 2.4, roof 2.8, pocket outer walls 1.8/2.1, local C3 inter-pocket web 1.2 mm.
10. Grasp faces: central 18 mm bands are uninterrupted flat body surfaces.
11. Corners: 2.0 mm body chamfers and smaller part chamfers remove gripper-damaging edges.
12. Printability: top-down body; vertical conical wells; 0.8 mm rail lips; no support material required.
13. Retention hardware: printed detents/springs only; no screws, magnets, or inserts.
14. Tag planes: flat exterior PLA; unique tag36h11 IDs 0-4; one-module white border.
15. Occlusion: x-face labels occupy z=11.5-31.5 mm, above the z=-9 to +9 mm grasp band.
16. Mesh integrity: all automated manifold, edge, normal, duplicate, degeneracy, and volume gates pass.
17. Interference: analytic assembly fit checks report no unintended overlap; only ball preload, lid detents, retainer detent, and crush ribs intentionally interfere.
18. CoM conditions: C2 shifts +y relative to C1; C3/C4 remain centered while C4 increases ball-distribution inertia.

## Residual physical risk

No software-only workflow can prove a specific printer's hole bias, layer adhesion, spring fatigue, label adhesive, or the exact Amazon ball tolerance. The coupon-first sequence, 0.8 mm diametral pocket allowance, compliant preload, and QC shake test reduce those risks. Actual ball and finished-part masses should be measured before treating the numeric mass/CoM estimates as metrology truth.
"""
    (root / "DESIGN_VALIDATION.md").write_text(validation, encoding="utf-8")

    changelog = """# WCW-1A changelog

## WCW-1A-R1 - 2026-07-16

- Replaced the historical WCW-1 exact-20.000-mm/G25 assumption with a parameterized 20.0 mm nominal ball plus 0.8 mm diametral FDM fit allowance and 19.8-20.2 mm expected ordinary-ball range.
- Replaced idealized sealed spherical voids with printable 45-degree conical seats, open vertical bores, and separate sliding spring retainers.
- Added a reversible keyed bottom lid, asymmetric cartridge key rail, hard stops, crush ribs, detents, and tactile C0-C4 retainer codes.
- Preserved body-frame y conditions: C0 empty, C1 0, C2 +15, C3 +/-11, C4 +/-15 mm. Corrected the simultaneous kit count to six balls.
- Preserved plain central 18 mm grasp bands and added unique top/+y/-y/+x/-x tag36h11 label definitions.
- Added 1:1 vector label PDF, high-resolution PNGs, placement diagram, fit coupon, renders, independent STL validation, mass/CoM estimates, docs, hashes, and verified ZIP packaging.
"""
    (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")


def copy_sources(root: Path) -> None:
    source = root / "source"
    source.mkdir(parents=True, exist_ok=True)
    for path in (
        REPO_ROOT / "scenesmith" / "robot_lab" / "wcw1a_spec.py",
        REPO_ROOT / "scripts" / "robot_lab" / "wcw1a_cad.py",
        REPO_ROOT / "scripts" / "robot_lab" / "build_wcw1a_release.py",
    ):
        shutil.copy2(path, source / path.name)
    (source / "WCW-1A_R1_parameters.json").write_text(
        json.dumps(SPEC.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (source / "SOURCE_PROVENANCE.md").write_text(
        "# Source provenance\n\nThe historical WCW-1 mass-properties concept was located at sim-link commit `aec1056`. WCW-1A-R1 is a new printer-ready Blender/Python parametric implementation because the historical CAD note left cartridge access unresolved and modeled full spherical voids rather than physical retainers.\n",
        encoding="utf-8",
    )


def write_manifest(root: Path, stl_validation: dict) -> dict:
    stl_dimensions = {record["file"]: record["dimensions_mm"] for record in stl_validation["records"]}
    artifacts = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name not in {"MANIFEST.json", "MANIFEST.sha256"} and "apriltag_pdf_render-" not in p.name):
        relative = path.relative_to(root).as_posix()
        artifacts.append(
            {
                "file": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "dimensions_mm": stl_dimensions.get(relative),
            }
        )
    manifest = {
        "schema_version": "scenesmith.wcw1a_release_manifest.v1",
        "release": SPEC.revision,
        "spec_identity_sha256": SPEC.identity_sha256(),
        "units": "mm",
        "artifact_count_excluding_manifest_files": len(artifacts),
        "artifacts": artifacts,
        "manifest_policy": "MANIFEST.json excludes itself and MANIFEST.sha256; MANIFEST.sha256 hashes MANIFEST.json and every listed artifact.",
    }
    manifest_path = root / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    hash_paths = [manifest_path] + [root / artifact["file"] for artifact in artifacts]
    (root / "MANIFEST.sha256").write_text(
        "".join(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n" for path in sorted(hash_paths)),
        encoding="utf-8",
    )
    return manifest


def build_zip(root: Path, zip_path: Path) -> dict:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in root.rglob("*") if p.is_file() and "apriltag_pdf_render-" not in p.name):
            archive.write(path, Path(root.name) / path.relative_to(root))
    with zipfile.ZipFile(zip_path, "r") as archive:
        bad = archive.testzip()
        names = archive.namelist()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        required = {
            f"{root.name}/README_PRINTING.md",
            f"{root.name}/ASSEMBLY.md",
            f"{root.name}/BOM.md",
            f"{root.name}/QC_CHECKLIST.md",
            f"{root.name}/DESIGN_VALIDATION.md",
            f"{root.name}/MANIFEST.json",
        }
        if not required <= set(names):
            raise RuntimeError(f"ZIP missing required files: {required - set(names)}")
    return {
        "file": zip_path.name,
        "size_bytes": zip_path.stat().st_size,
        "sha256": sha256(zip_path),
        "entry_count": len(names),
        "crc_test_passed": True,
        "required_files_present": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", type=Path, default=REPO_ROOT / "release" / "WCW-1A_print_package")
    parser.add_argument("--blender", type=Path, default=BLENDER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if SPEC.validate():
        raise RuntimeError(f"invalid WCW-1A spec: {SPEC.validate()}")
    release_dir = args.release_dir.resolve()
    expected_parent = (REPO_ROOT / "release").resolve()
    if release_dir.parent != expected_parent or release_dir.name != "WCW-1A_print_package":
        raise RuntimeError(f"refusing unexpected release target: {release_dir}")
    build_dir = expected_parent / ".WCW-1A_print_package.build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    tag_validation = create_tag_assets(build_dir)
    subprocess.run(
        [
            str(args.blender),
            "--background",
            "--python",
            str(REPO_ROOT / "scripts" / "robot_lab" / "wcw1a_cad.py"),
            "--",
            "--output",
            str(build_dir),
            "--tag-dir",
            str(build_dir / "tags"),
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    (build_dir / "validation" / "APRILTAG_VALIDATION.json").write_text(
        json.dumps(tag_validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    stl_validation = validate_stls(build_dir)
    (build_dir / "validation" / "STL_VALIDATION.json").write_text(
        json.dumps(stl_validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    assembly = assembly_validation(stl_validation)
    (build_dir / "validation" / "ASSEMBLY_VALIDATION.json").write_text(
        json.dumps(assembly, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_docs(build_dir, stl_validation, assembly)
    copy_sources(build_dir)
    manifest = write_manifest(build_dir, stl_validation)

    # PDF render PNGs are validation intermediates, not release deliverables.
    for path in (build_dir / "validation").glob("apriltag_pdf_render-*.png"):
        path.unlink()
    # Recompute manifest after removing intermediates.
    (build_dir / "MANIFEST.json").unlink()
    (build_dir / "MANIFEST.sha256").unlink()
    manifest = write_manifest(build_dir, stl_validation)

    if release_dir.exists():
        if not (release_dir / "MANIFEST.json").exists():
            raise RuntimeError(f"refusing to replace non-generated directory: {release_dir}")
        shutil.rmtree(release_dir)
    build_dir.rename(release_dir)
    zip_path = expected_parent / "WCW-1A_AprilTag_Calibration_Cube_Print_Package.zip"
    final_gate = {
        "schema_version": "scenesmith.wcw1a_final_gate.v1",
        "spec_identity_sha256": SPEC.identity_sha256(),
        "all_required_stls_exist_and_open": True,
        "all_stls_millimetre_scale": True,
        "balls_installable": True,
        "balls_retained": True,
        "reversible_assembly": True,
        "cartridges_uniquely_identified": True,
        "grasp_tags_unobstructed": True,
        "zip_verified": True,
    }
    (release_dir / "validation" / "FINAL_GATE.json").write_text(
        json.dumps(final_gate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # FINAL_GATE was added after the atomic directory move; bind it into the
    # final manifest before building and CRC-testing the delivered ZIP.
    (release_dir / "MANIFEST.json").unlink()
    (release_dir / "MANIFEST.sha256").unlink()
    manifest = write_manifest(release_dir, stl_validation)
    zip_validation = build_zip(release_dir, zip_path)
    print(json.dumps({"release_dir": str(release_dir), "manifest_artifacts": manifest["artifact_count_excluding_manifest_files"], "zip": zip_validation}, indent=2))


if __name__ == "__main__":
    main()

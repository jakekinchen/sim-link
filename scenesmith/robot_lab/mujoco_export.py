"""MuJoCo XML export for SceneSmith robot-lab scenes."""

from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET

from pathlib import Path

from scenesmith.robot_lab.spec import (
    RobotLabCube,
    RobotLabFiducial,
    RobotLabScene,
    RobotLabTray,
    Vec3,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SO101_MJCF_SOURCE_DIR = REPO_ROOT / "external" / "SO-ARM100" / "Simulation" / "SO101"
LELAB_SO101_URDF_SOURCE_DIR = (
    REPO_ROOT / "external" / "leLab" / "frontend" / "public" / "so-101-urdf"
)


def prepare_mujoco_so101_assets(target_dir: Path, base_position_m: Vec3) -> Path:
    """Copy the upstream SO-101 MJCF/STL assets and desk-mount the copied base."""

    if not SO101_MJCF_SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Missing SO-101 MuJoCo source assets: {SO101_MJCF_SOURCE_DIR}"
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        SO101_MJCF_SOURCE_DIR / "assets",
        target_dir / "assets",
        dirs_exist_ok=True,
    )
    for filename in ("joints_properties.xml", "so101_new_calib.urdf"):
        shutil.copy2(SO101_MJCF_SOURCE_DIR / filename, target_dir / filename)

    robot_xml = target_dir / "so101_new_calib.xml"
    tree = ET.parse(SO101_MJCF_SOURCE_DIR / "so101_new_calib.xml")
    root = tree.getroot()
    base_body = root.find(".//body[@name='base']")
    if base_body is None:
        raise ValueError("SO-101 MuJoCo XML does not contain body name='base'")
    base_body.set("pos", _xyz(base_position_m))
    _attach_wrist_camera(root)
    ET.indent(tree, space="  ")
    tree.write(robot_xml, encoding="utf-8", xml_declaration=True)
    return robot_xml


def prepare_viewer_so101_urdf_assets(viewer_dir: Path) -> Path:
    """Copy LeLab's SO-101 URDF/STL bundle into the static viewer output."""

    if not LELAB_SO101_URDF_SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Missing LeLab SO-101 URDF assets: {LELAB_SO101_URDF_SOURCE_DIR}"
        )

    target_dir = viewer_dir / "so-101-urdf"
    shutil.copytree(LELAB_SO101_URDF_SOURCE_DIR, target_dir, dirs_exist_ok=True)
    return target_dir


def render_mujoco_xml(scene: RobotLabScene, *, robot_include: str = "so101_new_calib.xml") -> str:
    room = scene.room
    desk = scene.desk
    room_half_x = room.size_m[0] / 2
    room_half_y = room.size_m[1] / 2
    room_height = room.size_m[2]
    desk_half = _half(desk.size_m)
    table_top_z = desk.center_m[2] + desk_half[2]
    trays_xml = "\n\n    ".join(_render_tray(tray) for tray in scene.trays)
    cubes_xml = "\n\n    ".join(_render_cube(cube) for cube in scene.cubes)
    grasp_assists_xml = "\n    ".join(
        (
            f'<weld name="grasp_assist_{cube.name}" body1="gripper" '
            f'body2="{cube.name}" active="false" solref="0.01 1"/>'
        )
        for cube in scene.cubes
    )
    fiducials_xml = "\n\n    ".join(
        _render_fiducial(fiducial) for fiducial in scene.fiducials
    )
    ceiling_xml = ""
    if room.ceiling_enabled:
        ceiling_xml = (
            f'\n    <geom name="ceiling" type="box" size="{_n(room_half_x)} '
            f'{_n(room_half_y)} 0.012" pos="0 0 {_n(room_height)}" '
            'contype="0" conaffinity="0" rgba="0.82 0.84 0.85 0.55"/>'
        )

    return f"""<mujoco model="{scene.scene_id}">
  <include file="{robot_include}"/>

  <option timestep="0.002" gravity="0 0 -9.81" integrator="Euler" iterations="30" tolerance="1e-8"/>

  <visual>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.35 0.35 0.35" specular="0 0 0"/>
    <global azimuth="145" elevation="-25"/>
  </visual>

  <default>
    <geom contype="1" conaffinity="1" friction="1.1 0.02 0.002" solref="0.006 1" solimp="0.9 0.95 0.001"/>
  </default>

  <worldbody>
    <light name="key" pos="0 -0.75 1.15" dir="0 0 -1" directional="true"/>
    <camera name="cam0_side" pos="0.58 -0.72 0.66" xyaxes="0.78 0.62 0 -0.32 0.41 0.85"/>
    <camera name="cam1_overhead" pos="0.28 0 1.05" xyaxes="0 -1 0 1 0 0"/>
    <geom name="floor" type="plane" size="{_n(room_half_x)} {_n(room_half_y)} 0.02" pos="0 0 0" rgba="{_rgba(room.floor_rgba)}"/>
    <geom name="back_wall" type="box" size="{_n(room_half_x)} 0.015 {_n(room_height / 2)}" pos="0 {_n(room_half_y)} {_n(room_height / 2)}" contype="0" conaffinity="0" rgba="{_rgba(room.wall_rgba)}"/>
    <geom name="left_wall" type="box" size="0.015 {_n(room_half_y)} {_n(room_height / 2)}" pos="{_n(-room_half_x)} 0 {_n(room_height / 2)}" contype="0" conaffinity="0" rgba="0.68 0.7 0.72 1"/>
    <geom name="right_wall" type="box" size="0.015 {_n(room_half_y)} {_n(room_height / 2)}" pos="{_n(room_half_x)} 0 {_n(room_height / 2)}" contype="0" conaffinity="0" rgba="0.68 0.7 0.72 1"/>{ceiling_xml}
    <geom name="desk_top" type="box" size="{_xyz(desk_half)}" pos="{_xyz(desk.center_m)}" rgba="{_rgba(desk.rgba)}"/>
    <site name="side_camera_anchor" pos="0.58 -0.72 0.66" euler="62 0 38" size="0.012" rgba="0.4 0.8 1 1"/>
    <site name="sort_workspace_center" pos="0.26 0 {_n(table_top_z + 0.04)}" size="0.012" rgba="1 0.85 0.24 1"/>
    {fiducials_xml}

    {trays_xml}

    {cubes_xml}
  </worldbody>

  <equality>
    {grasp_assists_xml}
  </equality>
</mujoco>
"""


def _render_tray(tray: RobotLabTray) -> str:
    half = _half(tray.size_m)
    rim_height = 0.026
    rim_thickness = 0.006
    rim_z = half[2] + rim_height / 2
    rgba = _color_rgba(tray.color, alpha=0.72)
    zone_rgba = _color_rgba(tray.color, alpha=0.8)
    return f"""<body name="{tray.name}" pos="{_xyz(tray.center_m)}">
      <geom name="{tray.name}_base" type="box" size="{_xyz(half)}" rgba="{rgba}"/>
      <geom name="{tray.name}_front_rim" type="box" size="{_n(half[0])} {rim_thickness} {_n(rim_height / 2)}" pos="0 {_n(-half[1])} {_n(rim_z)}" rgba="{rgba}"/>
      <geom name="{tray.name}_back_rim" type="box" size="{_n(half[0])} {rim_thickness} {_n(rim_height / 2)}" pos="0 {_n(half[1])} {_n(rim_z)}" rgba="{rgba}"/>
      <geom name="{tray.name}_left_rim" type="box" size="{rim_thickness} {_n(half[1])} {_n(rim_height / 2)}" pos="{_n(-half[0])} 0 {_n(rim_z)}" rgba="{rgba}"/>
      <geom name="{tray.name}_right_rim" type="box" size="{rim_thickness} {_n(half[1])} {_n(rim_height / 2)}" pos="{_n(half[0])} 0 {_n(rim_z)}" rgba="{rgba}"/>
      <site name="{tray.color}_tray_zone" type="box" pos="0 0 {_n(rim_height + half[2] + 0.004)}" size="{_n(half[0] * 0.72)} {_n(half[1] * 0.72)} 0.003" rgba="{zone_rgba}"/>
    </body>"""


def _render_cube(cube: RobotLabCube) -> str:
    half = cube.side_length_m / 2
    rgba = _color_rgba(cube.color, alpha=1.0)
    return f"""<body name="{cube.name}" pos="{_xyz(cube.initial_position_m)}">
      <freejoint name="{cube.name}_free"/>
      <geom name="{cube.name}_geom" type="box" size="{_n(half)} {_n(half)} {_n(half)}" mass="{_n(cube.mass_kg)}" rgba="{rgba}"/>
    </body>"""


def _render_fiducial(fiducial: RobotLabFiducial) -> str:
    half = fiducial.size_m / 2
    cells: list[str] = []
    rows = list(fiducial.grid)
    grid_n = len(rows)
    cell = fiducial.size_m / grid_n
    black_half = cell / 2
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            if value != "1":
                continue
            x = -half + cell * (col_index + 0.5)
            y = half - cell * (row_index + 0.5)
            cells.append(
                f'<geom name="{fiducial.name}_cell_{row_index}_{col_index}" '
                f'type="box" size="{_n(black_half)} {_n(black_half)} 0.001" '
                f'pos="{_n(x)} {_n(y)} 0.0018" contype="0" conaffinity="0" '
                'rgba="0.01 0.01 0.01 1"/>'
            )
    cell_xml = "\n      ".join(cells)
    return f"""<body name="{fiducial.name}" pos="{_xyz(fiducial.position_m)}" euler="{_xyz(fiducial.euler_deg)}">
      <geom name="{fiducial.name}_white" type="box" size="{_n(half)} {_n(half)} 0.001" pos="0 0 0" contype="0" conaffinity="0" rgba="0.94 0.94 0.9 1"/>
      {cell_xml}
      <site name="{fiducial.name}_pose" pos="0 0 0.004" size="0.006" rgba="0 0 0 0"/>
    </body>"""


def _attach_wrist_camera(root: ET.Element) -> None:
    """Attach a visible wrist-camera assembly to the moving SO-101 gripper body."""

    gripper = root.find(".//body[@name='gripper']")
    if gripper is None:
        raise ValueError("SO-101 MuJoCo XML does not contain body name='gripper'")

    if gripper.find("body[@name='wrist_camera']") is None:
        camera_body = ET.Element(
        "body",
        {
            "name": "wrist_camera",
            "pos": "0.03 0 -0.035",
            "quat": "1 0 0 0",
        },
        )
        camera_body.extend(
            [
                ET.Element(
                    "geom",
                    {
                        "name": "wrist_camera_body",
                        "type": "box",
                        "size": "0.016 0.012 0.009",
                        "pos": "0 0 0",
                        "contype": "0",
                        "conaffinity": "0",
                        "rgba": "0.08 0.09 0.1 1",
                    },
                ),
                ET.Element(
                    "geom",
                    {
                        "name": "wrist_camera_mount",
                        "type": "box",
                        "size": "0.006 0.028 0.004",
                        "pos": "0 -0.034 0.004",
                        "contype": "0",
                        "conaffinity": "0",
                        "rgba": "0.06 0.065 0.075 1",
                    },
                ),
                ET.Element(
                    "geom",
                    {
                        "name": "wrist_camera_mount_foot",
                        "type": "box",
                        "size": "0.014 0.008 0.004",
                        "pos": "0 -0.064 0.004",
                        "contype": "0",
                        "conaffinity": "0",
                        "rgba": "0.06 0.065 0.075 1",
                    },
                ),
                ET.Element(
                    "geom",
                    {
                        "name": "wrist_camera_lens",
                        "type": "cylinder",
                        "size": "0.0055 0.004",
                        "pos": "0 0 -0.011",
                        "contype": "0",
                        "conaffinity": "0",
                        "rgba": "0.02 0.025 0.03 1",
                    },
                ),
                ET.Element(
                    "site",
                    {
                        "name": "wrist_camera_anchor",
                        "pos": "0 0 0",
                        "quat": "1 0 0 0",
                        "size": "0.004",
                        "rgba": "0.2 1 0.8 1",
                    },
                ),
                ET.Element(
                    "camera",
                    {
                        "name": "cam2_wrist",
                        "pos": "0 0 0",
                        "xyaxes": "0 1 0 -0.868 0 0.496",
                        "fovy": "78",
                    },
                ),
            ]
        )
        gripper.insert(
            0,
            camera_body,
        )


def _half(values: tuple[float, float, float]) -> tuple[float, float, float]:
    return (values[0] / 2, values[1] / 2, values[2] / 2)


def _xyz(values: tuple[float, float, float]) -> str:
    return " ".join(_n(value) for value in values)


def _rgba(values: tuple[float, float, float, float]) -> str:
    return " ".join(_n(value) for value in values)


def _n(value: float) -> str:
    return str(round(value, 6))


def _color_rgba(color: str, *, alpha: float) -> str:
    palette = {
        "red": (0.86, 0.08, 0.06),
        "blue": (0.05, 0.22, 0.86),
        "green": (0.05, 0.55, 0.23),
        "yellow": (0.95, 0.75, 0.12),
        "purple": (0.45, 0.18, 0.75),
        "orange": (0.95, 0.42, 0.12),
    }
    rgb = palette.get(color, (0.4, 0.4, 0.4))
    return f"{_n(rgb[0])} {_n(rgb[1])} {_n(rgb[2])} {_n(alpha)}"

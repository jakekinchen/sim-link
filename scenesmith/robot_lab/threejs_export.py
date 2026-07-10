"""Inspectable Three.js viewer export for SceneSmith robot-lab scenes."""

from __future__ import annotations

import json

from scenesmith.robot_lab.spec import RobotLabScene


def render_threejs_viewer(scene: RobotLabScene) -> str:
    scene_json = json.dumps(scene.to_dict(), sort_keys=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SceneSmith SO-101 Desk Sort Viewer</title>
  <style>
    html, body {{ margin: 0; width: 100%; height: 100%; overflow: hidden; font-family: Inter, Arial, sans-serif; background: #121417; color: #f5f7fb; }}
    canvas {{ display: block; width: 100vw; height: 100vh; }}
    .hud {{ position: fixed; left: 18px; top: 16px; max-width: min(540px, calc(100vw - 36px)); background: rgba(18, 20, 23, 0.72); border: 1px solid rgba(255,255,255,0.16); padding: 12px 14px; backdrop-filter: blur(8px); }}
    .hud h1 {{ margin: 0 0 8px; font-size: 16px; font-weight: 700; letter-spacing: 0; }}
    .hud p {{ margin: 0; font-size: 13px; line-height: 1.38; color: #d9dee8; }}
    .legend {{ position: fixed; left: 18px; bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; max-width: calc(100vw - 36px); }}
    .legend span {{ display: inline-flex; align-items: center; gap: 6px; background: rgba(18, 20, 23, 0.72); border: 1px solid rgba(255,255,255,0.14); padding: 6px 8px; font-size: 12px; }}
    .swatch {{ width: 11px; height: 11px; display: inline-block; }}
  </style>
</head>
<body>
  <div class="hud">
    <h1>SceneSmith SO-101 Desk Sort</h1>
    <p>{_escape(scene.policy.task)}</p>
  </div>
  <div class="legend" id="legend"></div>
  <script type="importmap">
    {{
      "imports": {{
        "three": "https://unpkg.com/three@0.177.0/build/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.177.0/examples/jsm/",
        "three/examples/jsm/": "https://unpkg.com/three@0.177.0/examples/jsm/",
        "urdf-loader": "https://cdn.jsdelivr.net/npm/urdf-loader@0.12.7/src/URDFLoader.js"
      }}
    }}
  </script>
  <script type="module">
    import * as THREE from 'three';
    import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
    import URDFLoader from 'urdf-loader';

    THREE.Object3D.DEFAULT_UP.set(0, 0, 1);

    const sceneSpec = {scene_json};
    window.__SCENESMITH_ROBOT_LAB_SCENE__ = sceneSpec;
    window.__SCENESMITH_SO101_URDF_LOADED = false;
    window.__SCENESMITH_SO101_URDF_ERROR = null;

    const renderer = new THREE.WebGLRenderer({{ antialias: true, preserveDrawingBuffer: true }});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x121417, 1);
    document.body.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x121417);
    window.__SCENESMITH_THREE_SCENE = scene;
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.01, 10);
    camera.up.set(0, 0, 1);
    camera.position.set(0.62, -0.76, 0.58);
    window.__SCENESMITH_VIEWER_CAMERA = camera;
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0.23, 0, 0.35);
    controls.enableDamping = true;
    window.__SCENESMITH_VIEWER_CONTROLS = controls;

    scene.add(new THREE.HemisphereLight(0xffffff, 0x34383f, 1.2));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(0.4, -0.6, 1.4);
    scene.add(key);

    const root = new THREE.Group();
    scene.add(root);
    addRoom(root, sceneSpec.room);
    addDesk(root, sceneSpec.desk);
    for (const fiducial of sceneSpec.fiducials || []) addFiducial(root, fiducial);
    for (const tray of sceneSpec.trays) addTray(root, tray);
    await addSO101Urdf(root, sceneSpec.robot);
    for (const cube of sceneSpec.cubes) addCube(root, cube);
    addCameraSites(root);
    addLegend(sceneSpec);

    window.addEventListener('resize', () => {{
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }});

    let frame = 0;
    function animate() {{
      frame += 1;
      controls.update();
      renderer.render(scene, camera);
      const so101Summary = window.__SCENESMITH_SO101_URDF_SUMMARY;
      window.__SCENESMITH_VIEWER_READY =
        frame > 2 &&
        window.__SCENESMITH_SO101_URDF_LOADED &&
        (so101Summary?.meshObjectCount || 0) >= 10;
      window.__SCENESMITH_VIEWER_FRAME = frame;
      requestAnimationFrame(animate);
    }}
    animate();

    async function addSO101Urdf(parent, robotSpec) {{
      const manager = new THREE.LoadingManager();
      const loader = new URDFLoader(manager);
      loader.packages = {{
        so_arm_description: './so-101-urdf'
      }};
      loader.parseVisual = true;
      loader.parseCollision = false;

      return new Promise((resolve) => {{
        let modelAdded = false;
        let loadedRobotModel = null;
        manager.onLoad = () => {{
          if (loadedRobotModel) {{
            window.__SCENESMITH_SO101_URDF_SUMMARY = summarizeUrdfModel(loadedRobotModel);
            window.__SCENESMITH_WRIST_CAMERA_VISUAL = addWristCameraVisual(loadedRobotModel);
          }}
          window.__SCENESMITH_SO101_URDF_LOADED = modelAdded;
          resolve();
        }};
        manager.onError = (url) => {{
          window.__SCENESMITH_SO101_URDF_ERROR = `Failed to load ${{url}}`;
        }};
        loader.load(
          './so-101-urdf/urdf/so101_new_calib.urdf',
          (robotModel) => {{
            robotModel.name = 'so101_real_urdf';
            robotModel.position.set(...robotSpec.base_position_m);
            applyDefaultJointPose(robotModel, robotSpec);
            parent.add(robotModel);
            modelAdded = true;
            loadedRobotModel = robotModel;
            window.__SCENESMITH_SO101_URDF_MODEL_ADDED = true;
          }},
          undefined,
          (error) => {{
            console.error(error);
            window.__SCENESMITH_SO101_URDF_ERROR = String(error);
            resolve();
          }}
        );
      }});
    }}

    function addWristCameraVisual(robotModel) {{
      const gripperLink = robotModel.links?.gripper || robotModel.getObjectByName('gripper');
      if (!gripperLink) return {{ added: false, reason: 'gripper link not found' }};

      const group = new THREE.Group();
      group.name = 'scenesmith_wrist_camera';
      group.position.set(0.014, -0.0002, -0.078);
      group.quaternion.set(-0.452759, 0.4529, -0.519754, 0.565462);

      const bodyMaterial = new THREE.MeshStandardMaterial({{ color: 0x14171b, roughness: 0.58, metalness: 0.2 }});
      const lensMaterial = new THREE.MeshStandardMaterial({{ color: 0x05070a, roughness: 0.22, metalness: 0.55 }});
      const glassMaterial = new THREE.MeshStandardMaterial({{ color: 0x1b8cff, roughness: 0.12, metalness: 0.1, emissive: 0x042244, emissiveIntensity: 0.25 }});

      const housing = new THREE.Mesh(new THREE.BoxGeometry(0.032, 0.024, 0.018), bodyMaterial);
      housing.name = 'wrist_camera_body_visual';
      group.add(housing);

      const mount = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.056, 0.008), bodyMaterial);
      mount.name = 'wrist_camera_mount_visual';
      mount.position.set(0, -0.034, 0.004);
      group.add(mount);

      const foot = new THREE.Mesh(new THREE.BoxGeometry(0.028, 0.016, 0.008), bodyMaterial);
      foot.name = 'wrist_camera_mount_foot_visual';
      foot.position.set(0, -0.064, 0.004);
      group.add(foot);

      const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.0055, 0.0055, 0.008, 28), lensMaterial);
      lens.name = 'wrist_camera_lens_visual';
      lens.rotation.x = Math.PI / 2;
      lens.position.set(0, 0, -0.011);
      group.add(lens);

      const glass = new THREE.Mesh(new THREE.CircleGeometry(0.0046, 28), glassMaterial);
      glass.name = 'wrist_camera_glass_visual';
      glass.position.set(0, 0, -0.0154);
      group.add(glass);

      gripperLink.add(group);
      return {{
        added: true,
        parent: gripperLink.name || 'gripper',
        localPosition: [0.014, -0.0002, -0.078],
        localQuaternionWxyz: [0.565462, -0.452759, 0.4529, -0.519754],
        opticalAxis: '-Z',
      }};
    }}

    function summarizeUrdfModel(robotModel) {{
      const meshNames = [];
      const jointNames = [];
      let meshObjectCount = 0;
      let triangleCount = 0;
      robotModel.traverse((object) => {{
        if (object.isMesh) {{
          meshObjectCount += 1;
          if (object.name) meshNames.push(object.name);
          const geometry = object.geometry;
          if (geometry?.index) triangleCount += geometry.index.count / 3;
          else if (geometry?.attributes?.position) triangleCount += geometry.attributes.position.count / 3;
        }}
      }});
      for (const jointName of Object.keys(robotModel.joints || {{}})) {{
        jointNames.push(jointName);
      }}
      return {{
        name: robotModel.name,
        meshObjectCount,
        triangleCount: Math.round(triangleCount),
        jointNames,
        meshNames: meshNames.slice(0, 40),
      }};
    }}

    function applyDefaultJointPose(robotModel, robotSpec) {{
      for (const [jointName, value] of robotSpec.default_urdf_joint_positions_rad || []) {{
        if (typeof robotModel.setJointValue === 'function') {{
          robotModel.setJointValue(jointName, value);
        }} else if (robotModel.joints && robotModel.joints[jointName]?.setJointValue) {{
          robotModel.joints[jointName].setJointValue(value);
        }}
      }}
    }}

    function addRoom(parent, room) {{
      const floor = box(room.size_m[0], room.size_m[1], 0.012, 0x2b3036, 0, 0, -0.006);
      parent.add(floor);
      const back = box(room.size_m[0], 0.018, room.size_m[2], 0x9ca3ad, 0, room.size_m[1] / 2, room.size_m[2] / 2);
      const left = box(0.018, room.size_m[1], room.size_m[2], 0x8f98a3, -room.size_m[0] / 2, 0, room.size_m[2] / 2);
      const right = box(0.018, room.size_m[1], room.size_m[2], 0x8f98a3, room.size_m[0] / 2, 0, room.size_m[2] / 2);
      parent.add(back, left, right);
      if (room.ceiling_enabled) {{
        const ceiling = box(room.size_m[0], room.size_m[1], 0.01, 0xc3c7cc, 0, 0, room.size_m[2]);
        ceiling.material.opacity = 0.22;
        ceiling.material.transparent = true;
        parent.add(ceiling);
      }}
    }}

    function addDesk(parent, desk) {{
      parent.add(box(desk.size_m[0], desk.size_m[1], desk.size_m[2], 0x9c8f7a, ...desk.center_m));
      parent.add(box(desk.size_m[0], 0.035, 0.05, 0x5f564a, desk.center_m[0], desk.center_m[1] - desk.size_m[1] / 2, desk.center_m[2] + desk.size_m[2] / 2 - 0.03));
    }}

    function addTray(parent, tray) {{
      const color = colorHex(tray.color);
      const group = new THREE.Group();
      group.position.set(...tray.center_m);
      const base = box(tray.size_m[0], tray.size_m[1], tray.size_m[2], color, 0, 0, 0);
      base.material.opacity = 0.42;
      base.material.transparent = true;
      group.add(base);
      const rimH = 0.026;
      const rimT = 0.006;
      group.add(box(tray.size_m[0], rimT, rimH, color, 0, -tray.size_m[1] / 2, tray.size_m[2] / 2 + rimH / 2));
      group.add(box(tray.size_m[0], rimT, rimH, color, 0, tray.size_m[1] / 2, tray.size_m[2] / 2 + rimH / 2));
      group.add(box(rimT, tray.size_m[1], rimH, color, -tray.size_m[0] / 2, 0, tray.size_m[2] / 2 + rimH / 2));
      group.add(box(rimT, tray.size_m[1], rimH, color, tray.size_m[0] / 2, 0, tray.size_m[2] / 2 + rimH / 2));
      parent.add(group);
    }}

    function addCube(parent, cube) {{
      const mesh = box(cube.side_length_m, cube.side_length_m, cube.side_length_m, colorHex(cube.color), ...cube.initial_position_m);
      mesh.name = cube.name;
      parent.add(mesh);
    }}

    function addFiducial(parent, fiducial) {{
      const group = new THREE.Group();
      group.name = fiducial.name;
      group.position.set(...fiducial.position_m);
      const [rx, ry, rz] = fiducial.euler_deg || [0, 0, 0];
      group.rotation.set(THREE.MathUtils.degToRad(rx), THREE.MathUtils.degToRad(ry), THREE.MathUtils.degToRad(rz));
      const size = fiducial.size_m;
      const base = box(size, size, 0.002, 0xf1f1e8, 0, 0, 0);
      base.name = `${{fiducial.name}}_white_visual`;
      group.add(base);
      const rows = fiducial.grid || [];
      const cell = size / Math.max(1, rows.length);
      const half = size / 2;
      for (let row = 0; row < rows.length; row += 1) {{
        for (let col = 0; col < rows[row].length; col += 1) {{
          if (rows[row][col] !== '1') continue;
          const x = -half + cell * (col + 0.5);
          const y = half - cell * (row + 0.5);
          const marker = box(cell * 0.92, cell * 0.92, 0.0022, 0x050505, x, y, 0.002);
          marker.name = `${{fiducial.name}}_cell_${{row}}_${{col}}_visual`;
          group.add(marker);
        }}
      }}
      parent.add(group);
      window.__SCENESMITH_APRILTAG_VISUALS = [
        ...(window.__SCENESMITH_APRILTAG_VISUALS || []),
        {{
          name: fiducial.name,
          family: fiducial.family,
          tagId: fiducial.tag_id,
          sizeM: fiducial.size_m,
          positionM: fiducial.position_m,
        }},
      ];
    }}

    function addCameraSites(parent) {{
      parent.add(sphere(0.012, 0x66d9ff, 0.58, -0.72, 0.66));
      parent.add(sphere(0.01, 0x66ffcc, 0.31, 0, 0.42));
    }}

    function addLegend(spec) {{
      const legend = document.getElementById('legend');
      for (const tray of spec.trays) {{
        const item = document.createElement('span');
        item.innerHTML = `<i class="swatch" style="background:${{cssColor(tray.color)}}"></i>${{tray.color}} tray`;
        legend.appendChild(item);
      }}
      const robot = document.createElement('span');
      robot.innerHTML = '<i class="swatch" style="background:#ffd11a"></i>SO-101 URDF';
      legend.appendChild(robot);
      const camera = document.createElement('span');
      camera.innerHTML = '<i class="swatch" style="background:#1b8cff"></i>wrist camera';
      legend.appendChild(camera);
      for (const fiducial of spec.fiducials || []) {{
        const tag = document.createElement('span');
        tag.innerHTML = '<i class="swatch" style="background:#f1f1e8"></i>AprilTag';
        legend.appendChild(tag);
        break;
      }}
    }}

    function box(x, y, z, color, px, py, pz) {{
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(x, y, z), mat(color));
      mesh.position.set(px, py, pz);
      return mesh;
    }}

    function sphere(r, color, px, py, pz) {{
      const mesh = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 12), mat(color));
      mesh.position.set(px, py, pz);
      return mesh;
    }}

    function mat(color) {{
      return new THREE.MeshStandardMaterial({{ color, roughness: 0.65, metalness: 0.05 }});
    }}

    function colorHex(color) {{
      return {{ red: 0xd71914, blue: 0x1648d8, green: 0x178a3d, yellow: 0xf0bc24, purple: 0x7848bd, orange: 0xf06b24 }}[color] || 0x777777;
    }}

    function cssColor(color) {{
      return {{ red: '#d71914', blue: '#1648d8', green: '#178a3d', yellow: '#f0bc24', purple: '#7848bd', orange: '#f06b24' }}[color] || '#777';
    }}
  </script>
</body>
</html>
"""


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

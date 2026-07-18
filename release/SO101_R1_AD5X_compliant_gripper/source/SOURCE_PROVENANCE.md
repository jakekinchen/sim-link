# Source provenance

- Upstream: `https://github.com/Vector-Wangel/XLeRobot`
- Pinned commit: `51ca0ec31bdb48713b94bacdba828bf8d889296b`
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

- `SO101_soft_fin.stl`: `4125201fffaca5f9e5ee354a11ff80328c08e7ccb4676661442a937b7a79b121`
- `soft_gripper_finger.step`: `d90d2434f6920be1643963c6c1ba2dc1935a7ed84683ab01e07ee4bc132f4816`
- `LICENSE`: `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`
- upstream `XLeRobot_0_3_0.3mf` audit copy: `4b41ae03895144ffff0a22b0d1a76e02d4ff0db0bc5ff0066ab528df8ce4fa4d`

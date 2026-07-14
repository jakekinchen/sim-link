# Session Log 170 - T20.17 Bespoke/Package First Consolidation

## Scope

Brief 137's first simulation-only boundary recorded the recreation map and
retired only three module/test pairs proven to have no production import or
configuration consumer:

- `static_pose_session_review.py`
- `evidence_image_store.py`
- `so101_physical_coordinates.py`

The canonical SO-101 coordinate assertion remains in
`tests/unit/test_so101_coordinates.py`. Historical session logs, signed
artifacts, raw records, outputs, and the pinned external checkout were not
changed.

## Validation

- Repository-wide production-reference discovery found no remaining runtime
  reference to the three removed modules; the only current mentions are this
  retirement record and the recreation map.
- `PYTHONPATH=external/lerobot/src ./.mujoco_venv/bin/python -m unittest -q`
  passed 41 focused retained-contract tests: artifact, strict-grasp, geometry,
  scripted episode, SO-101 processor, coordinate, and stack checks.
- `PYTHONPATH=external/lerobot/src external/leLab/.venv/bin/python -m unittest
  -q tests.unit.test_pi05_autolearn` passed all 34 tests.
- The MuJoCo environment intentionally lacks `torch`; its direct
  `test_pi05_autolearn` run therefore cannot import the vendored LeRobot
  dependency. The pinned leLab runtime is the relevant passing training
  surface. This boundary did not change runtime imports.
- JSON parsing, pointer synchronization, Python compilation of retained
  boundaries, and `git diff --check` passed.

## Review and authority

Implementation commit `af317bccbdc139904f84684df7171ecfda2f2545` is reviewed
by Decision 167. No optimizer, model load or inference, simulator stepping,
hardware access, physical actuation, external compute, or Brev action occurred.
The task remains in progress; the next safe slice is the thin LeRobot-native
manifest and actual-pipeline hashing seam.

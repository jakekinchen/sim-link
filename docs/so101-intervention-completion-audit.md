# SO-101 Intervention System Completion Audit

**Date:** 2026-07-09

**Machine-readable result:**
`outputs/robot_lab/so101_desk_cube_sort/completion-audit/intervention-system-completion.json`

## Result

`PASS`

Every requirement in the active goal has current implementation and runtime
evidence. The audit is reproducible with:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/verify_intervention_system.py
```

## Requirement Matrix

| Requirement | Evidence | Result |
|---|---|---|
| AprilTag fiducial | Canonical 10x10 `tag36h11` ID 0 decoded from the MuJoCo overhead render with Hamming 0 and decision margin 224.79 | Pass |
| Randomized MuJoCo episodes | Seeds 4100-4102; 180 control frames; 540 distinct images; applied dynamics, camera, lighting, visual, and geometry randomization | Pass |
| Leader-arm correction bridge | Five live Studio leader samples and eight deadman-gated MuJoCo control frames; zero serial opens or motor writes by SceneSmith | Pass |
| Intervention dataset export | Three-episode 180-frame full export and three-episode 36-frame intervention-only export both reload through `LeRobotDataset` | Pass |
| Action-server UI hooks | Scripted randomized proof and real PI0.5 neural proof both pass Playwright with three cameras and no console errors | Pass |
| Documentation | Operator guide, SceneSmith/LeLab bridge, goal ledger, and this audit are present | Pass |
| Tests | 15 scene-builder, randomization, deadman, and leader-safety tests pass | Pass |
| Proof artifacts | Every required JSON report and browser screenshot exists; evidence hashes are in the completion report | Pass |
| Follower exclusion | Static tests, leader reports, browser proofs, and policy service all report no physical follower command | Pass |
| Live services | Action server responds at port 8822; persistent PI0.5 service is ready on MPS at port 8833 | Pass |

## Audit Corrections

The completion audit rejected two earlier weak claims and fixed them:

1. The original 8x8 marker looked like an AprilTag but did not decode. It was
   replaced with the canonical tag36h11 ID 0 geometry, the center debug site
   was hidden, cells were made contiguous, and an independent detector proof
   was added.
2. A valid neural task failure produced a complete episode summary but exited
   the runner with code 1, which the HTTP layer treated as an internal error.
   The action server now returns expected task failure as inspectable episode
   data while still rejecting missing or inconsistent runner output.

## Proof Boundaries

- The three-seed scripted batch proves pipeline behavior, synchronization,
  failure/recovery, export, and rendering. Its object motion is scripted and is
  not neural-policy or physical-contact training proof.
- The neural browser proof applies real PI0.5 actions from the persistent MPS
  service to MuJoCo contact physics. The current checkpoint stalls and task
  success remains false.
- The Studio leader bridge has live read and simulated-joint-control proof. No
  operator completed a cube grasp during the smoke, so contact success remains
  false.
- The physical follower is outside this goal and was never commanded.

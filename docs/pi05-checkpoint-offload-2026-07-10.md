# Pi05 checkpoint offload - 2026-07-10

To make room for additional local AI models, two older one-step Pi05 smoke checkpoints were moved off the internal SSD after content-level verification:

- `outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_mps_1step`
- `outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_wrist_mps_1step`

They now live at:

`/Volumes/cerebro-old/CodexOffload/EXPENDABLE_SPACE_RECOVERY/2026-07-10-scenesmith-pi05-and-codex-backups/pi05-archived-runs/`

The newest run remains local and is the one to use for current work:

`outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_physical_wrist_mps_1step`

All three were one-step smoke runs with no evaluation split or score that could establish a performance ranking. The two earlier runs were selected as the weaker archival candidates by recency and lower hardware fidelity; the physical-wrist run was kept locally.

The external folder is deliberately marked as an expendable recovery offload. Restore a run from that path before relying on it for an active experiment.

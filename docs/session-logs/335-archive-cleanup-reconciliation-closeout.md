# Session 335 — Archive Cleanup Reconciliation Closeout

## Boundaries

- Branch: `codex/pi05-autolearn-loop`
- Activation: `f25d63ea2a7dfd2d6bde7df830253b9d18648951`
- Reviewed implementation: `ac95b22947836fe8bc23413113fe7db7f6b5f21d`
- Brief: `docs/briefs/237-archive-cleanup-and-successor-spine-handoff.md`
- No hardware, model, optimizer, training, retry, external compute, or new
  Brev resource was used.

## Cleanup reconciliation

The tier-1/tier-2 paths named by the closure note were already absent from
`outputs/robot_lab/`. Preserved earlier audit: `DELETE_TOTAL_KiB 96967592`, or
96.97 GB decimal / 92.48 GiB. Current `outputs/` is 21 G; filesystem free is
146 GiB. Because the exact authorized targets were already gone, this session
performed no deletion.

The audit confirmed these keepers:

- tracked `autolearn/m13-rung-250/development-comparison.json` receipt;
- 2.6 G tier-3 `t20_35x` tree;
- 2.7 G R0 generator and 1.2 G R2/F0c source tree;
- 95 M append-only raw store;
- SmolVLA mirrors and rollouts;
- 13 G `weights/`; and
- 8.7 G external F1 selected-artifact directory on `/Volumes/cerebro`.

## Successor spine

`sim2claw` main `5ade87cb8e870bb4dc66c69e528ff0948c442d60`
contains `docs/SPINE_EXPORT.md` and `scripts/export_project_spine.sh`. A clean
scratch rehearsal exported 15 files plus one receipt and reconstructed all 15
hashes. Non-empty and root destinations failed closed with exits 73 and 64.

## Operational closeout

- `brev ls --json`: `{"workspaces": null}`.
- No sim-link training process was present.
- The :8790 server belongs to `/Users/kelly/Developer/so-101-sim`; installed
  Studio processes use `sim-link-studio` build products. They were out of scope
  and untouched.
- Two unrelated user crons were observed; no sim-link-owned cron exists.
- 21 focused project-state/documentation tests passed.
- JSON parse and `git diff --check` passed.

Source work stops. The branch remains unmerged; living work proceeds in
`/Users/kelly/Developer/sim2claw`.

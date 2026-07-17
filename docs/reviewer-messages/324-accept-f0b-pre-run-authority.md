# Reviewer Decision 324 - Accept F0b Pre-Run Authority

**Date:** 2026-07-17

## Decision

`ACCEPT_ONE_F0B_HYBRID_TAIL_CADENCE_EVALUATION`

The corrected Brief 232 implementation, model-free authority bundle, and smoke
preservation boundary are exact on origin at commits `171b5e5...`,
`4f70e0c...`, and `4cd4a53...`, respectively. This decision authorizes writing
one signed pre-run acceptance bound to this reviewer, followed only after that
acceptance is committed, pushed, and exact on origin by the single F0b
evaluation described below.

## Accepted identities and window

- spec: `ddf71cf91bcfcd4a1d40573a4ce5cfd648ee9dc141b3b6186bfbbd5fc16184ce`;
- owner grant: `b28101ec61e5f651e96f977dc6cf8263b08580e5c5e563cabaafded86529171d`;
- central request: `f5020b3d8fc24ed118004fc3d3bed32b39afbdbb0b4388d107be242d61b7856c`;
- central decision: `00ec322718fb1e20ea6d56f15e78c901f516fa7b78ec09703130fbc119e28cc2`;
- runtime preflight: `e36c53ddda321da618f5bc4260e607f6b4efda4af4427b85fcfa7e71f1142d9b`;
- one-use permit: `4a3843555efb86b7158820c8328276d26a9298c47c07184e9ae73a073ffbd686`;
- validity: `2026-07-17T05:17:00-05:00` through
  `2026-07-17T09:45:00-05:00`, with at least 30 minutes required at marker
  creation.

The central decision grants only its prerequisite
`simulation_training_ready`. The task-local owner grant and permit narrow that
token to one checkpoint load, one seed-0 simulation rollout, one signed result
mirror, and terminal evidence preservation. They explicitly deny optimizer
creation/training and retry; `training_lock` remains closed.

## Smoke and runtime review

Fresh retained-comparator rendering produced 244 H.264 frames at 1536x596 and
25 fps without checkpoint, model, inference, or simulation access. Smoke
receipt `2f1a9ef4...` binds signed manifest `86d4f7ad...`, MP4 SHA-256
`4ab15f7a...`, and 620,673 bytes. The exact signed manifest is remotely tracked
at
`configurations/robot_lab/f0b_hybrid_tail_cadence_renderer_smoke_manifest.json`
with file SHA-256 `74d33d91...`; its bytes equal the local output manifest.
The MP4 itself remains gitignored local diagnostic evidence, so a fresh clone
can audit the signed manifest/receipt linkage and declared video hash but cannot
replay the MP4 bytes. No broader remote-video-preservation claim is made.

Runtime preflight verifies branch/HEAD/upstream `171b5e5...`, Python 3.12.12,
torch 2.11.0, MuJoCo 3.3.5, LeRobot 0.6.1, MPS available, 172,285,657,088 free
bytes at observation time, checkpoint tree `c77ee362...` without tensor
deserialization, exact LeRobot/SO-ARM revisions, exact SO-101 asset tree, clean
implementation-scoped paths, and absent/unaliased attempt/result paths.

## Authorized execution

After the separately signed acceptance reaches origin:

1. write the one-use attempt marker before importing/loading ACT or reading a
   checkpoint tensor;
2. initialize Python, NumPy, and torch with seed `20260801` immediately before
   exactly one local checkpoint construction/load;
3. execute one policy-owned seed-0, 244-frame rollout with decode starts
   `[0,50,100,150,176,186,196,206,216,226,236]` and lengths
   `[50,50,50,26,10,10,10,10,10,10,8]`;
4. retain all eleven 50x6 chunks, the exact 24-action discard, two unexecuted
   selected terminal actions, all observed frames, source comparisons,
   independent unchanged strict-v2 replay, result, scorecard, retention,
   terminal receipt, and signed MP4 manifest;
5. stop after the first pass, policy negative, or infrastructure failure. No
   retry or automatic corrective rung follows.

## Closed authority

No optimizer, training, scheduler, sampler, dataset loader/mutation,
statistics or threshold change, second seed/checkpoint/episode, retry,
network/package installation, external compute, Brev, camera, serial, robot
hardware, physical motion, physical transfer, promotion, destructive
operation, or freeze tag is authorized. A Gate C pass is simulation evidence
only and routes to a separate F2/kit decision; it grants no physical authority.

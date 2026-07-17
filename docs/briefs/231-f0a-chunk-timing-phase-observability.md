# Slice Brief 231 - F0a Chunk Timing And Phase Observability

**Date:** 2026-07-17

## Objective

Explain F0's 20-frame delayed release without loading a checkpoint or running a
policy. Determine whether the retained ACT candidate encountered a direction-
ambiguous observation in the lift/lower reversal corridor, whether fixed
chunk-50 observation cadence coupled that state lag to the frozen release gate,
or neither. This audit may route a later experiment; it cannot execute one.

## Frozen source boundary

- Closeout source: `c433177b36baea3e7eea048ce743b509b61e3799`.
- F0 result: `807d3da7e21bbf3ec846454bb13aa6a2cb92eac4f6dffe8d86becb0ad777e5f9`.
- R0 retention: `19d19fbaa315511fa0e7df736d3895089827da8f0b8a2aecd15a2a75885bd495`.
- R0 statistics: `02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae`.
- Retained chunk-50 trace:
  `77bf82ce917c2a30cc3bfc915b887f0e6af98c8c8a397f022b633ccf23c7d19c`.
- Source episode file:
  `586a3e67034a577bf046381837aebe68d3d5febdce6b1c51dbcb6f0be4968b54`;
  raw rollout identity
  `9e186088c9ca82fa9c58cb6e3870f322a9c2a84405d5ea23152b822fb9d4abdb`.
- Frozen decode starts `[0, 50, 100, 150, 200]`, executed lengths
  `[50, 50, 50, 50, 44]`, one initial queue reset, release frames 200-211,
  release-settle frames 212-219, and retreat frames 220-243.

The audit must bind the exact R0 dataset feature metadata and statistics, raw
source frames and images, retained candidate/source comparisons, ACT runner,
coordinate map, and phase plan. It may decode already retained PNG bytes but
must not render a new image or create simulator state.

## Measurements and pre-registered rules

1. **Consumed observation contract.** Prove the exact ACT inputs at training
   and rollout. Report whether joint velocity, phase, progress, timestamp, or
   environment state is present. Distinguish raw compiler fields from the
   fields that survive into `LeRobotDataset` and the runner.
2. **Candidate progress at decode boundaries.** Convert source and candidate
   qpos to LeRobot units and normalize by the actual R0 observation-state
   standard deviations. At each decode start, report the nearest source frame
   overall and within each phase. For frame 200, define lower-state lag as
   `200 - nearest_lower_frame`. Lag alignment with F0 is supported only when
   the nearest lower frame precedes release and the lag differs from F0's
   20-frame release shift by at most five frames.
3. **Lift/lower reversal alias.** Use lift frames 76-99 and lower frames
   176-199 from the exact source episode. For each lower frame, choose the
   qpos-nearest lift frame. Calibrate one-step reference distributions from
   adjacent pairs inside those same two corridors.
   - state-near means normalized qpos L2 is no greater than the adjacent-state
     95th percentile;
   - image-near means the mean absolute RGB pixel difference across both
     256x256 cameras is no greater than twice the adjacent-image 95th
     percentile;
   - hidden direction conflicts when joint-velocity cosine is at most `-0.8`;
   - future targets conflict when the next-ten arm-action displacement cosine
     is at most `-0.8` with both norms at least `0.01` rad, or the next-twenty
     gripper targets differ by at least `0.5` rad.

   A reversal-observability defect is supported only when at least 12 of the 24
   lower frames satisfy all four conditions and the consumed ACT observation
   omits the conflicting velocity, phase, and progress fields. The image
   factor of two is frozen to tolerate object/render displacement along the
   reversed path while still requiring local, source-calibrated similarity.
4. **Chunk/gate coupling.** This mechanism is supported only when lag alignment
   passes, the aligned candidate release begins after frame 219, no policy
   observation occurs between frame 200 and that onset, the frozen release
   gate fails, and the frozen retreat-final-clear gate passes. Report facts at
   exact frames; do not relabel retreat clearance as a Gate C pass.

## Decision rule

- If chunk/gate coupling is supported, route first to a separately reviewed
  no-training F0b evaluation of the retained checkpoint. The counterfactual
  keeps chunk-50 execution through frame 175, discards the remaining queued
  tail once at frame 176, then re-decodes every ten actions at starts
  `[176, 186, 196, 206, 216, 226, 236]`. Expected executed lengths are
  `[50, 50, 50, 26, 10, 10, 10, 10, 10, 10, 8]`. Frozen strict-v2 Gate C and
  the source episode remain unchanged. F0b requires its own checkpoint,
  inference, rollout, authority, and one-attempt evidence boundary.
- If cadence coupling is false but the reversal-observability defect is true,
  route only to a separately reviewed velocity-augmented ACT data/schema
  proposal. The owner-authorized corrective training rung remains unspent.
- If neither mechanism passes, close the F0 family without corrective training.

No phase token or wall-clock forcing is licensed by this audit: opening the
gripper before the state reaches the release corridor could be unsafe. Any
future correction must preserve the frozen R2 negative and report the original
chunk-50 and receding-10 results unchanged.

## Deliverables and acceptance

- `scenesmith/robot_lab/f0a_chunk_phase_observability.py` emits and verifies one
  canonical signed result with exact source references, per-frame pair rows,
  calibration thresholds, findings, route, and false authority fields.
- `tests/unit/test_f0a_chunk_phase_observability.py` covers input-field loss,
  normalization, image decoding, alias thresholds, zero-norm target handling,
  lag/cadence routing, source drift, and authority mutation.
- `configurations/robot_lab/f0a_chunk_phase_observability.json` retains enough
  compact evidence to recompute every decision without a model or bulk output.
- Focused tests, relevant F0/ACT regressions, live verify, JSON/lint/whitespace,
  and a fresh same-agent adversarial review pass before closeout.

## Authority boundary

Allowed: read and hash frozen local evidence; decode retained PNG bytes in
memory; implement and fixture-test the deterministic audit; write its compact
signed result; update canonical docs and state after review.

Closed: new rendering or simulation, checkpoint tensor reads, model
construction/loading/inference, optimizer creation or training, rollouts,
dataset or statistics mutation, gate/threshold changes, network or package
installation, Brev/external compute, cameras, serial or robot hardware,
physical motion, Gate C execution, transfer, promotion, destructive operations,
and the freeze tag.

## Closeout

Implementation commit `f81fa9aa90ba4eaf93a125433f1f341992cca54b` is
exact on origin. Canonical result
`278e8bc772dc879622a226abe22665d320421925045ad9b3cb1f88b1c31153a4`
(file SHA-256
`2ef689c7f51784a799db20cba5dec5f35c51422608b5a78ff4bd94346da06fa6`)
passes its live source reconstruction and Reviewer 321.

Twenty of 24 lower-corridor source frames have a qpos-near and image-near lift
counterpart with opposite hidden velocity and a conflicting future target.
The retained candidate's frame-200 qpos is nearest lower frame 183 at normalized
L2 `0.5811591805297467` and almost equally near lift frame 93 at
`0.5813087817685448`; its 17-frame lower-state lag is within three frames of
F0's 20-frame release-pattern delay. These are deliberately separate evidence
claims: image similarity is measured between exact source frames, not invented
for candidate camera observations absent from the retained trace.

The fixed chunk-50 actor observes at frame 200 and not again before the delayed
release onset at frame 220, one frame after the frozen release gate at frame
219. The release gate fails while retreat-final clearance passes. The
pre-registered decision therefore routes to a fresh, separately reviewed F0b
hybrid-tail-cadence evaluation. No checkpoint tensor, model, inference,
optimizer, rollout, simulator, dataset, gate, hardware, network, external
compute, or Brev action occurred, and no corrective rung was selected or
consumed.

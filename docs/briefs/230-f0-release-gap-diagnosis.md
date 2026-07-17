# Slice Brief 230 - F0 Release-Gap Diagnosis

**Date:** 2026-07-17

## Objective

Explain the preserved T20.43c-R2 release-only failure using a deterministic,
model-free audit of the exact R0 data and ACT training path. Falsify candidate
mechanisms before selecting any corrective recipe. This brief cannot create a
model or optimizer, deserialize a checkpoint, run inference or a rollout,
start Brev, or access hardware.

## Frozen source boundary

- Source boundary: `545bba080c1af4033423e595f66b6c15fdf11a1f`.
- R0 mixture: `37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df`.
- R0 statistics: `02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae`.
- T20.43c-R2 run: `82a0608386375f029a56be8ca9f972bc0e83939d30ad286164db828aa22dc851`.
- T20.43c-R2 final receipt: `be11a258b6662baa10341acac13fe09055cd4ded7c2eaba4236d466977dfac5e`.
- Frozen execution semantics: seed `20260801`, batch size 8, 10,000
  updates, chunk size 50, and rollout phases totaling 244 frames with the final
  chunk beginning at frame 200 and executing 44 actions.

The audit must bind the exact tracked runner, LeRobot dataset-reader, sampler,
ACT loss, coordinate-contract, statistics, episode metadata, and retained
rollout bytes it interprets. The ignored R0 tree may be read only after its
tracked retention identities verify.

## Measurements, in order

1. **Actual sampler and tail coverage.** Reconstruct all batches consumed by
   the R2 seed and recipe. Distinguish the unpadded horizon-50 index from the
   actual `LeRobotDataset(delta_timestamps=0..49)` plus
   `EpisodeAwareSampler` path. Count frame-start exposure, valid target-action
   exposure, pad masks, phase mass, and exact frame-200 starts. A tail-coverage
   defect exists only if any target frame 200-243 receives less than 90% of the
   median exposure for target frames 50-199, or if actual release-phase mass is
   less than 90% of its valid-frame geometric share.
2. **Open-gripper normalization.** Compare every release/open action to the R0
   action min/max, mean/std, and normalized magnitude. A normalization defect
   exists only if the required open value lies outside the R0 envelope, is
   non-finite, or exceeds three standard deviations. Do not reuse the older
   T20.12 envelope as if it were R0.
3. **Release mixture.** Report start-sample and valid-loss mass for `release`,
   `release_settle`, and `retreat`, including truncated base episodes and the
   exact deterministic third-epoch subset. Do not infer weighting from the
   standalone unpadded-window artifact when the runner does not consume it.
4. **Gripper loss alignment.** Derive normalized-unit-to-physical-radian
   Jacobians from the R0 standard deviations and canonical coordinate map. For
   ACT's L1 objective, normalize absolute-Jacobian coefficients to active mean
   1.0. A gripper-weighting mechanism remains eligible only when its coefficient
   is at least 1.5 and the retained best R2 rollout has a same-direction,
   contact-relevant gripper error during release.

## Decision rule

- A verified tail or normalization defect routes to a fresh-data 10,000-update
  proposal that changes only the diagnosed data/statistics surface.
- If tail and normalization are falsified but both release-mixture and gripper
  alignment remain coherent, route to a separately reviewed approximately
  2,000-update continuation proposal with release-start oversampling and an
  explicitly derived gripper coefficient.
- If no mechanism clears its rule, close F0 without training. Do not spend the
  owner-authorized single corrective rung on an ungrounded recipe.

Any routed training is a new task and brief. It must preserve chunk-50 as the
primary rollout, frozen strict-v2 Gate C predicates, held-out ownership, and
the immutable T20.43c-R2 negative.

## Deliverables and acceptance

- `scenesmith/robot_lab/f0_release_gap_diagnosis.py` emits one canonical signed
  result and independently verifies it.
- `tests/unit/test_f0_release_gap_diagnosis.py` covers source drift, padding
  semantics, deterministic sampler reconstruction, phase truncation,
  normalization boundaries, physical-L1 weights, and fail-closed routing.
- `configurations/robot_lab/f0_release_gap_diagnosis.json` retains exact counts,
  ratios, source hashes, findings, route, and false authority fields.
- Focused tests, relevant ACT regressions, JSON/compile/whitespace checks, and a
  fresh same-agent adversarial review pass before Reviewer 320 may close F0.

## Authority boundary

Allowed: read and hash frozen local artifacts; implement and fixture-test the
deterministic audit; write its compact signed result; update canonical docs and
state after review.

Closed: checkpoint tensor reads, model construction/loading/inference,
optimizer creation or training, rollouts, dataset mutation, threshold changes,
network or package installation, Brev/external compute, cameras, serial or
robot hardware, physical motion, Gate C execution, transfer, promotion,
destructive operations, and the freeze tag.

## Closeout

Reviewer 320 verifies this brief at implementation commit
`698d5644e9add156266f0ab4997aaa27c9b98b10`. Canonical result
`807d3da7e21bbf3ec846454bb13aa6a2cb92eac4f6dffe8d86becb0ad777e5f9`
reconstructs all 10,000 update batches over 129 episodes and 31,366 frames.
The exact consumed path produced 79,996 sampled starts, including two
six-sample end-of-epoch batches.

The pre-registered tail and mixture rules are falsified: minimum late-frame
target exposure is 97.085% of the frame-50-to-199 median, late-phase valid-loss
mass is 113.889% of its geometric share, and frame-200 starts are 97.869% of
uniform expectation. Tail padding is active with final valid lengths 44 and
38. The standalone unpadded H50 index contains no release window, but the ACT
runner does not consume that index.

The R0 action envelope also falsifies the normalization hypothesis. Required
open gripper is within the pre-registered `1e-4` envelope tolerance at 1.4174
standard deviations. The physical-L1 coefficient for gripper is 2.6963, and
retained release error is
same-direction and contact-relevant, so loss underweighting remains
mechanistically coherent. It is not enough to select the one corrective rung:
the retained candidate reproduces the 12-frame source release pattern best at
a 20-frame shift, reducing MAE from 0.74179 rad to 0.04893 rad, a 15.16x
alignment improvement.

F0 therefore closes without corrective training. The single corrective ACT
rung remains unconsumed. A fresh model-free F0a brief may audit chunk timing,
phase observability, and observation aliasing after this closeout is exact on
origin. Every closed authority in this brief remains closed.

# Session 325 - F0 Release-Gap Diagnosis

**Date:** 2026-07-17

**Task:** F0 / Brief 230

**Reviewer:** 320

## Outcome

F0 is a verified model-free diagnosis at implementation commit
`698d5644e9add156266f0ab4997aaa27c9b98b10`. Signed result
`807d3da7e21bbf3ec846454bb13aa6a2cb92eac4f6dffe8d86becb0ad777e5f9`
binds the exact R0 mixture, statistics, retained episode metadata, standalone
window index, R2 final rollout, runner, coordinate contract, and relevant
LeRobot sampler, dataset-reader, and ACT-loss sources.

The actual R2 training path sampled all episode frames and masked padded target
actions. Reconstructing all 10,000 updates yields 79,996 starts over 129
episodes and 31,366 frames. Minimum exposure across target frames 200-243 is
0.9708519498 of the frame-50-to-199 median. Late-phase valid-loss mass is
0.2024620810 against geometric share 0.1777721099, a ratio of 1.1388855154.
Exact frame-200 start exposure is 0.9786928323 of uniform expectation. The
tail and release-mixture defect hypotheses are false.

Required open gripper is 92.4301772% in LeRobot units, inside the R0 maximum
92.4301758% under the pre-registered `1e-4` float tolerance and only
1.4173925665 standard deviations above the mean. The old T20.12 envelope is
not the R0 envelope. The normalization hypothesis is false.

Physical-L1 conversion gives gripper a mean-one coefficient of
2.6963081474. The retained final rollout's release error is same-direction and
contact-relevant, so normalized-L1 gripper underweight remains supported. The
candidate nevertheless reproduces the source release pattern most closely 20
frames late: zero-shift MAE is 0.7417896319 rad, aligned MAE is 0.0489290261
rad, and the improvement ratio is 15.1605231282.

## Verification

- live write/verify and final verify reproduce identity `807d3da7...`;
- five focused F0 tests pass inside a 46-test relevant unit suite;
- 14 T20.43c continuation/replacement regressions pass independently;
- Ruff, JSON parsing/non-finite audit, source-reference ordering and path
  checks, source symlink audit, and whitespace checks pass;
- same-agent adversarial review finds no checkpoint deserialization, model or
  optimizer construction, inference, rollout, dataset mutation, network,
  external compute, Brev, hardware, path traversal, or authority escalation.

## Disposition

F0 closes without corrective training. The one owner-authorized corrective ACT
rung was neither selected nor consumed. The next eligible task is a fresh
model-free F0a brief for chunk timing, phase observability, and observation
aliasing. Training, Gate C, F1/Brev, hardware, transfer, promotion, and the
freeze tag remain closed.

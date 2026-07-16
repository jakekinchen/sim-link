# Reviewer Decision 271 - Verify T20.36o Baseline Negative

**Decision:** `VERIFY_BASELINE_NEGATIVE_ROUTE_SEPARATE_OPTIMIZER_AUTHORITY`

## Reviewed Boundary

Brief 208; Reviewer 270; remotely preserved runner `781e0e0`; source commit
`a40573a`; attempt `f89d3c04...`; decoded tensors `40bf3b01...`; denoise
trajectories `202ace38...`; result `e6537428...`; retention receipt
`1154d524...`; live and tracked-only exact verification; 27 combined tests;
and the complete scoped diff.

## Findings

- Permit `3d6a1548...` was consumed exactly once. One model was constructed and
  loaded; 50 decoded chunks and 500 denoise-step records were captured. No
  optimizer was created and no Gate C rollout occurred.
- All five start-zero endpoint hashes reproduce. Both endpoint and complete
  denoise-path repeats are bit-identical for all 25 probes.
- The retained source objective ratio remains passing at
  `0.002522120613670501 <= 0.1`.
- Start 0 preserves the prior mixed result: 3/5 seeds pass, with only five
  grasp/gripper violations and a maximum threshold ratio of 1.176784.
- Starts 50, 100, 150, and 200 fail all five seeds with respectively 649, 543,
  513, and 505 violations. Maximum threshold ratios are 47.3396, 45.7423,
  45.6028, and 16.7272. This is a decisive downstream-state coverage failure,
  not a gate-edge miss.
- Across 2,215 violations, gripper contributes 918 and shoulder lift 771;
  elbow flex contributes 220, wrist flex 270, and wrist roll 36. The miss is
  structured across later observations and both relative gate phases.
- The final six padded predictions at start 200 remain unscored. Frozen
  amendment `463477dc...` and the report-only uniform threshold are unchanged.
- The tracked-only verifier reconstructs result `e6537428...` without the
  gitignored run summary. The 8.3 MB trajectory artifact retains every float32
  state/velocity value, and receipt `1154d524...` binds all tracked paths,
  identities, file hashes, and sizes.
- Gate C remains unauthorized and not request-eligible at update 0. The owner
  direction keeps the conceptual route open only through a future bridge pass.
- No retry, threshold change, candidate substitution, hardware, network,
  external compute, or Brev occurred.

## Disposition

Verify the baseline negative and remotely preserve the complete result before
any optimizer action. Route next only to the already-designed bounded fallback:
250 retained correction examples, 1:1 unique standard replay, 2,500 updates
maximum, probes at 0/500/1000/1500/2000/2500, and first confirmed complete
pass. Compose and review a separate optimizer authority first.

## Withheld Authority

No optimizer creation/training yet, no second baseline attempt, no Gate C
execution, no threshold change, no policy selection/promotion, no hardware,
no network, no external compute, and no Brev.

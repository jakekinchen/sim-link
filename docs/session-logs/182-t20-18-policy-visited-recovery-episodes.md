# Session Log 182 - T20.18 Policy-Visited Recovery Episodes

## Scope

Brief 149 extended T18.4's immutable branch identity contract into exact
MuJoCo integration-state capture and bounded recovery episodes rooted in the
failed T20.17 policy rollout. No optimizer, hardware, camera, external compute,
or Brev was used.

## Execution

- The complete signed T20.17 seed-6 evaluation replayed exactly before any
  captured state was accepted.
- All 244 pre-action integration states were captured; deterministic midpoints
  selected approach frame 6, grasp frame 49, hold frame 71, and release frame
  205.
- Each parent ran a nominal and a bounded 0.01-rad joint-offset child using the
  immutable measured source suffix from the same frame onward.
- Every child ran twice with byte-identical state/action/contact trace
  summaries and zero numeric tolerance.
- Observed outcomes were four strict recoveries, two conservative near-failures
  that missed the full-cycle hold count, and two release-phase failures.
- A separate immutable supplement retained 1,290 complete child frames and
  2,580 fresh branch-rendered top/wrist observations across eight episodes.

## Evidence

- Causal manifest identity:
  `f97c784f2f68ce3028a221acb715576c8c3fcaf0e66917e77ad28ecef11dd0b3`.
- Causal gate identity:
  `299b24ae36579dced8552b6c34bf8fef41011d93c03f28026fa962d2ad739427`.
- Episode package identity:
  `4123e8d40e5e1fd80702c4dc40ceb7a31922c2da2f36c797c91a20677f208e7c`.
- Episode package gate identity:
  `c6f365151550e58f5edf7d52e51d7f1b3742995331c038fc571e66e3bc9e7b73`.
- The package occupies 48 MB in the ignored output store and contains 2,589
  files. Tracked gates bind every episode and observation byte.

## Validation And Review

Fifty focused/relevant tests and 273 subtests passed in the pinned LeRobot
runtime. Both artifact gates independently re-opened and verified source files,
parent states, measured actions, traces, images, counts, labels, and false
authority fields. Python compilation, workflow audit, project-state pointer
check, documentation gates, and diff checks passed. Same-agent adversarial
review covered finite/bounds safety, aliasing, double counting, source drift,
nondeterminism, label honesty, discarded evidence, and cleanup side effects.

## Result

Reviewer Decision 179 verifies T20.18 as recovery-episode evidence and a future
training candidate, not a frozen mixture or training-ready authority. T20.19 is
the next dependency-ready simulation-only task.

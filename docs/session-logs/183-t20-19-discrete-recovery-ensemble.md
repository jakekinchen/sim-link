# Session Log 183 - T20.19 Discrete Recovery Ensemble

## Scope

Brief 150 ran one fixed 12-cell, one-factor-only falsification grid around the
verified T20.18 approach recovery branch. It used local MuJoCo only. No model,
optimizer, hardware, camera, external compute, or Brev was used.

## Execution And Result

- Every cell restored the same frame-6 integration state with seed 6.
- The controller source remained the 238 measured actions bound to recovery
  branch `35790636...`; timing and gripper cells recorded explicit deterministic
  transforms rather than relabelling them as measured source actions.
- Each of 12 cells ran twice with exact trace identities.
- Eleven cells passed strict-v2. The sole failure was gripper scale 1.05:
  31.849 mm lift, 77 strict-contact frames, 21/64 stable-hold frames, and 9/24
  lower frames.
- The nominal cell passed with 136 strict-contact frames and 36.328 mm lift.

## Evidence

- Cell manifest identity:
  `2842bb35296e1a5b1504ba07932ddb425cff4f1a68115249a26d259ebf708688`.
- Evidence identity:
  `67c0003ef46961a5cb932a3a7ab0b78b117ed75b3a1e26e580a9d1b10175a12b`.
- Scorecard identity:
  `19834ecd0198764a1243b3be6d34d37ab19b14b94e095f843aa8f7fdc81cac0f`.
- Tracked gate identity:
  `1205e336a81b68b650013572bd96ac8f6d452a5262ab924966aa14b7fa5e10c6`.

## Validation And Review

Fifty-four relevant tests and 274 subtests passed in the pinned runtime. The
tracked manifest, evidence, scorecard, replay hashes, derived success rate, and
worst-cell selection reverified. Same-agent adversarial review covered physical
bounds, finite values, source/action provenance, factor isolation, transform
length, projection, replay determinism, score derivation, authority escalation,
and cleanup side effects.

## Result

Reviewer Decision 180 verifies a 91.67% success rate only on this fixed,
uncalibrated grid. The +5% gripper cell exposes a concrete sensitivity. T20.20
is next; no optimizer or physical authority was created.

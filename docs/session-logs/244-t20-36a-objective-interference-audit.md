# Session Log 244 - T20.36a Objective Interference Audit

## Evidence

- Implementation commit: `3bbdc64`.
- Audit identity: `339a72290b302a2751be02bbccc07ac9441e3b5db65f023741ce38ba190b73aa`.
- Audit file SHA-256: `526f88fd114715bd210a2b1719db4d58ce9fd6e7afa79a7cddf1c7a2d856a707`.
- Audit size: 20,116 bytes.
- Source result: `e79dacff...`; campaign result: `02b543be...`.
- Twenty relevant T20.35x/T20.36/T20.36a tests pass; exact audit verification,
  lint, compile, diff, pointer, and workflow checks pass.

## Result

T20.36a classifies `weighted_objective_physical_gate_aliasing_under_coverage`.
The joint-weighted correction metric improves to `0.513119` of X while raw
correction worsens to `1.545902`, standard objective worsens `12.118449`-fold,
and the worst decoded physical error worsens `4.176295`-fold. All five seeds
worsen. This proves metric non-equivalence in the recorded campaign, not a
specific gradient cause. Reviewer 241 routes a pure Gate B retention contract.
No checkpoint, model, optimizer, rollout, hardware, external compute, or Brev
action occurred.

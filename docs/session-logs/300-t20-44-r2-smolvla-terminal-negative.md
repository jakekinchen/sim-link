# Session Log 300 - T20.44 R2 SmolVLA Terminal Negative

**Date:** 2026-07-16
**Task:** T20.44 / Brief 220

The sole permit-consuming T20.44 attempt completed the frozen cached-base
SmolVLA recipe: 5,000 finite updates, five scheduled checkpoints, and ten
chunk-50/receding-10 strict-v2 rollouts. Producer and independent verifier
both return terminal-negative result `9d916206...` with run `3d49f4df...`.
No Gate C pass exists.

The closest partial behavior was checkpoint 1,000/receding-10: 73 strict
contact frames and 18.061 mm lift, but only 3/8 grasp-hold and 31/64 stable-hold
frames. At checkpoint 5,000, chunk-50/receding-10 reached only 5.507/3.427 mm
lift, and neither recorded a grasp-hold frame. Strict-v2 remains unchanged and
the first-pass selector is null.

Reviewer 297 verifies marker `cb01bcfb...`, result `9d916206...`, scorecard
`c8d7e3f0...`, retention `727b4067...`, complete local signed checkpoint/
rollout/mirror trees, independent verifier exit 0, and zero forbidden runtime
uses. The T20.44 attempt is consumed with no retry. After this closeout is
exact on origin, owner addendum `8b4a206` routes to one fresh T20.43b ACT
replacement brief using the stable T20.44 renderer runtime and unchanged ACT
recipe. T20.45, archive replay, hardware, network, external compute, and Brev
remain closed.

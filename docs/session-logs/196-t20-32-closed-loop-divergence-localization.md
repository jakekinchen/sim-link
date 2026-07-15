# Session Log 196 - T20.32 Closed-Loop Divergence Localization

## Scope

Brief 163 instrumented complete source-relative closed-loop traces for the
frozen T20.24 and T20.31 adapters on training seed 0 and held-out seeds 6-7.
It ran local-MPS inference only. No optimizer, dataset/statistics/twin change,
hardware, camera, external compute, or Brev was used.

## Evidence

- Threshold identity: `edbbf85e56a7020cec9b16cbab6263dc3e9dbe106ff8f55b53a85d3034d7f4cb`.
- Result identity: `f9b091c61f6be77c66034a6062124418e84c21f01fb43b55f4c19f8ec42bd9a5`.
- Trace coverage: 6/6 complete signed traces, 244 frames each, 1,464 total.
- Frozen held-out replay: 4/4 prior action-sequence hashes reproduced exactly.
- T20.24 seed 0: first action divergence at frame 0, shoulder lift
  `1.020866` rad; no strict grasp.
- T20.31 seed 0: first action divergence at frame 0, shoulder lift
  `0.823639` rad; no strict grasp.
- Both first state divergences occur at frame 1; projection and assistance are
  zero across every probe.

## Result And Validation

The observed failure begins before chunk-boundary, cadence, hold, or
observation-feedback effects can initiate it. T20.32 therefore routes Gate B
`gate_b_memorization_or_model_plumbing`, not the leading Gate C hypothesis.
Forty-nine relevant tests pass, both trace sets and the signed report reverify,
the autonomous-workflow audit passes, and implementation commit `7bbf7cf` is
confirmed on origin. Policy acceptance, transfer, promotion, hardware,
external compute, and Brev remain false.

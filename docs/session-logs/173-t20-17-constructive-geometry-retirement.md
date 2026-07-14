# Session Log 173 - T20.17 Constructive Geometry Retirement

## Scope

Implementation `1aceebec9c200e92eb485eeaee0e72e903cdeea8` removes the
obsolete `geometry_first_grasp_search` candidate generator and the eight T19
wrapper builders. The retained behavior now lives in
`geometry_derived_grasp_primitives.py`: the deterministic MuJoCo runner,
midpoint solve, orientation selection, contact truthfulness helpers, post-yaw
settle duration, and approach-motion limit.

The unilateral grasp uses the exact historic source request as a fixed named
fact. It no longer derives that request through a Halton candidate index. The
scripted generator and closed-loop evaluator consume the named primitive.

## Validation

- The frozen geometry-derived proof replayed exactly against its immutable
  signed artifact.
- Focused MuJoCo tests passed for retirement, frozen diagnostics, geometry
  proof, scripted episode generation, and ACT closed-loop gates (17 tests).
- The broad MuJoCo discovery gate and the cross-runtime pinned-leLab gate both
  passed. A static guard confirms no live source imports a retired wrapper and
  no Halton candidate generator remains in the live primitive.
- The signed historical JSON files and `retired_grasp_diagnostics.py` were
  retained. Only redundant per-wrapper tests were removed; the consolidated
  hash-pinning test remains.

## Authority

No new search was run and no historic artifact was regenerated. No model,
optimizer, dataset conversion, simulator evaluation beyond deterministic unit
proofs, hardware, external compute, or Brev action occurred. This does not
grant training, policy, physical-transfer, or promotion authority.

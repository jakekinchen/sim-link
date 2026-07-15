# Brief 193 - T20.36b Gate B Retention Contract

## Objective

Encode the unchanged Gate B standard-objective and five-seed physical-action
conjunction as a pure fail-closed checkpoint-retention decision so no proxy
loss can again be mistaken for memorization retention.

## Frozen Sources

- T20.35x signed Gate B pass `e79dacff...`.
- T20.36 signed Gate B regression `02b543be...`.
- T20.36a signed non-equivalence audit `339a7229...`.
- Exact thresholds: standard/original objective ratio at most `0.10`, maximum
  physical action error at most `0.05` rad on every fixed inference seed
  `20260721` through `20260725`.

## Contract

Define a signed retention specification with a predeclared ordered checkpoint
schedule. A checkpoint row is Gate-B-retained only when its standard ratio and
all five exact-seed physical maxima pass. Weighted, raw, coverage, or aggregate
losses may be tracked but cannot substitute for either conjunct.

The decision must distinguish:

1. a post-source checkpoint that retains Gate B;
2. only the frozen source checkpoint retaining Gate B, which is rollback
   capability but not a coverage candidate;
3. no checkpoint retaining Gate B; and
4. invalid, incomplete, stale, post-hoc, duplicated, or non-finite evidence.

## Acceptance

- Deterministic positive, negative, adversarial, missing-seed, duplicate,
  reordered, changed-threshold, proxy-only, stale-identity, and non-finite
  tests pass.
- A signed contract plus fixture decision proves T20.35x is retained only as
  the source and T20.36 is rejected as a coverage candidate.
- The output grants contract validity only. It cannot grant training,
  inference, Gate C, policy acceptance, physical transfer, or promotion.
- Focused and relevant broad tests, lint, workflow audit, same-agent review,
  scoped commit, push, and remote confirmation agree.

## Prohibited Actions

No checkpoint read, model construction, inference, optimizer, training,
campaign permit, rollout, dataset/statistics mutation, Gate B amendment,
hardware, camera, serial, external compute, or Brev.

## Result Boundary

Spec `6e56f6ff...` and historical-fixture decision `e709c30c...`, preserved at
`5fdc36c`, retain only `t20_35x_source` as rollback capability. T20.36 fails
the action conjunct and no coverage checkpoint is selected. The fixture does
not claim pre-registration; future schedules require remote preservation
before optimizer creation. Reviewer 242 verifies the contract and routes only
the read-only local ACT/SmolVLA preflight in Brief 194.

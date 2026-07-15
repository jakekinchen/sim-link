# Brief 188 - T20.35v Dependency-Complete Balanced Path Audit

## Objective

Execute the T20.35u trajectory comparison under a distinct one-use permit only
after the exact Python 3.12 runtime proves every dependency needed through
dataset construction, checkpoint loading support, and policy construction is
importable without consuming the attempt.

## Frozen Evidence

- Bind T20.35u runtime failure `0abd9650...` and consumed attempt
  `179092b9...`; neither may be deleted, rewritten, or reused.
- Rebind the unchanged T20.35u source/result/checkpoint/seed/time/target/
  processor/sampler contract under new T20.35v spec, permit, attempt, and
  result identities and paths.
- Do not change a model, sampler, seed, threshold, comparison, or route merely
  to repair the runtime dependency surface.

## Runtime Preflight

A no-checkpoint, no-model, no-attempt mode must activate the exact LeRobot
stack and import every module used before and during dataset/model setup,
including `datasets`, `pyarrow`, `torch`, `safetensors`, processor/config/
dataset/factory/policy modules, and the local source package. It must also
verify MPS availability and the immutable T20.35t checkpoint tree. This mode
must pass in the exact command environment intended for the attempt.

## One-Use Boundary

Tests, implementation, signed spec, distinct one-use permit, successful exact
runtime preflight, same-agent adversarial review, scoped commit, push, and
remote confirmation must precede creation of the T20.35v attempt marker.
Exactly one inference-only evaluation attempt may then be consumed.

## Prohibited Actions

No U attempt reuse or deletion, optimizer creation or training, source/result
mutation, retry, extra state/seed/time, sampler or processor change, rollout,
Gate C, hardware, camera, serial, external compute, or Brev.

## Acceptance

The exact runtime preflight passes without creating an attempt; the distinct
attempt then reproduces all five T20.35t endpoints and emits one signed finite
trajectory result, or fails closed with a new non-reused failure artifact.
Gate B remains false unless unchanged objective and action gates pass in a
separately authorized evaluation.

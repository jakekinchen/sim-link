# Brief 187 - T20.35u Balanced Post-Training Trajectory Audit

## Objective

Localize why T20.35t passes both unchanged objective gates yet every decoded
action seed still exceeds 0.05 rad by reproducing the balanced checkpoint's
five complete ten-step denoising trajectories.

## Frozen Sources

- Bind T20.35t spec `34881e21...`, run `b5da8ab3...`, checkpoint
  `aeef380b...`, and result `f63ee934...`.
- Reuse the exact T20.35q target, source trajectories, processors,
  active-zero/padded-normal sampler, five seeds, and ten denoise steps.
- Reproduce all five T20.35t decoded endpoint hashes before interpreting any
  intermediate state.

## Audit Contract

Record every balanced-checkpoint state at steps 0 through 10. For each seed
and step, compare the active and padded state to the deterministic target, the
pre-correction T20.35p source path, and the signed T20.35t endpoint. Derive the
earliest material target-residual worsening and source-path displacement using
explicit signed thresholds. The classification may route one smallest
simulation-only discriminator; it cannot authorize training by itself.

## One-Use Boundary

Deterministic tests, implementation, signed spec, one-use inference permit,
same-agent adversarial review, scoped commit, push, and remote confirmation
must precede checkpoint tensor access or model construction. Exactly one
inference-only evaluation attempt may then be consumed.

## Prohibited Actions

No optimizer creation or training, source/result mutation, retry, extra
state/seed/time, sampler or processor change, rollout, Gate C, hardware,
camera, serial, external compute, or Brev.

## Acceptance

All source identities, checkpoint files, seeds, states, and endpoints verify
exactly; all recorded values are finite; and one signed result identifies the
earliest remaining path failure or records that the existing comparisons are
insufficient. Gate B remains false unless the unchanged objective and action
requirements both pass in a separately authorized evaluation.

## Pre-Run Boundary

Implementation `5c99e79`, signed spec `2575861c...`, and one-use permit
`bda88c46...` are remotely preserved. The contract binds Q source result
`6ba4954c...`, T run `b5da8ab3...`, T result `f63ee934...`, checkpoint
`aeef380b...`, the exact five base-noise and source/new endpoint hashes, and
ten denoise steps. Reviewer 232 authorizes exactly one Python 3.12 local-MPS
inference-only audit. Nineteen relevant tests, exact spec verification, and
the Python 3.12 model-free preflight pass. No T20.35u checkpoint tensor access,
model construction, inference, optimizer, rollout, hardware, external
compute, or Brev action occurred before authorization.

## Result

Attempt `179092b9...` was consumed once and failed closed while importing
LeRobot's dataset surface because the isolated Python 3.12 environment lacked
the `datasets` package. The failure occurred before checkpoint tensor access,
model construction, or inference; no result was emitted, the checkpoint tree
remains `aeef380b...`, and the attempt marker is retained. Signed failure
`0abd9650...` is preserved at `5700fb0`. Reviewer 233 closes T20.35u without a
retry and routes distinct T20.35v only after a dependency-complete runtime
preflight. Gate B and Gate C remain closed. No optimizer, rollout, hardware,
external compute, or Brev action occurred.

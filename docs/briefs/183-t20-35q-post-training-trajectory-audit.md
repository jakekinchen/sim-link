# Brief 183 - T20.35q Post-Training Trajectory Audit

## Objective

Explain why T20.35p's exact terminal-state correction passes both objective
checks yet worsens decoded actions by comparing its self-generated denoising
path with T20.35o's source path and the deterministic target flow.

## Frozen Inputs

- T20.35p checkpoint `9358cee4...`, result `cde1347f...`, and five decoded
  endpoint hashes.
- T20.35o normalized target and five complete 10-step source trajectories.
- Exact batch/processors, five base-noise tensors, active-zero/padded-normal
  mask, 10-step grid, checkpoint parameter boundary, and action conversion.

## Evidence

Run exactly five inference calls. Reproduce every T20.35p decoded endpoint,
retain each new pre-update state and learned velocity, and compute at each step:

- new-path residual to `(new_state-target)/time`;
- source-path residual from T20.35o;
- new-versus-source state and velocity displacement in active and padded
  dimensions;
- the earliest step where target residual or path displacement materially
  worsens.

Classify whether correction failure is early/mid-path interference,
off-trajectory terminal supervision, padded-state coupling, or a distributed
combination. This is diagnostic evidence, not an action correction.

## One-Use Boundary

Implementation, signed spec and permit, tests, same-agent adversarial review,
commit, push, and remote confirmation must precede checkpoint tensor access.
The runner writes an immutable attempt marker before model loading.

## Prohibited Actions

No optimizer, training, retry, extra condition/seed/step, sampler or processor
change, action correction, rollout, Gate C, hardware, camera, serial, external
compute, or Brev.

## Acceptance

All endpoint hashes reproduce; every retained tensor is finite and signed;
source/new/reference metrics recompute exactly; the earliest divergence and
classification are deterministic; and one next hypothesis is routed without
opening Gate B or Gate C.

## Pre-Run Boundary

Implementation `fbc1087`, spec `fdb2fe3e...`, and one-use permit
`ab85aede...` are remotely preserved. Reviewer 225 authorizes exactly five
Python 3.12 local-MPS inference calls after accepting the tensor-retaining
verifier, 0.01 material thresholds, classification precedence, and 40 passing
relevant tests. No model, checkpoint tensor, inference, optimizer, training,
rollout, Gate C, hardware, external compute, or Brev action occurred before
authorization.

## Result

The sole consumed attempt `57d0f2ec...` reproduced all five T20.35p decoded
endpoints and produced signed result `6ba4954c...`, remotely preserved at
`21ced86`. The corrected field worsens mean active target residual by
`0.067819` at step 0 and materially leaves the source path by step 2. Maximum
active state displacement is `0.078061`, larger than the padded maximum
`0.060895`, so padded-state coupling is not selected. Reviewer 226 verifies
early/mid-path interference, keeps Gate B and Gate C closed, and opens
T20.35r under Brief 184 for one separately reviewed full-path
self-consistency correction.

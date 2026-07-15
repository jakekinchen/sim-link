# Reviewer Decision 239 - Authorize One T20.36 Bounded Campaign

**Decision:** `AUTHORIZE_ONE_T20_36_LOCAL_MPS_CAMPAIGN_WITH_ORDERED_CONDITIONAL_EVALUATION`

## Reviewed Boundary

Brief 191; implementation commits `8da3cae` and `18f81e7`; signed spec
`522a1e5a...`; owner scope; central decision `25e63103...`; runtime proof
`04f2ce56...`; one-use permit `68d9042d...`; runner, renderer, tests, source
trees, branch, remote, and the complete scoped diff.

## Adversarial Findings

- The source is exact X checkpoint `40c94f66...`, whose signed result is the
  first unchanged Gate B pass. The runner verifies the complete checkpoint
  tree before attempt creation and repeats dependency and disk checks before
  any tensor read.
- The recovery dataset remains exactly ten episodes and 2,330 frames. Its five
  files are content-bound. The 500 standard-gradient samples are the exact 500
  unique official-sampler indices from T20.28; there is no implicit
  duplication, new data, changed statistics, or held-out leakage.
- Every update accumulates one full-coverage standard gradient and one X
  time-and-joint-weighted correction gradient before a single expert-only
  AdamW step. The X processor/statistics, correction examples, weights,
  optimizer, learning rate, update count, and unchanged Gate B are explicit.
- Gate order fails closed: a post-campaign Gate B miss emits no rollout; only a
  retained Gate B may run seed 0; a failed seed 0 emits no held-out rollout;
  only a strict-v2 seed-0 success permits seeds 6 then 7.
- Every reached rollout must be complete, unassisted, policy-owned, signed, and
  action-sequence-linked to its trace. Every trace automatically produces a
  signed, content-addressed MP4 manifest. The exact renderer source, FFmpeg
  8.0.1, MuJoCo 3.3.5, Pillow 12.3.0, and a real one-frame render are bound.
- The runtime recorded 23,132,839,936 free bytes and enforces a 6-GiB minimum
  again immediately before attempt creation. This protects the additional
  multi-gigabyte checkpoint and mirror outputs without deleting X evidence.
- Thirty-two relevant tests pass; lint, exact artifact verification, pointer
  checks, and diff checks pass. Duplicate AVFoundation class warnings from the
  co-installed OpenCV/PyAV libraries remain a recorded nonfatal caveat; the
  preflight opened no camera or hardware.
- No attempt directory exists. No checkpoint tensor, model, inference,
  optimizer, rollout, hardware, camera, serial device, external compute, or
  Brev action occurred. Physical transfer, promotion, and policy acceptance
  remain closed.

## Authorization

After remote confirmation of this decision, authorize exactly one local-MPS
T20.36 attempt under permit `68d9042d...`. The attempt may perform 500 paired
updates and only the evaluation episodes unlocked by its own prior gate
results. It may not retry, change a factor, access hardware, use external
compute, grant policy acceptance, or promote a result.

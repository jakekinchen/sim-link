# Reviewer Decision 237 - Authorize One T20.35x Joint-Weighted Attempt

**Decision:** `AUTHORIZE_ONE_T20_35X_LOCAL_MPS_ATTEMPT`

## Reviewed Boundary

Brief 190; commits `1c0fc1a` and `ff36b1b`; signed spec `96efc6d3...`;
training-only authority `a3a4eee7...`; runtime preflight `292a5b10...`;
one-use permit `c497dbed...`; exact verifiers; 22 lineage tests; runner
wrong-runtime rejection; canonical state; and the complete scoped diff.

## Adversarial Findings

- The exact T checkpoint `aeef380b...` is the immutable source. All 50 current
  V-path states and their learned-velocity hashes reconstruct exactly.
- Active weights come only from the dataset statistics bound by the signed
  manifest and the SO-101 coordinate contract. They average exactly 1.0; all
  26 padded coefficients remain 1.0. Raw, joint-weighted,
  time-and-joint-weighted, standard, and combined objectives are independently
  retained.
- Ten time weights exactly equalize the initial joint-weighted objective across
  denoise steps. The 50-example schedule is balanced at ten uses each.
- Every correction gradient is paired with one of 500 unique deterministic
  standard-replay seeds before the optimizer step.
- The unchanged Gate B contract remains standard-objective ratio at most 0.10
  of the original baseline plus every decoded action within 0.05 rad.
- The runtime proof binds Python 3.12, LeRobot 0.6.1, datasets 4.8.5,
  PyArrow 25.0.0, Torch 2.11.0, Safetensors 0.8.0, Transformers 5.5.4,
  local MPS, and the signed LeRobot stack. The normal runner repeats those
  checks before it can create the attempt marker.
- A PyArrow 24 invocation fails before any attempt path; the exact PyArrow 25
  invocation passes and leaves the permit unconsumed. This closes the stale
  runtime gap found during same-agent review.
- Duplicate AVFoundation class warnings from OpenCV/PyAV remain the recorded
  nonfatal import caveat. No camera or decoder is opened, and the warning grants
  no hardware authority.
- Spec, authority, preflight, permit, attempt, run, checkpoint, and result paths
  are distinct and immutable. No retry or second-attempt path exists.
- Gate C, rollout, hardware, physical transfer, promotion, external compute,
  and Brev remain closed.

## Disposition

Authorize exactly one invocation of the reviewed T20.35x runner in the exact
dependency-complete local-MPS surface. The attempt is consumed when its marker
is written. Any failure after that marker is a consumed negative result, not a
retry. Route only from the signed Gate B result.

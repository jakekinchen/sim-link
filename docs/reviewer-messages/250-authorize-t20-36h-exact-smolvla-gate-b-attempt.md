# Reviewer Decision 250 - Authorize T20.36h Exact SmolVLA Gate B Attempt

**Decision:** `AUTHORIZE_ONE_EXACT_LOCAL_SMOLVLA_GATE_B_ATTEMPT`

## Reviewed Boundary

Brief 199; design `fb217f3e...`; implementation `29b9525`; central decision
`b6b88518...`; static preflight `b7e2938f...`; one-use permit `5fa7c1d2...`;
canonical batch evidence; exact raw checkpoint hashes; 56 T20.36 tests; 12
pointer tests; exact verifiers; and the complete scoped diff.

## Adversarial Findings

- The policy checkpoint, both policy normalization tensors, and VLM checkpoint
  were read only as raw bytes and hashed. Sizes match the design; no safetensor
  was deserialized and no model was constructed.
- Source and remote are the exact same commit `29b9525` on the required branch.
  Scoped paths are clean, MPS is available, the canonical two-camera batch
  hashes reproduce, and 17,001,496,576 free bytes exceed the 6-GiB floor.
- Hub and Transformers offline modes are mandatory and MPS fallback is set to
  zero. Both policy and VLM constructors use exact local snapshot directories.
- The attempt marker is written before the first model import/construction.
  Construction/forward/backward smoke is part of the sole counted attempt; a
  smoke failure is signed, consumes the permit, and cannot retry.
- Runtime review requires all parameters and buffers on MPS and permits only
  the action expert, state projection, action in/out projections, and both
  action-time MLPs to train. Missing pathways, CPU fallback, or non-finite loss
  or gradients fail closed before an optimizer update.
- The constant-`1e-4` schedule, fixed objective/inference seeds, deterministic
  per-seed duplicate decodes, 0.10 objective ratio, 0.05-rad all-element gate,
  first-pass stop, 2,000-update ceiling, and selected-only checkpoint are exact.
  Neither outcome selects a policy or authorizes Gate C execution.

## Disposition

Commit and push this pre-run boundary. After the remote branch exactly contains
it, execute `run_t20_36h_exact_smolvla_gate_b.py` once in the pinned Python 3.12
environment. Preserve either its signed result or signed consumed-attempt
failure. No second attempt is authorized.

## Withheld Authority

No retry, sweep, network/download, CPU fallback, policy selection, Gate B
change, Gate C execution, rollout, simulation-policy acceptance, hardware,
external compute, or Brev.

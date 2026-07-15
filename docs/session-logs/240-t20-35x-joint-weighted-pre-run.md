# Session Log 240 - T20.35x Joint-Weighted Pre-run

## Evidence

- Implementation commits: `1c0fc1a`, `ff36b1b`.
- Training spec: `96efc6d35115126268684c91346b7388077342c573e458b7e708e98714113cfd`.
- Central authority: `a3a4eee706162dfa3df88ad3fc20a23e4487a432592c2e1d454ab3dd56340b1a`.
- Runtime preflight: `292a5b10c66b208bf87947840639be5b4ea5e7cb575e91d5c3331df7e1c041b9`.
- One-use permit: `c497dbed89c5d5ae3b0a512b6e4d0237d4271d721b4326dc938f7a9ce0523e24`.
- Twenty-two focused lineage tests pass; eight T20.35x tests pass after runner
  hardening. Exact spec, authority, runtime, permit, and runner preflight
  verifiers pass.

## Boundary

The wrong PyArrow 24 runtime fails before attempt creation. The reviewed
PyArrow 25 runtime passes without consuming the permit. Reviewer 237 authorizes
one local-MPS training/evaluation attempt. No checkpoint tensor, model,
inference, optimizer, rollout, hardware, external compute, or Brev action has
occurred. Gate B is false and Gate C remains closed pending the signed result.

# Reviewer Decision 243 - Verify T20.36c Local Policy-Track Preflight

**Decision:** `VERIFY_METADATA_PREFLIGHT_ROUTE_EXACT_ACT_CONTROL_DESIGN_ONLY`

## Reviewed Boundary

Brief 194; exact local LeRobot source and dirty-path evidence; canonical T20.23
dataset metadata; ACT and SmolVLA cache inventory; signed report
`61fcf124...`; implementation commit `139fe32`; deterministic tests; and the
complete scoped diff.

## Adversarial Findings

- Every `.safetensors`, `.pt`, `.pth`, or `.bin` entry is stat-only, records
  `content_read=false`, and has no content hash. A guarded loader test aborts
  if any tensor read is attempted.
- Source HEAD and nine relevant source hashes are pinned. The two unrelated
  existing LeRobot dirty paths are recorded without modification. Stale source
  or an aliased cache path fails closed.
- ACT's prior MPS proof is real but is only T20.2 evidence. The cached ACT
  candidate has different camera keys/resolution and a 100-step chunk, so it
  cannot stand in for the exact current Gate B control.
- SmolVLA's base and VLM metadata is complete, and its six-joint/50-step shape
  matches. Its cached three-camera processor does not match the canonical
  two-camera dataset, and source compatibility is not MPS runtime proof.
- Twenty-three relevant tests pass; exact artifact verification, lint,
  compilation, diff, pointer, and workflow checks pass.
- The report keeps all authority fields false. Cache presence makes no model
  performance or checkpoint-integrity claim and selects no policy.

## Disposition

Verify T20.36c. Open Brief 195 for the exact ACT one-batch control specification
and adversarial verifier only. The design must use fresh explicit ACT
initialization and the canonical shared data/normalization contract; the cached
third-party ACT checkpoint is not a shortcut.

## Withheld Authority

No network, checkpoint tensor read, model load, inference, optimizer, ACT run,
SmolVLA entry, policy selection, Gate B change, Gate C, rollout, policy
acceptance, hardware, external compute, or Brev.

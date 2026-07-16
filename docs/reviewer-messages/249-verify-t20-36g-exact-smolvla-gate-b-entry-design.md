# Reviewer Decision 249 - Verify T20.36g Exact SmolVLA Gate B Entry Design

**Decision:** `VERIFY_EXACT_SMOLVLA_GATE_B_DESIGN_ROUTE_PRE_RUN_IMPLEMENTATION`

## Reviewed Boundary

Brief 198; T20.36c, T20.36d, and T20.36f signed sources; pinned SmolVLA,
processor, checkpoint-loader, and batch/normalization source files; spec
`fb217f3e...`; implementation `1c5faf3`; 47 relevant tests; exact regeneration;
and the complete scoped diff.

## Adversarial Findings

- The cached three-camera map is replaced before construction by the two exact
  canonical base/wrist keys with `empty_cameras=0`; padding, duplication,
  synthesis, aliasing, and silent drops are rejected.
- Policy and VLM constructors point to exact local snapshot directories with
  hub and Transformers offline modes required. Mutable repository resolution,
  network fallback, and CPU fallback are forbidden.
- Review caught and removed an inherited ACT processor reference. The final
  contract names the SmolVLA processor and requires `default_collate` because
  LeRobot's batch step does not batch a rank-2 horizon action chunk.
- Pretrained expert-only plus state projection is the sole trainable scope.
  The VLM and vision encoder remain frozen; runtime trainable, dtype, buffer,
  device, finite-loss, and finite-gradient inventories are mandatory.
- The 0/100/250/500/1,000/2,000 schedule, constant `1e-4` AdamW, fixed seeds,
  unchanged 0.10 objective ratio, and unchanged 0.05-rad all-element gate are
  frozen. Scheduled evaluations stay in memory; only the selected pass or
  terminal checkpoint is saved and hashed.
- Pass/fail routes remain bounded. The design cannot select SmolVLA, amend Gate
  B, authorize Gate C, claim simulation success, or grant physical authority.
  No checkpoint tensor, model, inference, optimizer, hardware, network,
  external-compute, or Brev action occurred.

## Disposition

Verify T20.36g. Open Brief 199 for pre-run implementation, raw checkpoint-file
integrity hashing, exact runner/verifier construction, static preflight, and a
task-specific central decision. No attempt or model access may occur until that
separate boundary is reviewed, committed, pushed, and confirmed on origin.

## Withheld Authority

No attempt marker, tensor deserialization, model construction/load, inference,
optimizer, training, retry, policy selection, Gate B change, Gate C, rollout,
hardware, network, external compute, or Brev.

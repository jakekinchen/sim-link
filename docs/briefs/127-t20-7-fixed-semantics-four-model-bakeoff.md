# Slice Brief 127 - T20.7 Fixed-Semantics Four-Model Bake-Off

**Date:** 2026-07-14

## Objective

Compare PI0.5, SmolVLA, ACT, and Diffusion Policy on one source-bound grasp
dataset under the same sample schedule and closed-loop strict semantics. Do not
reuse the existing ACT and PI0.5 outcomes as if they were paired: their update,
batch, chunk, and sample schedules differ.

## Contract

- Revalidate central simulation authority before every model load or optimizer
  run. Use local MPS only; external compute and Brev remain forbidden.
- Bind the T20.1 tensor view, T20.6 semantic fixture, exact train/evaluation
  split, task prompt, held-out episode seed 2, inference seed 1703, canonical
  coordinates, and one immutable common sample-start plan.
- Use a 50-action supervision chunk and exactly the same ordered source starts
  for every model. Absolute losses are model-specific diagnostics; closed-loop
  strict behavior is the comparison surface.
- PI0.5 and SmolVLA begin from their complete pinned local base snapshots with
  bounded rank-4 LoRA. ACT uses the reviewed compact T20.2 architecture with a
  50-action chunk. Diffusion Policy uses a compact local configuration with no
  downloaded backbone or unrecorded pretrained weights.
- First run a four-model load/preprocess/forward/backward canary. Continue only
  when all four models produce finite loss and gradients on the same sample.
- A comparison artifact must record exact samples seen, model/checkpoint and
  runtime identities, parameter counts, loss margins, action-sequence hashes,
  assist/projection counts, five 256 px keyframes, every strict measured-versus-
  threshold gate, terminal outcome, and T20.6 outcome-versus-strict semantics.

## Acceptance Criteria

- All four canaries and any continued rung use the same ordered source starts;
  missing, skipped, retried, or model-specific samples fail the paired gate.
- Every checkpoint and rollout is immutable and source-bound. A missing model,
  non-finite value, preprocessing mismatch, or unavailable local dependency is
  recorded as a negative readiness result, never silently substituted.
- No winner is named from training loss. Ranking requires the same policy-owned
  closed-loop proof mode, seeds, horizon, strict gates, and rendered keyframes.
- The same-agent review explicitly checks sample equality, initialization
  asymmetry, evaluator leakage, assistance, action projection, stale identities,
  and unsupported policy-acceptance claims.

## Out Of Scope

External downloads, external compute, Brev, hardware, physical transfer,
promotion, T20.8 acceptance, and changes to the T20.6 evaluator.

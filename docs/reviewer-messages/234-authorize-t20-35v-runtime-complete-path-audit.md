# Reviewer Decision 234 - Authorize T20.35v Runtime-Complete Path Audit

**Decision:** `AUTHORIZE_ONE_DISTINCT_T20_35V_INFERENCE_ONLY_TRAJECTORY_AUDIT`

## Reviewed Boundary

Brief 188, implementation `d1861f3`, spec `a0b5c211...`, permit
`304b956b...`, runtime preflight `59ecc86c...`, consumed U attempt/failure,
Q source paths, T run/checkpoint/result, runner, tests, canonical state, and
the complete scoped diff were reviewed before any V attempt exists.

## Adversarial Findings

- T20.35u attempt `179092b9...` remains present and consumed. T20.35v uses
  distinct spec, permit, attempt, result, and runtime-preflight paths and cannot
  delete or reuse U evidence.
- The runtime preflight activated the exact signed LeRobot source stack under
  Python 3.12 and imported dataset/config/policy/processor/checkpoint modules
  plus `datasets 4.8.5`, `pyarrow 25.0.0`, `torch 2.11.0`, `safetensors 0.8.0`,
  and `transformers 5.5.4`. MPS was available.
- The runtime emitted duplicate AVFoundation class warnings from OpenCV/PyAV,
  but completed cleanly. This slice opens no camera or video decoder; the
  warning grants no hardware authority and remains a runtime caveat.
- Preflight `59ecc86c...` records no V attempt/result, no checkpoint tensor
  read, no model/inference, and the exact `aeef380b...` checkpoint tree.
- Before creating an attempt, the normal path must repeat the full import
  surface and exactly match every preflight dependency version. A dependency
  failure or version drift therefore leaves the V permit unconsumed.
- Five seeds, ten denoise steps, active-zero/padded-normal masking, targets,
  processor, sampler, Q source paths, and T endpoints are unchanged.
- Optimizer creation/training, checkpoint mutation, rollout, Gate C, hardware,
  external compute, and Brev are denied. Twenty-three relevant tests and all
  signed/model-free/runtime verifiers pass after remote preservation.

## Disposition

Authorize exactly one distinct Python 3.12 local-MPS T20.35v inference-only
audit under permit `304b956b...`. Use the exact reviewed offline
`lerobot[dataset,pi]` environment. Interpret only its signed result. Do not
retry, create an optimizer, train, enter Gate C, access hardware, or start
external compute.

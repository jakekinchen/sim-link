# Brief 199 - T20.36h Exact SmolVLA Gate B Pre-Run

## Objective

Implement, test, centrally compose, and remotely preserve the exact one-use
SmolVLA Gate B runner defined by T20.36g without creating its attempt marker,
constructing a model, loading tensor content, running inference, or creating an
optimizer at this boundary.

## Frozen Inputs

- T20.36g spec `fb217f3e...` and implementation
  `1c5faf315e09bebff5de681d7e06de6787f1a8cb`.
- Exact local policy and VLM snapshot directories, pinned LeRobot head, source
  hashes, canonical two-camera episode-0 batch, T20.23 MEAN_STD statistics,
  joint order, horizon, seeds, schedule, optimizer, stop rules, and unchanged
  Gate B from that spec.
- Current local-MPS simulation-training authority window. Hardware, network,
  external compute, and Brev remain closed.

## Required Implementation

1. Verify the signed design and all source identities before any runtime import.
2. Hash every exact policy/VLM weight and processor tensor file as raw bytes,
   without safetensor deserialization, and bind those hashes plus file sizes to
   a signed static preflight.
3. Fail closed on wrong branch/commit/remote, dirty scoped paths, missing MPS,
   insufficient disk, expired authority, cache/source drift, network fallback,
   or any existing attempt marker.
4. Implement the exact offline constructor, canonical `default_collate` batch,
   SmolVLA processors, MPS construction/forward/backward smoke, trainable and
   dtype/device inventories, constant AdamW loop, scheduled deterministic
   evaluations, finite-value checks, early-pass/terminal stop, selected-only
   checkpoint, signed result, and exact verifier.
5. Compose a task-specific one-use central decision and permit bound to the
   reviewed remote implementation commit and current window. The later smoke is
   part of the sole counted attempt; a smoke failure consumes it and permits no
   retry.

## Acceptance

- Deterministic unit tests cover source/spec/permit drift, stale or duplicate
  attempts, camera aliases, batching, offline snapshot paths, non-finite values,
  device fallback, schedule/gate drift, and conservative result claims.
- The implementation, static preflight, central decision, permit, brief, state,
  reviewer decision, and remote branch agree before execution.
- A fresh same-agent review authorizes at most one T20.36h attempt only after
  the reviewed boundary is confirmed on origin.

## Prohibited Actions

Attempt-marker creation, safetensor deserialization, model construction/load,
inference, forward/backward smoke, optimizer creation/training, retry, sweep,
policy selection, Gate B amendment, Gate C, rollout, hardware, camera, serial,
network/download, external compute, or Brev before the reviewed remote pre-run
boundary.

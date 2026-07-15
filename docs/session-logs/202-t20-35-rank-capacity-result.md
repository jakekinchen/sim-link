# Session Log 202 - T20.35 Rank-Capacity Result

## Execution

- A Python 3.14 invocation rejected the pinned Draccus policy config before the
  attempt marker, model construction, or optimizer. It did not consume the
  reviewed one-run permit.
- The compatible locked Python 3.12 runtime passed config and MPS preflight.
- Signed attempt `f58f435a...` consumed the one-run permit before model
  construction at 07:58:27 CDT.
- Exactly 500 rank-16 local-MPS updates completed. All 500 objectives and
  pre-clip gradient norms are finite; no retry or continuation occurred.

## Evidence

- Run: `6e0dd4e2003fa78f5d82cf38414cf6763444c27a44e797f30ff99c3097cd5dbe`.
- Checkpoint: `0dea38b3135a4f1957bcd1fd7f3e78ca77fc2096eff5e2c75f0a3d9365f22032`.
- Result: `99538521686cf3e3ea16df352e12ddd7d02613bd2fdd2a9877ebe16e9b036ca8`.
- Remotely preserved result implementation: `fd9399d959500f6cc439b6ad0fe7f29a7eea54ac`.
- Trainable parameters: 1,287,168, exactly four times T20.33 rank 4.
- Baseline/final five-seed objective: `0.959079` / `0.148952`; ratio
  `0.155307` versus required `0.10` and prior rank-4 `0.528248`.
- Every mean decoded error improves versus rank 4 by 0.157864-0.249830 rad,
  but maximum errors remain 0.708520-1.467995 rad versus required 0.05.

## Decision

Gate B fails. Rank capacity materially helps objective fit and average decoded
action error but is insufficient under the frozen budget, and worst-joint
decoded errors remain large. No retry, continuation, Gate C work, campaign,
policy acceptance, hardware, external compute, or Brev is authorized. Route
first to the optimizer-free exact PEFT module/tensor coverage audit.

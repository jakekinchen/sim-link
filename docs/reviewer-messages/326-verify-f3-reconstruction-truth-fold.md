# Reviewer Decision 326 - Verify F3 Reconstruction Truth Fold

**Date:** 2026-07-17

## Decision

`VERIFY_F3_RECONSTRUCTION_TRUTH_FOLD_AND_AUTHORIZE_BOUNDARY_TAG_AFTER_ORIGIN`

Brief 233 satisfies its current-truth reconstruction acceptance criteria.
The sim2claw capsule now answers what is proven, why learned release remains
unsolved, which architecture survives into the fork, how to reproduce the
runtime/data/evidence boundary, and which failed paths must not be repeated.

## Verified evidence

- origin contains implementation `48970159ccd14de6d93fed8a7f318eafcc64b777`
  and source-pin commit `8066e59b515edba848e221aadddb26e5bb104b1d`;
- manifest `ec9084dc...` selects 444 files / 81,458,869 bytes, retains the full
  replayable F0b trace, and hashes 11 deliberate omissions including every
  consumed F0b authority/preflight/permit artifact;
- pristine export `57b4623b...` independently verifies 465 files / 81,798,833
  bytes without signing its ephemeral absolute scratch path;
- offline W1 bootstrap `bd2c9575...` uses Python 3.12.12, passes 29 focused
  tests, generates one strict 244-frame expert episode, and renders all three
  retained trace schemas;
- retained W2 receipt `86739578...` independently passes signature and exact
  expected/observed equality with `mismatches={}`; seven deterministic R0
  contracts pass, and the 4,425-second isolated generation is not repeated;
- F3 receipt `bf488607...` binds the seven immutable T20.43c-R2 identities,
  F0/F0a/F0b results, manifest, export, W1, W2, and the complete test ledger;
- final wrapper export `480059b3...` verifies the reconciled kit
  bytes used by this closeout.

## Verification ledger

- reconstruction-kit tests: 13 pass;
- documentation information-architecture tests: 6 pass;
- project-state pointer tests: 15 pass;
- F0/F0a/F0b tests under the pinned LeRobot runtime: 27 pass;
- R0 regeneration contracts: 7 pass;
- fresh-export W1 focused tests: 29 pass;
- manifest check/verify, portable asset identity `935c3da1...`, strict JSON,
  Python compilation, and `git diff --check`: pass.

## Same-agent adversarial review

The review preserves the exact T20.43c-R2 terminal negative and does not
relabel the original update-728 interruption. It preserves F0's rejected
tail/normalization/aggregate-loss explanations, F0a's 20/24 source aliases
without claiming candidate-image equality, and F0b's cadence-only terminal
negative. No third ACT attempt or corrective rung is implied.

The fork remains subtractive: one pinned LeRobot interpreter, in-process
rendering, camera-free 60-frame state tasks for fast RL, ACT plus state-RL as
primary, CPU/fp32 evaluation, one workcell XML plus task registry, one gateway,
ignored human-named outputs, and auto-emitted run receipts. Frozen held-out
data, replayable artifacts, and separate evaluator ownership remain intact.

No non-finite value, path traversal, symlink alias, stale-permit activation,
authority escalation, learned Gate C success, W3 completion, W5 gRPC or
policy-quality claim, F1/Brev execution, model/checkpoint action, optimizer,
training, rollout, hardware, network acquisition, external compute, transfer,
promotion, or destructive cleanup appears. `.codex/config.toml`, `external/*`,
and `tmp/*` remain unrelated and unstaged.

## Disposition

F3 is verified and closed. After the scoped closeout commit containing this
decision is pushed and its exact SHA is confirmed on origin, create one
annotated tag `freeze-2026-07-17-hackathon-fork` on that exact commit and verify
the remote tag. The tag records an immutable source boundary only; it grants no
training, hardware, transfer, promotion, network, external-compute, Brev, or
live-authority state. No new source-repo model task is activated.

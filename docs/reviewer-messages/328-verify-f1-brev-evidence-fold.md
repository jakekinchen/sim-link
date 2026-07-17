# Reviewer Decision 328 - Verify F1 Brev Evidence Fold

**Date:** 2026-07-17

## Decision

`VERIFY_F1_COMPLETED_NEGATIVE_NO_GATE_C_NO_NEW_AUTHORITY`

Brief 235 and implementation `fc46257b67b97b927ac6b8d8bda2ec243d62b572`
honestly reconcile the completed off-ledger F1 experiment into the canonical
spine. This is a historical evidence fold, not another model action.

## Verified source evidence

- Run receipt `ca9a23b183c9854266d3960b66bc60f0d7cf4aea8d0dc40ad96293e9201d8716`
  recomputes exactly from file SHA-256 `d7677389...`.
- Evaluation summary `992cf3fdd3f12c8543b643000691504003a080ff063fbedf98992425ab7a0b50`
  and all ten individual rollout identities recompute exactly.
- The run is one ABEJA-parity full fine-tune of `lerobot/pi05_base`: 5,000
  updates, checkpoints 1,000/2,000/3,000/4,000/5,000, two fixed variants,
  ten rollouts, and zero strict successes. The evaluator's first headless-GLFW
  startup failed before a rollout; the bounded EGL attempt completed all ten.
- The frozen selection is checkpoint 1,000/chunk-50, rollout
  `e03c690e...`, with `0.03751930418757199` m maximum lift and only
  `grasp_hold_strict_v2` failing. Gate C is false. This is not a successful
  policy or gateway result.
- Spend receipt `c949abbf...` records `$5.526` calculated from the displayed
  `$1.656/hour` rate over 12,014 seconds, explicitly not a provider invoice.
- Teardown receipt `7343ad9fc1bc1802ec00bd13eab65807ca2d41818c8d59210957b980b2b66064`
  records delete request at 06:10:23 CDT, confirmation at 06:10:58, and final
  inventory at 06:11:07 with zero resources.

## Retention and live cost control

The selected seven-file checkpoint remains outside Git at
`/Volumes/cerebro/CodexOffload/f1-pi05-r0-20260717/checkpoint-001000/pretrained_model`.
Direct read-only hashing, without tensor deserialization, reproduced model
SHA-256 `755544956570297f09f72c48874f5dc9643e02f14a0c934109b81a9e66aec7fb`
and config SHA-256
`1f17178a8bf1a7d62f9ef89673b79eb4ef839158485e5c09dda2ad9c4eb125d9`.
No model/checkpoint bytes or external clones entered Git.

Fresh authenticated `brev ls --json` at 09:34:41 CDT returned
`{"workspaces": null}`. No cleanup mutation was necessary and no Brev resource
remains.

## Canonical evidence and tests

Signed fold `1e9334299675e42e3104c3d49f29909afa21e7f6eea43ff881221738c7147755`
is tracked at file SHA-256 `f2ff09c0...`. Six focused F1 tests, thirteen
reconstruction-kit tests, six documentation tests, and fifteen project-state
pointer tests pass. Strict JSON, signed identity verification, link resolution,
and `git diff --check` pass.

## Same-agent adversarial review

The fold distinguishes historical Brev execution from canonical fold actions,
records the pre-rollout renderer startup failure without relabeling it as a
training retry, and rejects false Gate C, gateway, policy-success, physical,
transfer, promotion, or authority claims. Absolute paths are evidence pointers,
not portable content identities; every source receipt also carries its exact
identity and file digest. The compact pointer does not pretend the off-repo
checkpoint is remotely retained.

F0/F0c/F2/F3 are not reopened. F0c spec `6a178138...` remains at file SHA-256
`9ff87253...`; F3 manifest `ec9084dc...` is unchanged; annotated tag
`freeze-2026-07-17-hackathon-fork` still targets `04a52929...`. No training,
model construction/load/inference, optimizer, rollout, hardware/camera/serial,
external-compute start, Brev creation, destructive action, or gateway work
occurred in this fold. `.codex/config.toml`, `external/*`, and `tmp/*` remain
unrelated and unstaged.

## Disposition

F1 is verified and closed as a completed terminal PI0.5 negative with no Gate C
pass. The current fork route remains F0c packaging followed by its separately
reviewed future execution; the F1 result changes the evidence record, not live
authority or policy priority.

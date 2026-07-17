# Reviewer Decision 327 - Verify F0c Fork-Day-One Package

**Date:** 2026-07-17

## Decision

`VERIFY_F0C_PACKAGED_FOR_FORK_DAY_ONE_NO_EXECUTION`

Brief 234 satisfies the owner's completion-budget stop rule. The full reviewed
implementation, authority, one-attempt continuation, rollout, preservation,
and closeout boundary could not fit before 10:00 CDT, so no partial run began.
F0c is instead preserved as the sim2claw fork's first exact training task.

## Verified evidence

- activation `126121d28b2c495332a71436b2313e0ccb54c69f` and implementation
  `91bb87695f6676a06371aa146240c60b39e0a59b` are exact on origin;
- signed spec
  `6a178138f79236f27adc04b337e0142a5dfa851f1f67d32d55dcc8b41e4da5dd`
  is tracked at file SHA-256 `9ff87253...` and deterministically reconstructs
  from the immutable R2/R0/F0/F0a/F0b sources;
- the R2 update-10,000 checkpoint tree remains `c77ee362...`; the package
  hashes its two unaliased regular files without deserializing tensor values or
  modifying the checkpoint;
- the correction freezes release/release-settle start weights at 4.0, all
  other eligible starts at 1.0, F0's active-mean-one physical-L1 coefficients,
  fresh AdamW, seed 20260801, and a 2,000-update ceiling;
- chunk-50 is the only evaluation variant at updates 0/500/1000/2000, with
  starts `[0,50,100,150,200]`, executed lengths `[50,50,50,50,44]`, strict-v2
  unchanged, first-pass stop, and no retry or receding-10;
- pristine post-freeze export `dce41616...` independently verifies 467 files
  and carries the exact spec bytes plus the F0c explainer while retaining F3
  manifest `ec9084dc...` unchanged;
- remote tag `freeze-2026-07-17-hackathon-fork` still targets immutable F3
  closeout `04a52929...`; F0c does not move or reinterpret that tag.

## Verification ledger

- F0c deterministic package tests: 7 pass;
- reconstruction-kit tests: 13 pass;
- documentation information-architecture tests: 6 pass;
- project-state pointer tests: 15 pass;
- package `--check`, manifest check/verify, portable asset verify, strict JSON,
  export/independent verify, and `git diff --check`: pass.

## Same-agent adversarial review

The package rejects source identity drift, checkpoint byte drift, path aliases,
budget escalation, correction/schedule changes, and false execution/authority
claims. The exported JSON is receipt-bound outside the frozen F3 source
manifest, avoiding both a stale pointer and a silent manifest repin. The
checkpoint itself is deliberately absent from the kit and must later arrive
through a separately licensed checksum-bound channel.

No attempt marker, checkpoint tensor read, model construction/load/inference,
optimizer creation, training, rollout, Gate C execution, dataset/statistics
mutation, retry, receding-10 investigation, hardware/camera/serial access,
network acquisition, external compute, Brev, transfer, promotion, destructive
operation, or F1/F2/F3 reopening occurred. Learned strict-v2 success remains
false. `.codex/config.toml`, `external/*`, and `tmp/*` remain unrelated and
unstaged.

## Disposition

F0c is verified and closed only as `packaged_for_fork_day_one`. The fork's next
eligible work is to implement and independently review the frozen runner,
acquire/bind the exact checkpoint, and materialize fresh fork-native authority
before executing the one attempt. This decision grants no optimizer or rollout
authority in either repository.

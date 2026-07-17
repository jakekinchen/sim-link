# Reviewer Decision 325 - Verify F0b Hybrid Tail-Cadence Terminal Negative

**Date:** 2026-07-17

## Decision

`VERIFY_F0B_TERMINAL_NEGATIVE_ROUTE_TO_F3_RECONSTRUCTION_FOLD`

Brief 232 completed its sole authorized evaluation. Result preservation commit
`2d39bcc076c7328364777712cd1bf7828bc1cae9` is exact on origin. Signed result
`8fb34ff4...` is a clean learned-policy negative under the unchanged strict-v2
Gate C evaluator, not an infrastructure failure and not a retry grant.

## Verified execution

- Attempt marker `274356f5...` was written before one construction/load of the
  exact update-10,000 ACT checkpoint `c77ee362...`.
- One seed-0, 244-frame rollout used decode starts
  `[0,50,100,150,176,186,196,206,216,226,236]` and executed lengths
  `[50,50,50,26,10,10,10,10,10,10,8]`. The trace retains all eleven 50x6
  decoded chunks, the exact 24-action frame-176 discard, two selected but
  unexecuted terminal actions, all observed physics frames, and source
  comparisons.
- The run created no optimizer, performed no training, changed no dataset,
  statistics, or evaluator threshold, and used no retry, network, external
  compute, Brev, camera, serial device, robot hardware, or physical motion.
- Independent unchanged strict-v2 replay reproduces the one failed predicate:
  `release_final_contact_clear`, measured 0 versus required 1. Every grasp,
  lift, hold, lower, support-free, no-assist, no-projection, and retreat-final
  predicate passes. Maximum anchor lift remains exactly
  `0.037655304225193253` m.

## Mechanism disposition

The hybrid trace and original chunk-50 comparator are action-identical through
frame 175. Requested and applied actions first diverge at frame 176; qpos,
qvel, and anchor state first diverge at frame 177. Thus the result isolates the
cadence intervention rather than a checkpoint, seed, initial-state, or gate
change.

The intervention changes the lower/release/retreat tail and increases strict
retreat-contact frames from 1 to 17. It does not clear contact at the frozen
release-final frame 219: both fingertip pad geoms are still present and strict
contact remains true. The final frame 243 is contact-free only after the object
has returned to desk height. The candidate therefore opens too late for the
unchanged task cycle. Hybrid observation cadence is useful diagnostic control,
but it is not sufficient to unlock Gate C for this checkpoint.

No conclusion is drawn that cadence can never help a differently trained
policy. The narrower supported conclusion is that F0a's cadence/gate mechanism
does not repair the retained update-10,000 ACT policy without training.

## Evidence preservation and review

- trace identity `af62a3b5...`, tracked file SHA-256 `831a1075...`;
- result `8fb34ff4...`, scorecard `c24cd471...`, retention `4c3c74d0...`, and
  final receipt `7b7f4f77...`;
- signed result mirror manifest `acaa395a...`, tracked byte-for-byte at file
  SHA-256 `300f2906...`; its local gitignored 244-frame MP4 is 629,126 bytes
  with SHA-256 `db088a4d...`;
- live output verifier: pass; fresh focused F0b unittest suite: 15 pass;
- marker/result/trace/scorecard/retention/final exclusivity and all signed
  identities reconstruct; repository-relative references and output aliases
  fail closed;
- result commit, upstream, and origin branch were exact before this closeout.

The tracked trace makes the verdict and contact timing independently
replayable from a fresh checkout. The MP4 bytes themselves are not remotely
preserved, so only its signed manifest and hash are remotely auditable.

## Authority disposition

F0b is verified and closed. No retry, additional checkpoint or seed, corrective
ACT rung, F1/Brev run, hardware action, physical transfer, promotion, or freeze
tag follows. The one owner-authorized corrective ACT rung remains unselected
and unconsumed. After this closeout is exact on origin, the next eligible task
is a fresh F3 brief to fold the R2/F0/F0a/F0b ground truth into the portable
reconstruction kit, reconcile stale documentation, verify the fork bootstrap,
and prepare the separately governed freeze boundary.

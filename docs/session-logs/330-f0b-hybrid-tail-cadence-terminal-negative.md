# Session 330 - F0b Hybrid Tail-Cadence Terminal Negative

**Date:** 2026-07-17

**Task:** F0b / Brief 232

**Reviewer:** 325

## Outcome

F0b consumed its one-use permit once and completed cleanly. Marker
`274356f5...` precedes one load of retained ACT checkpoint `c77ee362...` and one
seed-0 hybrid-tail rollout. Result `8fb34ff4...` is
`verified_terminal_negative`: Gate C executed and remained false, with no
infrastructure failure, optimizer, training, retry, dataset/statistics change,
or extra model/checkpoint/seed action.

The cadence schedule preserved chunk-50 through frame 175, discarded exactly
24 queued actions at frame 176, and re-decoded every ten actions thereafter.
The full tracked trace `af62a3b5...` retains eleven decoded chunks, 244 observed
frames, the discarded suffix, two terminal unexecuted actions, source
comparisons, and independent strict-v2 replay. Signed mirror manifest
`acaa395a...` binds the local 244-frame MP4 at SHA-256 `db088a4d...`; the
manifest is tracked, while the MP4 bytes remain gitignored local diagnostic
evidence.

## Finding

The new and original chunk-50 policies execute identical actions through frame
175 and diverge only at the planned frame-176 re-observation. Hybrid cadence
changes the late tail and raises strict retreat-contact coverage from 1 to 17
frames, but it still fails only `release_final_contact_clear`. At frame 219
both fingertip pad geoms remain in strict contact. Contact clears by the final
retreat frame only after the anchor returns to desk height. Maximum lift stays
exactly `0.037655304225193253` m.

This falsifies cadence alone as the repair for the retained checkpoint. It
does not weaken the frozen gate or erase the substantive learned grasp, lift,
hold, and lower capabilities.

## Verification and disposition

The pinned LeRobot runtime passes the live output verifier and 15 focused F0b
tests. Same-agent review confirms exact source/checkpoint/seed binding,
marker-first execution, terminal exclusivity, replayable tracked evidence, and
no authority escalation. Result preservation commit `2d39bcc...` is exact on
origin.

F0b closes without retry and without consuming the corrective ACT rung. F3 is
next eligible as a fresh reconstruction-kit/current-results fold. F1/Brev,
hardware, transfer, promotion, and the freeze tag remain closed.

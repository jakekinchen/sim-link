# Executor Session 021 - MPS Rung 250

**Date:** 2026-07-10

## Slice

Run, finalize, reload, and evaluate the first corrected PI0.5 MPS training rung,
then stop before rung 500 for owner review.

## Result

- Completed exactly 250 audited MPS updates in 481 seconds with 125 base and
  125 correction draws; each of five correction phases contributed 25 draws.
- Final loss was 0.193 and final gradient norm was 4.056, with finite training.
- Finalized checkpoint 000250 against the pinned normalizer, recorded complete
  model/runtime/data provenance, and reloaded the standalone checkpoint on MPS.
- Ran the accepted baseline and candidate on the same four rotating development
  seeds, 1,000 policy steps each, strict neural proof mode, no assistance, and
  no physical hardware.
- Candidate mean reach rate improved from 0.500 to 0.625. Contact remained 0.250.
  Grasp, lift, transport, release, placement, sorted count, and success remained zero.

## Decision

`RUNG EVIDENCE ACCEPTED - CHECKPOINT NOT PROMOTED - PAUSE BEFORE 500`

The rung met its declared engineering gates and showed a narrow upstream stage
improvement. Development seeds are not promotion evidence, and the lack of any
grasp/downstream improvement means the accepted checkpoint pointer stays unchanged.

## Proof Boundary

This proves a reproducible local train-finalize-reload-evaluate loop for PI0.5 on
Apple MPS and a measurable development change. It does not prove autonomous sorting,
generalization, sim-to-real transfer, or physical-robot competence.

## Next Step

Present the current capability rundown to the owner and incorporate their advice
before starting rung 500.

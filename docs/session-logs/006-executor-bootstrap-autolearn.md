# Executor Session 006 - real MPS autolearn bootstrap

**Date:** 2026-07-10

## Slice

Run one real end-to-end autolearn cycle on Apple MPS and prove Git stage
boundaries, DAgger aggregation, finite adapter training, standalone candidate
reload, held-out evaluation, and rollback.

## Result

The cycle completed as a system and rejected the model candidate:

- baseline seed 6301: 0/4 pure-policy sort at the 200-frame bound;
- collection seed 6204: 4/4 hybrid completion from 2,559 neural frames;
- DAgger export: 660 explicit expert-correction frames;
- aggregate: 9 episodes and 11,316 frames including the 10,656-frame base;
- training: five MPS optimizer steps, 23,045,376 learnable parameters, 92 MB
  adapter artifact;
- candidate seed 6301: 0/4 pure-policy sort at the same bound;
- decision: rejected for `candidate_below_pure_success_threshold`;
- accepted V10 checkpoint pointer unchanged.

## Git Evidence

The runner committed baseline, collection, export, aggregation, failure,
checkpoint finalization, candidate evaluation, and rejection as separate
boundaries. The source implementation commits are `58d63e9`, `841a32d`, and
`f19d591`.

## Repair During The Slice

LeRobot saved the trained PEFT adapter without the policy `config.json` needed
by standalone inference. The first training attempt was recorded as a failed
artifact contract. A deterministic finalization stage and argv/artifact-checked
resume path were added and tested; the successful five-step training was not
rerun or hidden.

## Proof Boundary

This is the first successful automated learning-cycle execution on MPS. It
proves the flywheel, candidate reload, and safe rollback. It does not prove
autonomous sorting or statistically meaningful improvement.

## Next Suggested Slice

Run restored `cycle-001-mps`: four correction seeds, 25 MPS steps, and four
held-out seeds with a 0.75 pure-success threshold.

# Slice Brief 005 - Meaningful MPS Training Ladder

## Objective

Run the corrected PI0.5 replay recipe for 250, 500, and 1,000 MPS updates, with
reload/finalize/provenance gates and rotating development evaluation after each rung.

## Invariants

- Use the M10-M12 trusted dataset, pinned normalizer, balanced replay, strict proof
  modes, seed governance, and complete provenance surfaces.
- Record realized samples and reject any plan/audit mismatch.
- Commit rung status before and after every training/evaluation boundary.
- Development results cannot update the accepted checkpoint.
- Stop on NaN/loss failure, checkpoint reload failure, provenance drift, or hardware access.

## Rung 250 Acceptance

- Exactly 250 audited draws with the configured 50/50 base/correction balance.
- Checkpoint 000250 finalizes against the pinned normalizer and reloads on MPS.
- Candidate and accepted checkpoint run strict paired development evaluation.
- Stage metrics and terminal results are recorded without promotion.

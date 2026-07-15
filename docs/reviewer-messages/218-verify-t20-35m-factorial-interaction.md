# Reviewer Decision 218 - Verify T20.35m Factorial Interaction

**Decision:** `VERIFY_ACTIVE_NOISE_DOMINANCE_ROUTE_NEAR_ZERO_SCALE`

## Reviewed Boundary

Brief 179, implementation/report commit `2ba6d8e`, audit `83105424...`, exact
T20.35l source, writer/verifier, tests, canonical state, and the complete scoped
diff were reviewed after model-free construction.

## Adversarial Findings

- All four signed condition metrics are preserved in exact order and every
  contrast retains its algebraic sign.
- Active noise increases worst error by `0.040813` with padded zero and
  `0.083923` with padded normal; it increases all three metrics at both padded
  settings.
- The worst-error interaction is `+0.043111`, so active and padded effects are
  not additive.
- Padded noise improves worst/mean when active noise is zero but worsens them
  when active noise is normal. Spread increases in both padded-noise contexts.
- Active-zero/padded-normal is the best signed condition at `0.066398` worst
  error, still above the 0.05-rad gate.
- Fifty-two relevant tests and 24 subtests pass; exact writer verification
  agrees under Python 3.11 and 3.12. All model, checkpoint, optimizer, Gate C,
  hardware, external-compute, and Brev flags remain false.

## Disposition

Verify T20.35m. Open T20.35n under Brief 180 to inherit active scales 0/1 with
padded noise normal and evaluate only active scales 0.25/0.5 after a separate
pre-run review. Do not load a model or create an optimizer in this boundary.

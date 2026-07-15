# Reviewer Decision 201 - Verify T20.35b PI0.5 Coverage Correction

**Decision:** `ACCEPT_SOURCE_CORRECTION_ROUTE_EXPERT_ONLY_CAPACITY_CEILING`

## Reviewed Evidence

Brief 168, pinned LeRobot stack/revision/patch set, exact PI0.5 source AST,
T20.35a's immutable tensor enumeration, corrected signed audit, tests, scoped
diff, and remotely preserved implementation `b630930` were reviewed together.

## Findings

- PI0.5 defines action in/out and `time_mlp_in/out` as its four relevant
  linear pathways and intentionally defines no `state_proj`.
- Its default PEFT regex still names `state_proj` and stale
  `action_time_mlp_in/out`; it omits the real `time_mlp_in/out` names.
- T20.35a's 76-tensor enumeration remains exact. Its conclusion is narrowed:
  state absence is expected, while both real time-MLP layers are genuinely
  uncovered.
- The corrected audit is deterministic, signed, source-bound, and still routes
  to the planned no-LoRA expert-only capacity ceiling.
- No model, inference, optimizer, source mutation, checkpoint mutation,
  hardware, external compute, or Brev occurred.

## Disposition

Accept T20.35b and supersede only T20.35a's generic five-pathway semantics.
Open T20.35c for exactly one expert-only no-LoRA frozen-batch capacity-ceiling
run. Freeze the PaliGemma vision/language base and train the complete action
expert plus action/time projections. Require a new signed spec, exact trainable
name/count audit, central training-only decision, tests, pre-run review,
commit, push, and remote confirmation before model load or optimizer creation.

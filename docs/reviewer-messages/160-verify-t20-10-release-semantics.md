# Reviewer Decision 160 - Verify T20.10 Release Semantics

`CONTINUE`

Reviewed implementation boundary `5088c6d0641d17a9369edd9b65cf09c691b6ce88`
and corrected oracle identity
`dad3133a55507e028642c89ba6cd9378e9fd79ba76d70a56819fcf3e46ae1f6c`.

The evaluator now exposes two explicit release modes. Historical T20.7/T20.9
evidence retains the original geometry-pair mode and T20.9 still recomposes
byte-identically. The new mode treats release as clear only when the final
release-settle frame has neither a positive-force pad aggregate nor a non-pad
robot/object contact. Final retreat remains stricter: all geometric contact
pairs must be absent.

The immutable seed-2 source oracle preserves zero action/state/object/contact
divergence, five 256 px keyframes, zero projection, zero assistance, and a
36.3853 mm lift. Under the corrected basis, release active-contact clearance is
1/1 and retreat geometry clearance is 1/1; every strict gate passes. The
artifact explicitly records that release-settle geometry is not clear, so the
result does not hide the residual overlap. It also records no model load,
inference, optimizer work, policy acceptance, or historical reinterpretation.

The deterministic product check and 79 relevant generation, rollout,
semantics, authority, acceptance, strict-grasp, and pointer tests pass.
Re-signed mode confusion, nested-rollout drift, and authority escalation are
rejected. Verify T20.10 and continue to per-phase learned-action error
localization against this exact source oracle. Do not accept a learned policy
or grant hardware, physical transfer, promotion, external-compute, or Brev
authority.

# Reviewer Decision 087 - Close Unused Static-Pose Gate

**Date:** 2026-07-12

## Decision

`NUDGE; CLOSE GATE UNUSED; REQUIRE ONE UNAMBIGUOUS HARDWARE-SUPERVISED PARENT`

Evidence anchor `100`: the formal runtime-profile verifier rejected before
discovery because the same rollout contained concurrent active turn contexts
with contradictory `on-request` and `never` approval policies. Selecting the
favorable record or relaxing the one-active-context requirement would defeat
the signed hardware gate.

The live gate is closed with session count zero. No discovery, holder census,
lease, candidate contract, private outcome artifact, device open, model,
policy, replay, actuation, training, or paid compute occurred. A retry requires
the conflicting turn to end, one unambiguous
`danger-full-access`/`on-request` parent, fresh formal profile evidence, and a
new separately reviewed remotely preserved finite gate.

Same-agent adversarial review rejected both tempting shortcuts: accepting a
repeated session-metadata record set without active-turn disambiguation and
selecting the earlier favorable context despite the later contradiction.
Thirty-four focused tests pass in each pinned runtime, the strict canonical
state audit passes, and the 374-test broad regression is green.

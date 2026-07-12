# Slice Brief 061 - Static-Pose Preflight Runtime Ambiguity

**Date:** 2026-07-12

## Objective

Fail closed on the first real static-pose preflight because the active rollout
contains concurrent turn contexts with contradictory approval policies. Close
the unused gate without enumerating or opening hardware.

## Contract

- Preserve the preflight failure exactly: formal profile capture rejected
  before discovery because the rollout no longer resolved one unambiguous
  active session/turn context.
- Do not weaken the profile verifier, ignore the later `never` context, or
  choose the earlier favorable `on-request` context.
- Record sessions-started zero, close the live gate, and retain the training
  lock closed.
- Do not write a private session success/failure artifact because the candidate
  session never crossed its started boundary.
- Before a retry, end the conflicting turn, establish one unambiguous
  `danger-full-access`/`on-request` parent, and use a new separately reviewed
  finite gate.

## Evidence and authority

No hardware metadata discovery, holder enumeration, device open, model,
policy, replay, actuation, training, or paid compute occurred. This slice grants
no experimental proof label.

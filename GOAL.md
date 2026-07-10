# GOAL

## Active Mission

Close the SceneSmith PI0.5 simulation learning flywheel. A bounded cycle must run
the current policy on randomized workcells, capture privileged corrective actions
from policy-visited states, export a verified DAgger dataset, launch an explicitly
configured fine-tune, evaluate fixed held-out seeds without high-level controller
assistance, and promote a candidate only when it clears the acceptance gate. Git
commits and small machine-readable manifests are the source of truth between
feature, data, training, and promotion boundaries. The physical SO-101 follower
must never be instantiated or commanded by this path.

## Current Milestone

M6 - Git-guarded learning-cycle contract

## Current Slice

Implement `docs/briefs/002-pi05-autolearn-loop.md`: DAgger correction export,
cycle orchestration, held-out promotion gates, and Git-backed evidence ledgers.

## Stop Conditions

- Stop before any code path opens or writes to the physical follower port.
- Stop before destructive dataset replacement unless an explicit overwrite flag is present.
- Do not mark the goal complete from scripted cube teleportation, final-frame image reuse, or browser animation alone.
- Never train on policy-proposed actions when an expert/controller action was
  executed unless the label source is explicit.
- Never promote from training seeds, a partial evaluation set, assisted task
  completion, or a dirty/uncommitted learning-loop implementation.
- Stop/delete paid Brev resources after a bounded training stage finishes or
  fails; record the cleanup result in the cycle manifest.
- Escalate only after three evidence-backed attempts at a true tool, dependency, or hardware blocker.

## Human Constraints

- Physical-leader reads are allowed; physical-follower commands are outside this goal.
- Browser takeover must require an armed, fresh deadman signal and release immediately when stale.
- Keep neural-policy, scripted-controller, simulated-leader, and physical-leader proof states distinct.

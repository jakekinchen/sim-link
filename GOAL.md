# GOAL

## Active Mission

Build the SceneSmith-native SO-101 domain-randomized evaluation and human-intervention loop. SceneSmith must generate the workcell, run inspectable MuJoCo episodes, arbitrate policy and leader-arm actions at each control step, record synchronized observations and correction labels, export a loadable LeRobot dataset, and expose the workflow in the existing browser action server. The physical SO-101 follower must never be instantiated or commanded by this path.

## Current Milestone

M5 - End-to-end acceptance complete

## Current Slice

Goal loop stopped after `docs/reviewer-messages/003-completion-audit.md` accepted the requirement-by-requirement audit in `docs/so101-intervention-completion-audit.md`. Physical data collection and policy fine-tuning are routed to the next product cycle.

## Stop Conditions

- Stop before any code path opens or writes to the physical follower port.
- Stop before destructive dataset replacement unless an explicit overwrite flag is present.
- Do not mark the goal complete from scripted cube teleportation, final-frame image reuse, or browser animation alone.
- Escalate only after three evidence-backed attempts at a true tool, dependency, or hardware blocker.

## Human Constraints

- Physical-leader reads are allowed; physical-follower commands are outside this goal.
- Browser takeover must require an armed, fresh deadman signal and release immediately when stale.
- Keep neural-policy, scripted-controller, simulated-leader, and physical-leader proof states distinct.

# T20 Simulation Capability-Ladder Goal Loop

## Mission

Advance the learned SO-101 policy from the lowest unmet capability gate to the
SceneSmith MVP exit through the smallest evidence-routed, simulation-only
slices. Preserve strict distinctions among memorization, open-loop inference,
closed-loop policy behavior, controller-assisted success, and physical proof.

## Source Of Truth

Resolve conflicts in this order:

1. The latest explicit owner instruction.
2. `AGENTS.md`.
3. `docs/autonomous-workflow/project_state.json` for dynamic task, authority,
   window, and proof state.
4. `GOAL.md`.
5. The active numbered slice brief.
6. `docs/sim-link-mvp-execution-plan.md`.
7. `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`.
8. The latest session log, reviewer decision, implementation, tests, and
   signed runtime artifacts.

Narrative claims never override a closed or absent machine-readable grant.

## Active Boundary

T20.35 is the current task under Brief 166. It permits exactly one rank-16
LoRA discriminator using the frozen T20.33 batch, base, processors, learning
rate, 500-update budget, training seed, five inference seeds, and unchanged
Gate B thresholds. Only rank and alpha may change from 4 to 16. A fresh signed
training specification, owner-scope grant, central-composer decision, tests,
same-agent adversarial review, scoped commit, push, and remote confirmation
must agree before model load or optimizer creation.

The run remains simulation-only. Hardware, cameras, serial devices, physical
motion, external compute, Brev, promotion, and physical-transfer authority are
closed.

## Execution Rhythm

Repeat while the run window and authority permit:

1. Verify branch, HEAD, upstream, dirty paths, active window, current task,
   training lock, and task-specific central authority.
2. Select only the next dependency-ready slice identified by the latest signed
   evidence and record it `in_progress` with the smallest precise brief.
3. Add deterministic failure tests first where practical, implement one
   coherent slice, and run focused plus relevant broad regression gates.
4. Perform a fresh same-agent adversarial review for authority escalation,
   stale identities, non-finite values, evidence spoofing, ambiguous routing,
   unsafe retries, nondeterminism, and documentation drift.
5. Update canonical state, ledger, plan, session log, and reviewer decision;
   stage explicit paths, commit, push only to
   `origin/codex/pi05-autolearn-loop`, and confirm the remote commit.
6. Execute a model or optimizer only after its exact pre-run boundary is
   remotely preserved. Adjudicate once, sign the result, and route the next
   gate without silently changing factors.

## Evidence Routing

- If T20.35 passes both unchanged Gate B thresholds, route to the separately
  reviewed bounded campaign; do not infer closed-loop success.
- If T20.35 fails, follow T20.35.x one reviewed discriminator at a time. Run
  optimizer-free module-coverage and attainable-loss-floor audits where they
  can eliminate hypotheses without spending another training rung.
- Gate C opens only after Gate B is mechanically proven. A first learned
  closed-loop grasp must be labeled autonomous only when every action is policy
  owned and the strict-v2 evaluator passes.
- A negative result is a verified result when its contract, evidence, review,
  state, commit, and remote preservation agree.

## Evidence Standard

Every verified slice records its exact inputs and content identities, allowed
and withheld authorities, deterministic test output, proof-mode label, result,
limitations, reviewer decision, implementation commit, and remote branch
receipt. Generated videos, datasets, and checkpoints may remain external to
Git only when content-addressed and referenced by the signed result.

## Stop Conditions

Stop opening major slices at the recorded cutoff and complete closeout by the
hard deadline. Stop immediately before any action requiring new owner
authority, hardware access, external spend, destructive mutation, or a permit
not mechanically granted by the central composer. Record a genuine blocker
only after safe in-scope alternatives and the required repeated blocked audit
are exhausted.

## Completion Condition

The loop is complete only when the MVP plan's learned strict-policy exit and
all remaining required integration and separately authorized physical-canary
gates are genuinely verified. Pipeline reachability, lower loss, an open-loop
match, or a controller-assisted grasp is not MVP completion.

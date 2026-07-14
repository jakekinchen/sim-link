# Slice Brief 149 - T20.18 Policy-Visited State-Fork Recovery Data

**Date:** 2026-07-14

## Objective

Extend the verified T18.4 immutable branch contract into a bounded MuJoCo
state-fork data generator rooted in the failed T20.17 seed-6 policy rollout,
then preserve labelled failure, near-failure, and recovery evidence without
running another optimizer campaign.

## Contract

- Bind the exact T20.17 result gate, run summary, final adapter, held-out seed-6
  source episode, and existing T18.4 manifest before any inference or rollout.
- Replay the exact frozen T20.17 candidate once with the same base, adapter,
  processor, seed, action horizon, and unassisted policy adapter. Its action
  digest, gate result, projections, assistance count, contact outcome, and lift
  must reproduce the verified T20.17 evaluation before any captured state is
  eligible.
- Capture every pre-action policy-visited MuJoCo integration state with the
  matching frame, phase, requested action, applied action, observation-state,
  object pose, and parent identity. Preserve the original T20.17 evidence
  unchanged; write only new T20.18 artifacts.
- Select a small deterministic set of approach, grasp, hold, and release
  parent states. Fork only from their exact serialized simulator states. Bind
  each child to its parent, perturbation specification, `generation_reason`,
  controller owner, action source, and observed strict-v2 result.
- Use only measured source or geometry-derived corrective actions already
  available in this checkout. Do not pad, interpolate, infer missing actions,
  relabel policy actions as expert actions, or treat an intended recovery as a
  successful recovery unless the observed child trace proves it.
- Replaying any parent or child from its bound state and action sequence must
  deterministically reproduce its state/action/contact/outcome digests within
  explicit finite tolerances. Missing state components, non-finite values,
  source drift, aliasing, duplicate branches, or nondeterminism fail closed.
- Keep policy-visited failure, perturbed near-failure, corrected recovery, and
  unsuccessful correction evidence distinct. The output grants only a
  simulation recovery-dataset capability; it cannot grant policy acceptance,
  training readiness, physical transfer, promotion, hardware, external
  compute, or Brev authority.

## Acceptance Criteria

- Tests first cover exact-state round trips, parent/source binding, deterministic
  selection, action provenance, no padding or inference, perturbation bounds,
  duplicate/path rejection, non-finite rejection, replay drift, label honesty,
  and authority escalation.
- The exact T20.17 candidate replay reproduces the verified action and result
  identities before its visited-state capture is accepted.
- The generated manifest contains source-bound parent snapshots across all four
  named phases and observed child outcomes with immutable IDs, explicit
  `generation_reason`, and no inferred or padded action.
- A second replay reproduces every retained parent/child digest within the
  reviewed tolerance; the generator refuses overwrite and preserves the
  original T18.4 and T20.17 artifacts byte-for-byte.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commit, and
  remote branch agree before T20.18 is described as verified.

## Out Of Scope

Optimizer training; dataset mixture or training-readiness composition; policy
acceptance; broad domain randomization; posterior inference; T20.19-T20.22;
hardware or camera access; physical transfer; promotion; Hub publishing;
external compute; or Brev.

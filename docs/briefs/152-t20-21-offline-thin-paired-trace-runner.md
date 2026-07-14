# Slice Brief 152 - T20.21 Offline Thin Paired Trace Runner

**Date:** 2026-07-14

## Objective

Define and falsify a thin offline runner that compares two separately signed
joint/action/event traces from one exact declared `q0`, while preserving action
provenance and routing mismatches without changing the twin.

## Contract

- Bind the verified T20.20 observer-role evaluator fixture and require exactly
  one `simulator_privileged` trace and one `hardware_observable` trace.
- Each trace must be independently signed and declare its evidence source,
  clock source, six-joint `q0`, strictly increasing integer nanosecond
  timestamps, joint positions, and separate proposed, issued/safety-modified,
  and measured/applied actions. Never relabel one action variant as another.
- Require exact `q0` and proposed-command-sequence identity before comparing
  joint tracking, issued actions, measured actions, and grasp/contact event
  presence and elapsed time. Preserve clock-source identity; do not infer clock
  synchronization.
- Route mismatches into fixed categories without editing a trace, selecting a
  calibration update, changing the twin, or claiming a cause outside the
  evidence. Pixel equality is neither required nor accepted as trace evidence.
- The checked fixture may use only independently signed synthetic offline
  traces to falsify the runner. A `hardware_observable` schema instance is not
  a hardware observation, paired real/sim result, or physical qualification.
- Do not access hardware or cameras, instantiate a live robot object, run an
  optimizer, mutate calibration or twin parameters, start external compute or
  Brev, or grant policy acceptance, physical transfer, or promotion.

## Acceptance Criteria

- Tests first cover exact matched comparison; `q0`, proposed, issued, measured,
  joint, event-presence, event-time, length, and clock-source mismatch routing;
  missing variants; role order; trace mutation; non-finite/wrong-width values;
  non-monotonic timestamps; duplicate events; undeclared/pixel/privileged
  fields; deterministic signing; and authority escalation.
- The runner binds two immutable trace identities, compares no images, reports
  joint/action statistics and event elapsed-time deltas, and leaves all inputs
  and twin/calibration identities unchanged.
- A signed fixture records a fully matched pair plus one fixed diagnostic case
  per mismatch category without relabelling synthetic evidence as physical.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commit, and
  remote branch agree before T20.21 is described as verified.

## Out Of Scope

Live robot execution; camera or pixel comparison; clock synchronization or the
T20.22 timing certificate; calibration optimization; twin mutation; full
shadow simulation; physical success or qualification; optimizer training;
physical transfer; promotion; external compute; or Brev.

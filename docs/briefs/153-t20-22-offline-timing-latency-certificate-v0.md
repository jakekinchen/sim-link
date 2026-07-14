# Slice Brief 153 - T20.22 Offline Timing And Latency Certificate V0

**Date:** 2026-07-14

## Objective

Define and falsify a signed offline timing certificate that derives frame age
and skew, observation assembly, action transport and hold, control period and
jitter, inference latency where present, observation drops, and deadline misses
without relabelling a timing confound as dynamics error.

## Contract

- Bind the verified T20.21 paired-trace fixture and preserve explicit clock
  source identity for sensor, observation assembly, inference, action transport,
  and control-loop streams.
- Accept only signed synthetic/offline timing samples in the checked fixture.
  Require integer nanosecond timestamps, strict cycle ordering, valid within-
  cycle causal ordering, paired inference timestamps or explicit absence, and
  finite declared thresholds.
- Derive all metrics mechanically. Do not trust caller-supplied aggregate
  latency, drop, deadline, jitter, or mismatch labels.
- Fail closed on missing clocks, cross-domain comparisons without declared
  shared clock identity, future sensor frames, negative latency/hold, duplicate
  cycles, malformed timestamps, source drift, or signed mutation.
- Route timing mismatches through fixed categories. Any detected timing
  mismatch must set `dynamics_error_attribution_blocked_by_timing=true`; a clean
  timing certificate may remove that timing blocker but never prove dynamics
  error, calibration need, or twin fidelity.
- Do not run a live timing probe, access hardware or cameras, instantiate a
  robot, run an optimizer, change calibration/twin parameters, start external
  compute or Brev, or grant physical qualification, transfer, or promotion.

## Acceptance Criteria

- Tests first cover a passing certificate and fixed diagnostics for clock
  domain, frame age, frame skew, observation assembly, action transport, action
  hold, control period, control jitter, inference latency, observation drop,
  and deadline miss; every diagnostic blocks dynamics attribution.
- Tests also reject missing/unknown fields, non-finite or non-integer time,
  wrong clock keys, non-monotonic/duplicate cycles, future frames, invalid
  within-cycle order, half-present inference timestamps, signed mutation,
  caller-supplied aggregates, contract drift, and authority escalation.
- The signed fixture binds the T20.21 contract/trace/result identities, derives
  every metric without pixels, and changes no trace, calibration, or twin.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commit, and
  remote branch agree before T20.22 is described as verified.

## Out Of Scope

Live probes; clock synchronization; camera access; dynamics/contact
calibration; twin mutation; task-family fidelity; posterior inference; full
shadow simulation; physical success or qualification; optimizer training;
physical transfer; promotion; external compute; or Brev.

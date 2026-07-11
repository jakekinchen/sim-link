# Session 049 - Mechanically Computed Twin Qualification

**Date:** 2026-07-11

## Scope

Execute Brief 037 as T16.2b. No hardware, camera, optimizer, paid compute,
physical evidence, or global-authority expansion was used.

## Implementation

- Added a signed v2 specification with code-pinned metric rules for exact units,
  aggregation, tolerance, uncertainty, sample/trajectory minima, evidence mode,
  provenance, conditions, proof states, and freshness.
- Added signed metric-evidence and qualification-input contracts with canonical
  paths/order, exact profile/spec linkage, content identity and file hashes,
  timestamps, samples, held-out trajectory IDs, conditions, and confidence-
  bearing uncertainty.
- Added a deterministic generator for aggregate, conservative decision value,
  tolerance result, qualifying status, reason codes, proof-state summary, and
  scoped capability facts.
- Added a distinct verifier that independently recomputes every result rather
  than trusting serialized status.
- Closed executed status in the legacy v1 scaffold; it now accepts only its
  deterministic all-`not_run` example.
- Added a product CLI and fixture pair whose numeric tolerances pass while both
  qualification statuses and all central-composer decisions remain withheld.

## Evidence

- Implementation commit: `710960b756553a40fd5fc9c67d7bd598281722be`.
- Focused computed-qualification suite: 16 tests passed.
- Broad feeding/consuming gate: 147 tests passed in 70.883 seconds.
- Ephemeral threshold conformance computed a scoped pass at `0.05`, fail at
  `0.051`, and no global grant in either case.
- Spec/input/report identities: `eff5a15e...`, `5c942916...`, `7ed02c6e...`.
- Fixture denial composition: `41a4d731...`; authority granted list empty.
- Computed/legacy twin, authority, production/blocked inertial, dependency,
  structural-twin, and LeRobot product paths all exited zero.
- `py_compile` and `git diff --check` passed.

## Same-agent adversarial review

The complete diff was freshly reviewed for caller-declared status, tolerance
drift, non-finite or negative values, sample-count and held-out-ID mismatch,
wrong units, condition violations, missing confidence, stale or extended
validity, profile/spec drift, evidence substitution/reuse, fixture relabeling,
issuer/subject/scope mismatch, path aliases, ordering nondeterminism, profile
pre-authorization, report tampering, and global authority escalation.
Review-time hardening pinned rules and paths, intersected freshness with source
evidence, classified fixture paths, and gated physical proof state on the exact
profile. Final focused, broad, product, compile, and diff gates were rerun.

Reviewer decision 046 accepted the implementation locally before push. The
remote closeout below then satisfied the final T16.2b verification condition.

## Remote closeout

- Pushed only to `origin/codex/pi05-autolearn-loop`.
- Fresh fetch, remote-tracking ref, and `git ls-remote` all resolved to
  `383557b0bdb1dc17725b4eac0db37d19c902b1c0`.
- Ancestry checks confirmed implementation
  `710960b756553a40fd5fc9c67d7bd598281722be` and reviewer decision 046 on the
  named remote.
- T16.2b is verified on declared fixture evidence only. No current simulation or
  physical prerequisite is satisfied, every global decision remains withheld,
  and T16.5a is next as an offline-only gate.

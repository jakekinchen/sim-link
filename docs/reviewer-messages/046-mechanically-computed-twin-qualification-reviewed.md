# Reviewer Decision 046 - Mechanically Computed Twin Qualification Reviewed

**Date:** 2026-07-11

## Decision

`CLOSE T16.2b AFTER REMOTE PRESERVATION; CONTINUE T16.5a OFFLINE`

## Review target

Implementation commit `710960b756553a40fd5fc9c67d7bd598281722be`
under Brief 037.

## Findings

- A code-pinned v2 specification declares exact units, maximum aggregation,
  conservative absolute uncertainty, sample and trajectory minima, evidence
  modes, provenance classes, environmental bounds, proof-state requirements,
  and a 24-hour freshness ceiling.
- Signed metric evidence contains finite timestamped samples, exact held-out
  trajectory IDs, conditions, confidence-bearing uncertainty, issuer and scope,
  and is bound into the qualification input by artifact identity and file hash.
- The generator derives aggregate, conservative decision value, tolerance
  outcome, qualifying status, reason codes, summary, and scoped capabilities.
  No caller supplies `pass`, `fail`, or a qualification state.
- A separate verifier revalidates every reference and independently recomputes
  every metric, summary bucket, and capability before accepting a report.
- Input freshness cannot outlive or predate its evidence; profile and spec paths
  are code-pinned; metric and evidence order is canonical; reuse and path aliases
  fail closed.
- The v1 scaffold now rejects all executed/caller-declared statuses and remains
  valid only for its deterministic all-`not_run` example.
- Fixture observations numerically meet both tolerances but receive
  `qualification_status=withheld` because their evidence mode and provenance
  are non-authorizing. The simulation-only profile cannot request or
  pre-authorize physical qualification.
- Scoped prerequisite claims are sent through the central composer. The
  checked-in fixture claims are false and all global decisions remain withheld.

## Evidence

- 16 focused computed-qualification tests passed.
- 147 feeding/consuming tests passed in 70.883 seconds.
- The ephemeral boundary conformance test computed pass at conservative value
  `0.05` and fail at `0.051`; even the passing scoped metric granted no global
  decision.
- Spec identity:
  `eff5a15eb0ae211c6f09f7b87dec1018d1162652ab6d654dba388d0df5983f60`.
- Fixture input identity:
  `5c94291694571fdf82c9a3f1e1ad2079b4ed22a217fdd6be717ac157f1231f97`.
- Fixture report identity:
  `7ed02c6e30cfef6d5743661d7c09546a0e49a7e41da0612d9ddb361b50d2affa`.
- Fixture denial composition identity:
  `41a4d731899cf7f3c9536e8197ec145345f099d2a2311e790caf6e8e491cc47e`.
- Computed-qualification, legacy twin, default authority, production inertial,
  blocked current-arm, dependency-lock, structural-twin, and LeRobot product
  verifiers all exited zero. `py_compile` and `git diff --check` passed.

## Review-time corrections

Review pinned the exact metric rules and default profile/spec paths, added
fixture-path classification beyond issuer/mode checks, bounded input validity to
the source evidence intersection, rejected impossible negative samples, enforced
canonical report order, and prevented the current simulation profile from
requesting a physical-qualified report. All final gates were rerun afterward.

## Authority

After remote preservation, this closes T16.2b and establishes only
`twin_qualification_computation_valid` on declared fixture evidence. It does not
establish a simulation metric pass from real simulation evidence, current-arm
physical qualification, simulation-training readiness, physical transfer,
deployment, promotion, or optimizer authority. Hardware was not accessed and
`training_lock` remains closed.

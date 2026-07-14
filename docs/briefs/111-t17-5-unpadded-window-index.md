# Slice Brief 111 - T17.5 Unpadded Action Window Index

**Date:** 2026-07-13

## Objective

Compile deterministic, source-bound, unpadded action-window rows from the
eligible hard-boundary segments produced by T17.4, at horizons 5, 10, 15, and
50. The current source has no eligible segments, so it must produce a valid,
explicitly empty index rather than padding or inventing windows.

## Contract

- Bind every index and manifest row to the T17.4 compiler-manifest hash, the
  source experience-record identity, the source normalization-bundle identity,
  and the source segment/frame identities.
- A window contains exactly `horizon` contiguous eligible frame rows from one
  T17.4 segment. Its frame indices and timestamps must be strictly increasing;
  no padding, inferred action, reset, teleport, timestamp gap, hard-boundary,
  prompt/controller/coordinate drift, or cross-segment transition is allowed.
- Compile horizons 5, 10, 15, and 50 independently. Segments shorter than a
  horizon yield no row for that horizon and are reported as such, not padded.
- The output is an immutable, deterministic `window_index.parquet` plus a
  canonical manifest and verifier. It is a compiler artifact only; it may not
  claim training eligibility, simulation-training readiness, optimizer work,
  physical actuation, raw-byte rewriting, or source-data mutation.

## Acceptance Criteria

- Repeated compilation of the verified T17.4 fixture is byte-identical and
  yields zero rows at every horizon.
- Synthetic complete rows used only in unit tests prove exact row counts,
  deterministic identities, source binding, and exclusion of short segments.
- Adversarial tests reject duplicate or unknown frames, noncontiguous indices,
  timestamp regressions/gaps, ineligible frames, action-incomplete rows,
  source-identity drift, and cross-segment input.
- Writer `--verify`, focused tests, relevant compiler/contract regression,
  project-state pointer check, and same-agent adversarial review agree before
  T17.5 can be marked verified.

## Expected Files

- `scenesmith/robot_lab/experience_window_index.py`
- `scripts/robot_lab/write_experience_window_index.py`
- `tests/unit/test_experience_window_index.py`
- `configurations/robot_lab/t17_5_window_index/`
- workflow state, ledger, session, and reviewer evidence

## Out Of Scope

No raw-rollout generation, dataset mixture, normalization rewrite, training,
optimizer, Brev, external compute, hardware, or physical motion. T17.5b may
be evaluated only after this boundary closes; it is not adopted by this brief.

## Stop Conditions

Stop and retain an empty index if eligible source segments do not exist. Stop
on any source-manifest/hash/schema drift or any input that would require
padding, inference, or a boundary crossing.

## Verified Outcome

- Implementation is committed as a deterministic source-bound window compiler
  and writer. The tracked output binds T17.4 compiler-manifest hash
  `4e4df563c4a82a2b195e12704a9a9c1760b76f511477891d79c879028a4ebf4c`.
- The current empty source produces zero windows at every required horizon;
  `window_index.parquet` hash is
  `d03744b08fa52bc741ed52a57e0a09684aef604f4d945f0dc3a184b10560b091` and
  `window_manifest.json` hash is
  `72be8a73257a7956491170f243befe7558095f76eecf1541f6941839fefb015b`.
- Tests cover deterministic empty output, all horizon counts on a complete
  synthetic segment, boundary splitting, noncontiguous/empty actions,
  upstream hash drift, forged segment identity, and forged authority flags.
  The focused suite has 6 tests; the relevant broad compiler/contract gate has
  74 tests. Both writers, pointer check, lock check, and diff check pass.
- Reviewer Decision 139 accepts this as a compiler-valid but data-empty
  boundary. It grants no `valid_action_windows`, training, optimizer, or
  physical authority.

# Slice Brief 020 - Semantic Unnamed Geom Identity

**Date:** 2026-07-10

## Objective

Close T16.3 by replacing sibling-index fallback identities for unnamed
collision geoms with an order-invariant, semantically honest identity strategy.
Do not reopen accepted quaternion, inertial/contact, or solver behavior.

## Acceptance Criteria

- Named geoms continue to use their declared names.
- Unnamed geoms use a documented canonical identity or multiset grouping based
  on normalized structural attributes, not raw sibling position.
- Reordering unnamed collision siblings, or inserting an unrelated visual geom,
  leaves the extracted semantic identities and generated diff unchanged.
- Exact duplicate unnamed geoms are represented deterministically without
  losing multiplicity.
- A runtime mesh and Menagerie primitive are not paired solely by ordinal
  position. If no defensible semantic correspondence exists, they become
  explicit missing/extra evidence with reconciliation decisions.
- The same identifier helper is used by collision and effective
  friction/contact extraction so categories cannot drift apart.
- The artifact records the identifier strategy/version and remains
  content-addressed and source-bound.

## Tests And Verification

- Parse two equivalent XML fixtures with reordered unnamed geoms and assert
  identical extracted records and diff output.
- Insert a visual-only sibling and assert collision identities do not change.
- Reverse two structurally different unnamed collision geoms and assert their
  identities stay attached to the correct semantic records.
- Preserve exact-duplicate multiplicity deterministically.
- Assert no production artifact key uses the old `body[index]` fallback form.
- Run focused tests, sequential CLI write/verify, and the broader robot-lab
  suite.

## Exit Condition

A fresh reviewer confirms order-invariant identity, honest non-pairing, and all
prior T16.3 truthfulness regressions. T16.3 may then close and T16.4 may start.

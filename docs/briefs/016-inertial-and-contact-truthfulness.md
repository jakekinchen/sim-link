# Slice Brief 016 - Inertial And Contact Truthfulness

**Date:** 2026-07-10

## Objective

Advance T16.3 by making the structural twin diff more truthful in two remaining
semantic areas: mass-bearing bodies whose inertia cannot be derived from the
available source inputs, and friction/contact records that are declarations
rather than effective runtime attachments. Do not start deterministic unnamed-
geom repair or T16.4 in this slice.

## Why This Slice Exists Now

- Brief 015 is now proven by commit `fb54e64`.
- The remaining T16.3 gaps are about honesty of representation, not XML
  hashing: the diff still needs to say when inertia is genuinely unknown and
  when contact/friction properties are only declared defaults or unattached
  class-level settings.
- T16.4 measured-mass intake must stay blocked until T16.3 regains reviewer
  acceptance on these semantics.

## Required Changes

- Represent any mass-bearing body whose inertia cannot be derived from the
  available runtime/Menagerie source inputs as an explicit `unknown` inertial
  record instead of silently omitting it from comparison buckets.
- Add the Menagerie camera mount as the required regression case for that
  `unknown` inertial handling.
- Compare friction/contact properties through effective attachments where the
  XML provides enough information to resolve them.
- Where the XML only provides declaration-level defaults or unattached class
  records, label them distinctly so the artifact does not imply observed runtime
  behavior.
- Preserve explicit `adopt`, `adapt`, or `retain` decisions on any true
  mismatch, missing record, extra record, or newly surfaced unknown.
- Leave deterministic unnamed-geom identifiers and measured-mass compilation
  for later briefs.

## Expected Files

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/NNN-executor-*.md`

## Tests And Verification

- Add focused tests that prove a non-derivable inertial case lands in
  `unknown`, not `matched`, `mismatched`, `missing`, or `extra`.
- Add focused tests for the required Menagerie camera-mount inertial regression.
- Add focused tests that distinguish effective contact/friction attachments from
  declaration-only defaults or unattached class records.
- Retain regressions that keep real friction/contact deltas visible where
  effective attachments do differ.
- Run:
  - `python -m unittest tests.unit.test_structural_twin_diff`
  - `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
  - `python scripts/robot_lab/write_structural_twin_diff.py`
  - `python scripts/robot_lab/write_structural_twin_diff.py --verify`
  - `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Evidence Required

- Scoped commit for this slice only.
- Updated artifact identity for the checked-in structural diff.
- Executor log that states exactly which inertial/contact truthfulness gaps were
  closed and which T16.3 gaps remain open.
- Reachability proof from `scripts/robot_lab/write_structural_twin_diff.py`.

## Out Of Scope

- Measured-part mass intake or assembly inertia/COM compilation.
- Hardware access, read authority, motion authority, or Brev usage.
- Deterministic unnamed-geom identifier repair.
- Any T17 experience-compiler work or training activity.

## Exit Condition

A fresh reviewer can confirm that non-derivable inertials are surfaced as
explicit unknowns and that contact/friction records no longer overclaim runtime
behavior when only declaration-level defaults are present, while T16.3 remains
open only for deterministic unnamed-geom limits if that work is still pending.

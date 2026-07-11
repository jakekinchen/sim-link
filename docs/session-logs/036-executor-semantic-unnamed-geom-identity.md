# Executor Session 036 - Semantic Unnamed Geom Identity

**Date:** 2026-07-10

## Slice

Implement the final brief-020 T16.3 semantic-correction slice by replacing
ordinal unnamed collision geom identities with a shared order-invariant semantic
identifier path used by both collision and friction extraction. This slice does
not reopen quaternion handling, inertial/contact truthfulness, measured-mass
compilation, hardware, or training work.

## Files Changed

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/036-executor-semantic-unnamed-geom-identity.md`

## Tests / Validation

- `python -m unittest tests.unit.test_structural_twin_diff`
- `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

Focused validation passed with 21 structural-diff tests. Broad validation
passed with 46 robot-lab tests. The suite printed the existing environment
message `Mocking bpy due to import error: No module named 'bpy'`, but no test
failed.

## Reachability

The real product path remains `scripts/robot_lab/write_structural_twin_diff.py`.
That entrypoint calls
`scenesmith.robot_lab.structural_twin_diff.write_structural_twin_diff`, which
now emits a checked-in artifact whose unnamed collision geom keys come from a
shared semantic identifier helper rather than sibling position.

The sequential `write` then `--verify` run proves the new behavior is reachable
from the tracked product entrypoint rather than from test-only helpers. The
checked-in artifact also records the identifier strategy version so reviewers
can audit the naming contract directly from repo state.

## Evidence

- Commit: pending
- Artifact: `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- Structural diff identity: `5b070b1b1f98aad3eaf00d4bd9d153ab78f53ec4046b0948ef2cf5ae93387683`
- New regression proof:
  - reordering unnamed collision siblings now leaves both extracted collision
    records and extracted friction/contact records unchanged;
  - inserting an unrelated visual-only geom sibling no longer perturbs unnamed
    collision identities;
  - reversing structurally different unnamed collision geoms keeps semantic
    pairings attached to the correct records;
  - exact duplicate unnamed collision geoms retain deterministic multiplicity
    through stable `#1`, `#2`, ... suffixes on the shared semantic stem; and
  - incompatible structures such as a runtime mesh versus a Menagerie box stay
    explicit as missing/extra evidence instead of being paired by ordinal
    position.

## Step-9 Flags For Reviewer

- T16.3 appears implementation-complete for brief 020, but the ledger remains
  `in_progress` until the reviewer confirms closeout.
- The new artifact intentionally converts prior ordinal collision/friction keys
  like `wrist[1]` into semantic unnamed-geom keys and raises explicit
  missing/extra counts where no honest runtime-vs-Menagerie correspondence
  exists.
- The worktree still contains many unrelated modified and untracked files
  outside this robot-lab slice; they were left untouched.

## Next Suggested Slice

Review brief 020 against artifact identity
`5b070b1b1f98aad3eaf00d4bd9d153ab78f53ec4046b0948ef2cf5ae93387683`. If the
reviewer accepts T16.3 closeout, start T16.4 measured-part mass intake and
assembly inertia/COM compilation.

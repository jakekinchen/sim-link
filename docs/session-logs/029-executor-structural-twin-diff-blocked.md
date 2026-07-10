# Executor Session 029 - Structural Twin Diff Blocked

**Date:** 2026-07-10

## Slice

Attempt T16.3 from brief 011 by generating a machine-readable structural diff
between the active Robot Studio SO-101 runtime model and the pinned Menagerie
`robotstudio_so101` lineage from repo state.

## Files Changed

- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/029-executor-structural-twin-diff-blocked.md`

## Tests / Validation

- `sed -n '1,220p' GOAL.md`
- `sed -n '1,260p' docs/briefs/011-structural-twin-diff.md`
- `sed -n '1,220p' configurations/robot_lab/pi05_robotics_dependency_lock.json`
- `find external -maxdepth 3 -type d | sort`
- `rg --files | rg 'robotstudio_so101|so101\\.xml|scene\\.xml|menagerie'`

No focused or broad code validation ran because the required Menagerie source
files are absent from repo state, so the slice cannot reach a truthful
implementation boundary.

## Reachability

- The intended real product path is the dependency lock at
  `configurations/robot_lab/pi05_robotics_dependency_lock.json`, because brief
  011 requires the CLI to resolve both compared models from that tracked input.
- That lock resolves the active runtime MJCF locally at
  `external/SO-ARM100/Simulation/SO101/so101_new_calib.xml`.
- The same lock records Menagerie only as a remote pin with reference-file
  hashes for `robotstudio_so101/README.md`, `robotstudio_so101/so101.xml`, and
  `robotstudio_so101/scene.xml`; there is no corresponding local tracked source
  directory in the repo for a structural parser to open.
- Because brief 011 requires generation and verification from repo state rather
  than from chat memory or remote assumptions, the structural diff path is not
  currently reachable.

## Evidence

- Blocker category: missing tracked source inputs / repo-state prerequisite.
- `configurations/robot_lab/pi05_robotics_dependency_lock.json` pins Menagerie
  revision `71f066ad0be9cd271f7ed58c030243ef157af9f4` and hashes for
  `robotstudio_so101/so101.xml` and `robotstudio_so101/scene.xml`, but not a
  local path where those files exist in this checkout.
- `find external -maxdepth 3 -type d | sort` shows only
  `external/SO-ARM100`, `external/leLab`, and `external/lerobot`.
- `rg --files | rg 'robotstudio_so101|so101\\.xml|scene\\.xml|menagerie'`
  finds `external/SO-ARM100/Simulation/SO101/scene.xml` and prior docs, but no
  local Menagerie `robotstudio_so101` source tree.
- Prior session logs 024-027 treated Menagerie as a pinned structural lineage
  reference only; no later slice vendored those XML sources into repo state.
- The worktree contains many unrelated pre-existing edits and untracked paths;
  they were left untouched.

## Step-9 Flags For Reviewer

- This is a real blocker under brief 011, not an implementation refusal: the
  required comparison input is missing from repo state.
- Generating a structural artifact from only remote hashes would violate the
  brief's reachability requirement and would not be auditable offline.
- No runtime inputs were changed and no hardware path was touched.

## Next Suggested Slice

Add the pinned Menagerie `robotstudio_so101` XML sources to repo state under a
tracked path referenced by the dependency lock, then resume T16.3 with a real
structural diff CLI and tests.

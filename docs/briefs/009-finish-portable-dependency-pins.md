# Slice Brief 009 - Finish Portable Dependency Pins

## Objective

Correct commit `92adde5` so T16.1 genuinely pins OpenPI and Menagerie and the
lock is portable across equivalent repository checkout locations.

## Required Corrections

- Resolve `Physical-Intelligence/openpi` to one exact commit and record hashes
  for its license plus the selected transform/normalization reference files.
- Resolve `google-deepmind/mujoco_menagerie` to one exact commit and record hashes
  for `robotstudio_so101` license, README, and model XML.
- Replace both `unresolved_remote_reference` states with an exact remote pin state.
- Do not include an absolute `repo_root` in the signed artifact.
- Preserve the existing active Robot Studio model and split/dirty LeRobot evidence.

## Verification

- Tests reject null/short revisions, missing license/content hashes, wrong paths,
  and modified signed fields.
- A relocation test verifies an otherwise identical fixture from two different roots.
- Live lock generation and offline verification pass.
- No runtime model switch, training, hardware access, or dependency tree commit.

## Evidence Boundary

Remote pins establish reproducible source identity. They do not claim Menagerie
is integrated, that OpenPI code is the executed runtime, or that the twin is
physically qualified.

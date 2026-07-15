# Session Log 208 - T20.35d Residual Localization Result

## Scope

Execute the sole optimizer-free T20.35d checkpoint replay and localize the
remaining one-batch decoded-action residuals.

## Evidence

- Replay attempt:
  `d3b3ff438bdfdb3d7dc1b01e7ac81024268e5479acfc953df647ba4535980306`.
- Signed report:
  `13b08e70a805a8b176b9f9a7c0e37843f7267d7918f82aeb523551e2dadf1fbe`.
- All five T20.35c decoded hashes reproduce exactly.
- Total threshold exceedances: 366. Per seed: 52 / 103 / 67 / 78 / 66.
- Per joint: shoulder pan 0, shoulder lift 29, elbow flex 0, wrist flex 52,
  wrist roll 164, gripper 121.
- Boundary exceedances: 34/366 (9.29%); interior: 90.71%.
- Wrist roll plus gripper: 285/366 (77.87%).

## Validation

- The report recomputes exactly from its retained matrices and fixed inputs.
- The replay verifier re-hashes the complete checkpoint tree and accepts the
  attempt/report identities.
- Seven focused and 76 relevant tests passed before execution.
- No optimizer, training, checkpoint mutation, Gate C work, rollout, hardware,
  external compute, Brev, transfer, promotion, or policy acceptance occurred.

The predeclared classifier's distributed label is retained, but Reviewer 205
routes T20.35e to add a model-free top-two-channel classification before any
correction choice.

# Session Log 251 - T20.36f ACT Decode Localization

## Evidence

- Result: `472e5ec5aabf36d9f280d2daf3f90b40988ccbc6d236b27cf3b3289755681ffb`.
- Objective: exact `0.07610613852739334` reproduction.
- Action: direct plus five queued hashes exactly `ecaa2e4c...`; direct/queue
  maximum physical difference `0.0` rad.
- Maximum: wrist roll timestep 0, predicted `0.413404` versus target
  `-0.0290831`, error `0.442487` rad.
- Other task-relevant maxima: shoulder lift `0.125317` at timestep 0 and
  gripper `0.241636` at timestep 49.
- Fourteen threshold exceedances: 9 in steps 0-9, 1 in 30-39, 4 in 40-49.
- Exact result verification and 41 T20.36 regressions pass.

## Result

The error is sparse normalized boundary/endpoint underfit in ACT, not a direct-
queue or physical-coordinate mismatch. Reviewer 248 closes ACT and opens Brief
198 for design-only SmolVLA Gate B entry under the unchanged gate. No optimizer,
policy selection, Gate C, hardware, external compute, or Brev is authorized.

# Session 326 - F0a Chunk Timing And Phase Observability

**Date:** 2026-07-17

**Task:** F0a / Brief 231

**Reviewer:** 321

## Outcome

F0a is a verified model-free localization at implementation commit
`f81fa9aa90ba4eaf93a125433f1f341992cca54b`. Signed result
`278e8bc772dc879622a226abe22665d320421925045ad9b3cb1f88b1c31153a4`
binds F0, exact R0 metadata/statistics, the retained R2 chunk-50 trace, the raw
source episode and PNGs, the ACT runner/model source, the coordinate map, and
the frozen 244-frame phase plan.

ACT consumes two current RGB images and six qpos state values. The raw source
has joint velocity and the dataset has timestamp, but velocity, phase,
progress, timestamp, and environment state do not survive into the policy
input. Against source-corridor adjacent-pair calibration, 20 of 24 lower
frames have a qpos-near and image-near lift counterpart with cosine-opposed
hidden velocity and a conflicting future action target. This proves a source
trajectory observability ambiguity; the retained candidate trace has qpos but
does not retain candidate camera images, so F0a makes no candidate-image
identity claim.

At the candidate's final decode start, frame 200 is nearest source lower frame
183 at normalized L2 `0.5811591805297467` and nearly equally near source lift
frame 93 at `0.5813087817685448`. Its 17-frame lower-state lag aligns within
three frames of F0's 20-frame delayed release. The next fixed-cadence
observation would be frame 250, so no observation occurs before the aligned
release onset at frame 220. That onset is one frame after the frozen release
gate at frame 219; release-final clearance fails, while retreat-final clearance
passes.

## Verification

- live reconstruction under the pinned LeRobot runtime reproduces identity
  `278e8bc7...`;
- seven focused F0a tests pass inside the previously completed 53-test relevant
  unit suite;
- 14 T20.43c continuation/replacement regressions pass;
- offline Ruff, JSON/non-finite, path ordering/traversal, symlink, authority,
  and whitespace checks pass;
- same-agent adversarial review finds no new rendering or simulation,
  checkpoint read, model construction or inference, optimizer, rollout,
  dataset/statistics mutation, network, external compute, Brev, hardware, or
  authority escalation.

The initial final-boundary verification was accidentally invoked with system
Python and stopped before source reconstruction because NumPy was absent. The
pinned LeRobot runtime then reproduced the exact result; its environment lacks
pytest, so deterministic unit tests ran through `unittest`. No dependencies
were installed and no artifact bytes changed.

## Disposition

F0a routes to a fresh F0b brief for one no-training evaluation of the retained
checkpoint under a hybrid cadence: chunk-50 through frame 175, then queue reset
and re-decode every ten actions at frames 176 through 236. Strict-v2 Gate C,
the source episode, and all thresholds remain unchanged. This closeout grants
only permission to open that brief; checkpoint/model/inference/rollout action,
corrective training, F1/Brev, hardware, transfer, promotion, and the freeze tag
remain closed.

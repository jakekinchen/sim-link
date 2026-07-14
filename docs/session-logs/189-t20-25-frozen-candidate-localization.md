# Session Log 189 - T20.25 Frozen-Candidate Localization

## Scope

Brief 156 compared the immutable T20.17 clean-base and T20.24
recovery-augmented PI0.5 adapters against exact held-out source action/state
traces on seeds 6 and 7. No optimizer, hardware, camera, external compute, or
Brev was used.

## Evidence

- Clean seed 6 trace identity:
  `388dd09a7b429e2e96f3935b8c37d3867b7ec76c82c0a1ecd6d9f966761f3e48`.
- Clean seed 7 trace identity:
  `1b7cbe4deed6f9d254fdac97900adcb4ad229cc878526912891a1afa9a33d4c4`.
- Recovery seed 6 trace identity:
  `6236d940e7a69e37922a83a824534875c187b23e9b1f59f9081f3d88f035039d`.
- Recovery seed 7 trace identity:
  `37f9406547ab545e36a2fc4a65db60680b189f192ec5024a54c5c15ac189844b`.
- Aggregate gate identity:
  `fdaa6fa9afa6ad45ab66e91f1c8c965556caff278587d6953e92b5d50d7db522`.

All four runs account for 244 finite frames, exact phase order, identical source
reset, zero projected frames, zero assisted frames, and no strict success.

## Localization

| Candidate | Frame-zero action MAE | Pre-contact action MAE | Trajectory action MAE | Trajectory qpos MAE |
| --- | ---: | ---: | ---: | ---: |
| Clean base | 0.50735 rad | 0.40137 rad | 0.43005 rad | 0.42332 rad |
| Recovery augmented | 0.61872 rad | 0.35402 rad | 0.33728 rad | 0.32844 rad |

Recovery augmentation regresses sampled frame-zero action MAE by 0.11137 rad
and improves sampled pre-contact MAE by 0.04735 rad. The candidates diverge
from one another at frame zero and their qpos diverges at frame 1. Later-frame
measurements remain prediction plus compounding state-distribution drift, not
teacher-forced loss.

## Reproducibility Finding

Recovery seeds 6 and 7 exactly reproduce their prior action hashes. Clean seed
6 does not reproduce the prior stored hash `f74bef...`; both the T20.25 runner
and an independent invocation of the original T20.17 evaluation function
produce `ed2741...`. The current and prior LeRobot stack identity is the same
`c8e903...`. The clean comparison is therefore a new frozen stochastic sample,
not an exact replay, and the observed training-relative deltas cannot yet be
treated as isolated training effects.

## Validation And Result

Seventy-seven relevant tests passed. Same-agent review covered non-finite
values, source/candidate/seed substitution, frame/phase/joint ordering,
identical reset, action semantics, projection/assistance, checkpoint and prior
hash linkage, signed mutation, authority escalation, and cleanup.

T20.25 is a verified diagnostic that selects repeated frozen-inference
variability characterization as the next safe step. It creates no optimizer,
policy-acceptance, transfer, promotion, hardware, external-compute, or Brev
authority.

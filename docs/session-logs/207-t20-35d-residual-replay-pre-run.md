# Session Log 207 - T20.35d Residual Replay Pre-Run

## Scope

Implement, bind, and review the optimizer-free exact checkpoint replay and
decoded-action residual-localization boundary without constructing a model.

## Evidence

- Implementation: `7162497b39d7e03a880b47f11ec60396928745e2`.
- Evaluation spec:
  `b083c59393a0eb9027bb07253357e8c7ec9fb1f240c58118ad8d49fa1067c033`.
- Evaluation permit:
  `bd3b093308048bafa02b26f81392a27b07ce617546706da94c9da65ed2f0e260`.
- Source result/run/checkpoint: `f6f6b024...` / `9b1af8ee...` /
  `439ae119...`.
- The permit allows one model-load/inference replay and forbids optimizer
  creation, checkpoint mutation, rollout, hardware, external compute, and
  Brev.

## Validation

- Seven focused classification, replay, permit, and attempt tests passed.
- Seventy-six relevant T20.33-T20.35d, authority, state-pointer, and
  documentation tests passed.
- The spec and permit recompute exactly from immutable source evidence.
- Python compilation and `git diff --check` passed.

This is pre-run evidence only. No T20.35d model load, inference, optimizer,
residual classification, Gate B pass, Gate C work, policy acceptance, or
physical proof has occurred.

# Slice Brief 233 - F3 Reconstruction And Current-Truth Fold

**Date:** 2026-07-17

## Objective

Turn the verified source-repository boundary into the smallest useful seed for
the new **sim2claw — Simulation to Closed-Loop Autonomous Workcell** repository.
Reconcile the reconstruction kit and living documentation to the actual
T20.43c-R2, K2, F0, F0a, and F0b evidence; preserve the exact techniques and
failure mechanisms that matter; remove stale forward claims; and verify a
fresh export before any freeze tag is created.

This slice is documentation, deterministic tooling, manifest generation, and
scratch-export verification only. It cannot load a model or checkpoint, create
an optimizer, train, run a policy rollout, access hardware, use network or
external compute, start Brev, transfer a policy, promote a result, or create a
tag before a separate terminal review is exact on origin.

## Frozen source boundary and truth order

- F0b closeout commit:
  `e630c6390397a88478e78a4f1e49c8d93fa610e3`.
- T20.43c-R2 remains immutable: marker `dfe3ff05...`, equivalence
  `fdc06297...`, run `82a06083...`, result `bf2c8b46...`, scorecard
  `6f848570...`, retention `e565e17a...`, and final receipt `be11a258...`.
- R2 truth is 10,000 updates, seven checkpoints, fourteen rollouts, Gate C
  false, no infrastructure failure, no retry. Final chunk-50 lifted
  `0.037655304225193253` m and failed only release; maximum lift was
  `0.04567430422519325` m; final receding-10 had no grasp hold and lifted
  `0.000502` m.
- F0 result `807d3da7...` falsifies tail-window starvation, an R0 gripper
  normalization defect, and late-phase loss-mass underweighting. It localizes a
  20-frame delayed release pattern and a physical-L1 gripper coefficient of
  2.6963 without selecting corrective training.
- F0a result `278e8bc7...` finds 20/24 lift/lower observation aliases and a
  17-frame state lag aligned to the release delay. It does not claim retained
  candidate-image equivalence.
- F0b result `8fb34ff4...` is a clean one-rollout terminal negative. Trace
  `af62a3b5...` is identical to chunk-50 through frame 175, diverges at the
  planned frame-176 re-observation, and improves strict retreat-contact frames
  from 1 to 17, but both pads still contact at release-final frame 219. Cadence
  alone is insufficient; the one corrective ACT rung remains unconsumed.
- K2 remains the portability proof: final manifest `d5396251...`, final-pin W1
  `7d9fa11a...`, and exact combined W2 `86739578...`. W3 is still
  `blocked_dependency` at 0/3, and W5 is CPU/fp32 ACT-to-localhost-TCP-to-
  MuJoCo transport/replay evidence only, not gRPC and not policy quality.

When prose disagrees with a signed artifact or canonical state, the artifact
and `docs/autonomous-workflow/project_state.json` win. Historical briefs and
reviews remain history; they are not silently rewritten.

## Required fold

Update the living source-repo spine where current direction is explained:

- `docs/README.md`;
- `docs/architecture.md`;
- `docs/sim-link-mvp-execution-plan.md`;
- `GOAL.md` only as the active/current pointer;
- the task ledger and machine-readable project state.

Update the portable kit surfaces:

- `reconstruction-kit/README.md`;
- `CURRENT_STATE.md` and `CURRENT_STATE.json`;
- `ARCHITECTURE.md`, `FORWARD_PLAN.md`, `QUICKSTART.md`, and
  `RESULTS_AND_LESSONS.md`;
- `templates/README.md` and any template/manifest/test surface required to keep
  the export internally consistent;
- `source-selection.json` and regenerated `SOURCE_MANIFEST.json`.

The kit must carry compact F0/F0a/F0b source, tests, decisions, and result
evidence. Preserve the full F0b replayable trace even though it is larger than
the old two-megabyte per-file selection cap; raise that cap only to the
smallest bound that admits the signed trace. Expired grants, permits, runtime
preflights, and reviewer artifacts may travel only when deliberately selected
as inert history and must never become live destination authority.

## Fork architecture that must survive compression

1. W1 proves this source repo's existing dual-runtime/all-schema path. The new
   repo then uses the pinned LeRobot venv as its sole interpreter and renders
   in-process; subprocess dispatch is deleted.
2. Default iteration is camera-free joint state plus object pose, light
   parquet, and 60-frame success-terminated reach/push tasks. Cameras and full
   audiovisual datasets belong to VLA/demo work.
3. ACT and state-based RL are primary until a demo works. SmolVLA and PI0.5 are
   stretch tracks, not prerequisites.
4. Training may be accelerator-nondeterministic. A separately owned CPU/fp32
   evaluator must return bit-identical verdicts across Macs and Linux.
5. One frozen workcell XML plus a task registry replaces per-task XML edits.
6. Each fork run auto-emits `RUN_RECEIPT.json` with commit, config hash,
   dataset identity, seed, wall clock, and metrics. Outputs are ignored from
   fork commit one and use human names.
7. The gateway is the only future path for teleop, tests, and the demo.
8. Frozen held-out sets, replayable artifacts, and separate evaluator ownership
   remain non-negotiable. Copied permits remain inert.

## Tooling and verification

- Harden the project-state pointer checker so current `F*`/`K*` task IDs do not
  fail its live parser; add deterministic regression coverage. Do not use the
  checker to erase the legitimate distinction between a closed task and a
  separately next-eligible task.
- Regenerate the source manifest from a committed source boundary, not dirty
  working-tree bytes. The final selected source commit must contain the current
  evidence and architecture fold.
- Run strict JSON/non-finite/path/symlink checks, kit manifest check and verify,
  portable-asset verification, kit and R0-regeneration tests, documentation
  link/architecture tests, and a pristine scratch export verification.
- Run the one-command offline W1 bootstrap from the final scratch export if the
  unchanged local pins remain available. Do not repeat the hour-long W2 data
  recreation merely to refresh timestamps; preserve and independently verify
  its existing exact-content receipt.
- Perform a fresh same-agent contradiction review against the signed F0b/R2
  evidence and the ten subtractive fork decisions. W3/W5 claims remain absent
  unless their existing reviewed evidence supports the exact wording.

## Freeze boundary

The owner's direct eight-hour continuation authorizes this F3 work; the final
overnight document supplies task ordering. Neither source alone permits an
early tag. After implementation, final-pin export/bootstrap proof, terminal
review, closeout commit, push, and exact origin confirmation all agree, the
terminal reviewer may authorize one annotated tag
`freeze-2026-07-17-hackathon-fork` on that exact closeout commit. The remote tag
must then be verified. The tag records an immutable source boundary only; it
does not grant training, hardware, transfer, promotion, network, external
compute, or Brev authority.

## Acceptance

F3 passes only when a new reader can answer, from the kit alone:

- what is proven;
- what the best learned policies actually did;
- why release remains unsolved;
- which architecture is current for the fork;
- how to reach runtime/data/evidence parity from a fresh repo;
- what to run next and what not to repeat; and
- why no copied evidence grants live authority.

All required tests and a scratch export must pass, the scoped diff must contain
no stale Gate C or retry claim, and the final source manifest/receipt identities
must be recorded before terminal review.

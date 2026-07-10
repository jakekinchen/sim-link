# Slice Brief 006 - Scoped Goal-Loop Guard

## Objective

Complete T16.0 by preserving the user's unrelated dirty work while allowing the
robotics goal loop to prove that its own governed paths start from a recorded,
unchanged baseline.

## Invariants

- Do not stash, discard, stage, or commit unrelated files.
- Do not use blanket `--allow-dirty` without a tracked path-baseline check.
- Freeze rungs 500/1,000; start no policy training.
- The guard must be deterministic and suitable for unattended preflight.
- The active ledger and latest brief remain the loop's task source.

## Acceptance

- A command records or checks path/status/blob fingerprints for pre-existing
  unrelated changes without reading secrets into tracked output.
- New or changed governed robotics/workflow paths fail preflight unless they are
  part of the current bounded slice.
- The goal-loop dry-run resolves the active Executor and Reviewer prompts.
- Focused tests or a shell-level self-test prove drift detection.

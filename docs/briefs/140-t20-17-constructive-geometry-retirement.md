# Slice Brief 140 - T20.17 Constructive Geometry Retirement

**Date:** 2026-07-14

## Objective

Remove the retired T19.0 Halton-search wrappers without losing the live
constructive grasp behavior that later episode generation and closed-loop
grading still use. The signed historical diagnostic JSON files remain immutable
evidence, but no current code may regenerate them.

## Contract

- Extract only the shared deterministic MuJoCo runner, midpoint solve,
  orientation selection, contact truthfulness helpers, and the two retained
  constants: post-yaw settle duration and approach-motion limit.
- Change live consumers to the named constructive module. The unilateral grasp
  must use its exact historical seed request as a fixed source fact, not a
  Halton index or candidate search.
- Delete the eight retired wrapper builders and their duplicate per-wrapper
  tests only after a repository-wide import/configuration audit shows no live
  consumer. Preserve `retired_grasp_diagnostics.py`, the signed JSON files, and
  their consolidated integrity test.
- Do not run a new search, rewrite historical artifacts, start training, load
  a policy, touch hardware, external compute, or Brev.

## Acceptance Criteria

- No live source import refers to `geometry_first_grasp_search` or any of the
  eight retired wrapper modules.
- Scripted episode generation and the closed-loop contact gates use the
  extracted constructive primitive and preserve their focused regression
  behavior.
- A static retirement test proves the wrappers are absent while the frozen
  diagnostics remain hash-pinned and non-promoting.

## Out Of Scope

Changing the retained immutable T19 JSON evidence, regenerating a search,
changing strict grasp semantics, dataset work, model/inference/optimizer work,
physical observation, hardware, external compute, or Brev.

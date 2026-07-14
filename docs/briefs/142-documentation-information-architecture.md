# Slice Brief 142 - Documentation Information Architecture

**Date:** 2026-07-14

## Objective

Make the active SceneSmith SO-101 program understandable without dismantling
its evidence trail. Add a documentation front door, a system/tech-stack
explanation, a requirements-and-contract index, and an explicit current versus
historical guide. Link the root README and workflow index to those entry points.

## Contract

- Route, do not duplicate: dynamic state stays in `project_state.json`; active
  task narrative stays in `GOAL.md` and the active ledger; historical evidence
  stays in its existing signed artifacts, briefs, session logs, and reviews.
- Explain the real boundaries among SceneSmith, MuJoCo/SO-ARM100, pinned
  LeRobot, leLab, and the thin bespoke governance shell.
- Name exact authority distinctions: simulation-only evidence, training
  authority, live read-only proof, physical transfer, and promotion.
- Mark obsolete/superseded historical plans as history without deleting or
  relabeling evidence.

## Acceptance Criteria

- A new contributor can identify the current mission, source of truth,
  roadmap, architecture, tech stack, contracts, evidence history, and decision
  records from `README.md` or `docs/README.md` in two clicks.
- The guides link to canonical files rather than repeat mutable counts, hashes,
  or authority decisions.
- A static documentation test verifies required entry points, headings, and
  cross-links; JSON pointer synchronization and link checks pass.

## Out Of Scope

Changing runtime behavior, contracts, hardware gates, training authority,
historical evidence, external compute, or Brev.

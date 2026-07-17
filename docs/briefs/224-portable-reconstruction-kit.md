# Slice Brief 224 - Portable Reconstruction Kit

**Date:** 2026-07-16
**Support task:** K1
**Status:** Verified by Reviewer 303

## Objective

Create one self-contained, extractable directory that compresses the verified
SO-101/MuJoCo/LeRobot program into the minimum useful architecture, pinned
stack, current proof state, evidence map, lessons learned, quick start, and
forward route needed to seed a new repository without replaying the full task
alphabet or importing misleading capability claims.

## Source boundary

- Canonical result-state snapshot: `6c53d9309f7f41f0d3ac351c049436ddda20e50f`.
- Portable source/documentation boundary: implementation commit
  `605e4d3624a87593a1b5da9a97cd263f6bade78a`; the generated source manifest
  must pin this commit so corrected living docs and the immutable T20.41 route
  snapshot are exported without changing the earlier signed results.
- Live-state sources: `GOAL.md`, `docs/autonomous-workflow/project_state.json`,
  and the active task ledger.
- Architecture/contract sources: `docs/architecture.md`,
  `docs/requirements-and-contracts.md`, the pinned robotics dependency lock,
  and their referenced validators.
- Result sources: verified T20.42/R0, T20.43b pre-run/unconsumed boundary,
  T20.44 terminal negative, strict-v2 evaluator evidence, and the explicit
  Robo Scan producer/consumer boundary.

## Deliverables

Create a top-level `reconstruction-kit/` containing:

1. A plain-language entrypoint and exact current-status snapshot.
2. A compressed system/data/authority architecture.
3. A two-stage quick start: evidence-only bootstrap first, local simulation
   recreation second.
4. A results and lessons dossier separating verified wins, clean negatives,
   infrastructure failures, unresolved work, and rejected directions.
5. A dependency-ordered forward plan beginning with the unconsumed ACT rung.
6. A machine-readable source manifest pinned to the closeout commit.
7. Dependency-free verification and export helpers that refuse hash drift,
   unsafe destinations, ignored bulk outputs, private data, and external
   hardware/model actions.
8. Focused tests for manifest integrity, safe export, and path traversal.

## Acceptance criteria

- A reader can understand the project and its honest current capability in
  under fifteen minutes without reading numbered history.
- The manifest names every copied source, role, required/optional tier, exact
  SHA-256, and license/provenance caveat where applicable.
- The export helper copies only the curated tracked source set plus the kit,
  writes a receipt, and never copies `outputs/`, checkpoints, datasets, caches,
  credentials, hardware observations, or the untracked external checkouts.
- The verifier passes against the closeout source tree and fails on missing,
  changed, aliased, duplicate, absolute, or parent-traversing paths.
- The quick start makes clear that external repositories/checkpoints must be
  acquired separately at exact pins and that no runtime permission, training
  decision, or physical authority transfers to a new repository.
- Focused tests, strict JSON, shell/Python syntax, link/path checks, whitespace,
  and a fresh same-agent adversarial review pass.

## Authority granted

Read tracked repository evidence; create documentation, a manifest, and
dependency-free local file-copy/verification helpers; run model-free tests; and
preserve the reviewed slice on `origin/codex/pi05-autolearn-loop`.

## Authority withheld

No model or checkpoint download, package installation, network acquisition,
dataset/checkpoint/output copying, model construction or inference, optimizer,
simulation campaign, marker, hardware/camera/serial access, physical motion,
Robo Scan mutation, external compute, Brev, transfer/promotion claim, history
rewrite, or destructive operation. The kit documents authority; it does not
carry authority into another repository.

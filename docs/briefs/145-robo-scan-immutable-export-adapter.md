# Slice Brief 145 - Robo Scan Immutable Export Adapter

**Date:** 2026-07-14

## Objective

Implement Sim-link's independent, offline reader for one explicitly selected,
immutable `so101.scene-export-receipt.v1` directory and convert a valid receipt
only into a local, non-authorizing TwinCandidate descriptor.

## Contract

- Use no Robo Scan import, sibling checkout lookup, Git command, package path,
  camera, robot, simulator, model, training, external compute, or Brev API.
- Reject an export root in a checkout, a symlink, unsafe/extra/missing paths,
  noncanonical JSON, duplicate keys, bad hashes, unexpected schema fields,
  non-finite/non-rigid transforms, contradictory units, malformed uncertainty,
  identity/provenance/privacy drift, metric-evidence drift, or authority
  promotion.
- Bind the approved producer commit and exact source-free fixture identities in
  a Sim-link compatibility lock. Runtime input is a copied export directory,
  never the producer checkout.
- Validate identity, provenance, coordinate convention, units, transforms,
  uncertainty, and every asset before materializing the descriptor.
- A reference-only export may yield visual-context metadata only. It must be
  mechanically ineligible for simulation assets, collision, calibration,
  training, physical transfer, or promotion. A future metric candidate can be
  admitted only after the same independent checks and an updated lock.

## Acceptance Criteria

- A copied checked-in fixture is accepted through the independent validator and
  produces the deterministic candidate descriptor.
- Mutations covering checkout/symlink/path, JSON, bytes, receipt/manifest
  identity, transform, unit, uncertainty, provenance, privacy, disposition,
  metric evidence, and extra-file drift fail closed.
- A central-composer regression proves the resulting candidate descriptor
  cannot change any global decision.
- State, ledger, brief, session log, reviewer decision, scoped commit, and
  remote branch preservation agree.

## Out Of Scope

Changing Robo Scan; accepting a real metric workcell; generating MuJoCo XML or
collision assets; hardware or camera access; training; external compute; Brev;
or any global authority grant.

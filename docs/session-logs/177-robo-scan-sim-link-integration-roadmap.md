# Session Log 177 - Robo Scan And Sim-Link Integration Roadmap

## Scope

Implementation `d695ed41d4359839f799b97b0490426c70d80626` converts the
workcell-foundry proposal and the current state of both repositories into a
durable cross-repository integration plan.

The roadmap establishes:

- one product pipeline across two repositories, with no Git-history or private
  implementation merge;
- final ownership for capture/reconstruction, workcell representation,
  simulator compilation, calibration layers, tasks/episodes/policies, hardware
  runtime, and central authority;
- a seven-artifact contract stack from `SceneExportReceipt` through
  `WorkcellDeploymentBundle`;
- phases I0–I8 with exact owners, start conditions, planned consumer files,
  validation, exit gates, rollback, and compatibility rules;
- a concrete deduplication matrix that preserves independent validators and
  historical evidence while eventually removing duplicate active capture
  paths from sim-link;
- the immediate queue: Robo Scan finishes Brief 054, sim-link then implements
  an offline independent receipt validator, and real metric integration waits
  for Robo Scan M1–M4.

## Upstream Inspection

The separate Robo Scan worktree remained untouched. During planning it was on
`codex/brief024-d405-protocol-v2` with active dirty Brief 054 and its
`scene_export_receipt.py`, source-free fixture, and tests in progress. The
inspected producer implementation already enforces exact receipt fields,
canonical JSON, asset bindings, safe paths, finite transforms, non-metric
evidence denial, privacy denial, and global authority denial.

The roadmap deliberately keeps the producer Git revision outside the
self-checksummed receipt. The reviewed handoff publishes it, and sim-link's
future compatibility lock pins it with the schema and receipt identities. This
avoids a circular commit/receipt identity while preserving exact provenance.

## Validation

- Documentation information-architecture gate: 6 tests passed.
- Documentation, artifact-contract, authority-composer, and SO-101 processor
  gate: 40 tests passed.
- Strict JSON parsing, project-state pointer verification, local Markdown-link
  checks, and `git diff --check` passed.
- The existing test continues to reject direct `environment_scanner` or
  `so101_scan` imports in sim-link governance code.

## Authority

This is a planning/documentation boundary only. It edits no Robo Scan file,
accepts no export, adds no dependency or adapter, changes no simulation scene,
retires no code, opens no hardware, starts no training, and grants no twin,
transfer, promotion, physical, external-compute, or Brev authority.

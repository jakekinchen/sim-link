# Decisions And Adjuncts

Use this page to find design choices, package assessments, and external ideas
that influence the SO-101 program. These are decision records, not permission
grants or a substitute for current state.

| Topic | Decision | Canonical record |
| --- | --- | --- |
| Package versus bespoke boundaries | Keep artifact identity, strict grasp, geometry, SO-101 bridge, and authority thin; use LeRobot for ML/datasets/processors. | [Bespoke-versus-package recreation map](./autonomous-workflow/bespoke-package-recreation-map.md) |
| Legacy search experiments | Preserve signed diagnostics, retire wrapper/search code, use the constructive geometry primitive. | [Brief 140](./briefs/140-t20-17-constructive-geometry-retirement.md) and [review 170](./reviewer-messages/170-verify-t20-17-constructive-geometry-retirement.md) |
| Physical observation replacement | Keep historical evidence intact; future adapter is owner-present, read-only, content-addressed, and has no action API. | [Minimal live-adapter recreation](./autonomous-workflow/minimal-live-adapter-recreation.md) |
| External workflow patterns | Adopt or reject external scaffolds only through a durable assessment. | [External pattern assessment](./autonomous-workflow/08-external-pattern-assessment.md) |
| SO-Frame | Use its failure modes as semantic gates; do not import its runtime uncritically. | [SO-Frame adoption decision](./autonomous-workflow/so-frame-adoption-decision.md) |
| Proof interpretation | Preserve negative transfer, fixture limits, and gate progression explicitly. | [Proof-state history](./autonomous-workflow/proof-state-history.md) |

## Evaluation Rule

An external package or idea earns adoption only when it improves a bounded
requirement without weakening provenance, authority composition, deterministic
replay, or truth labels. It is not adopted merely because it demonstrates a
task visually or offers a larger implementation surface.

For a new adjunct, add a focused decision record that names: the source,
problem addressed, interfaces adopted, interfaces rejected, authority impact,
verification plan, and retirement/reversal condition. Link it here only after
the decision is reviewed.

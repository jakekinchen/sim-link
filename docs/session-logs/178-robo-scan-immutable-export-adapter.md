# Session Log 178 - Robo Scan Immutable Export Adapter

## Scope

Implementation `67daad9a1a81c3b705d9aacaaab287ca9b628a68`, hardened by
`cb4e5a02f666edcb2cf058d6deab615f181e1b13` and adversarially covered by
`d01416bbb69a1a74a682700459b2c32b79341356`, executes only Brief 145's offline
cross-repository intake boundary. It does not import the producer package,
inspect a sibling checkout at runtime, open hardware, instantiate a simulator,
generate simulation assets, run a model/training job, use external compute, or
use Brev.

## Delivered

- `robo_scan_export_receipt.py` independently reopens the approved copied
  `so101.scene-export-receipt.v1` directory with strict JSON/duplicate-key,
  path, checkout, symlink, file-set, byte/hash, manifest, transform, units,
  uncertainty, provenance, privacy, metric-evidence, and disposition checks.
- The compatibility lock pins Robo Scan commit
  `72eb02efe7e69981a5afab41a2733cd31ec03d4e`, the receipt/manifest identities,
  and all fixture-file identities. It is not a runtime path to Robo Scan.
- The CLI accepts only an explicit copied export root. A root inside a Git
  checkout is rejected.
- A passing reference-only fixture becomes a content-addressed local
  `reference_only_visual_context` descriptor. Its relative units make
  simulation-asset compilation ineligible. It exposes no central-authority
  field and contains no raw data or source path.
- The hardening commit also independently enforces the producer's canonical
  node order, required root/layer namespace, parent closure, inferred-default
  visibility, and reference-only isolation rules.

## Validation

`python3 -m unittest tests.unit.test_robo_scan_export_receipt
tests.unit.test_authority_composer tests.unit.test_twin_contract
tests.unit.test_documentation_information_architecture -v` passed 42 tests.

The adapter-specific adversarial cases reject checkout roots, symlinks, extra
or missing files, noncanonical JSON, checksum/identity drift, transforms,
units, uncertainty, provenance, privacy, disposition, and metric-evidence
injection. The central-composer regression keeps every global decision denied.

## Authority

This proves only independent receipt conformance and local candidate metadata
for the checked-in reference fixture. It does not verify upstream metric
capture/calibration, metric geometry, a MuJoCo asset compile, physical twin,
training, transfer, promotion, hardware access, external compute, or Brev.

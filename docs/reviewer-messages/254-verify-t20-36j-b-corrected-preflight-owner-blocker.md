# Reviewer Decision 254 - Verify T20.36j-B Corrected Preflight And Owner Blocker

**Decision:** `VERIFY_CORRECTED_PREFLIGHT_CONTRACT_BLOCK_LIVE_EXECUTION_PENDING_OWNER`

## Reviewed Boundary

Brief 202; SmolVLA spec `fb217f3e...`; consumed failure `3804eff6...`;
dependency audit `0804fd4f...`; offline resolution `8dec69ae...`; cache
manifest `6cc7235c...`; corrected contract `cb018b69...`; implementation
`79b5670`; 69 T20.36 tests; 12 pointer tests; exact verifier; origin parity;
and the complete scoped diff.

## Adversarial Findings

- The historical T20.36h path created its counted attempt marker before the
  model import that reached `AutoProcessor`. The corrected contract makes the
  only legal order recursive installed closure, offline AutoProcessor smoke,
  attempt marker, then full policy construction.
- Installed-closure evidence is independently reconstructed from exact
  distribution versions, metadata hashes, recursive active `Requires-Dist`
  edges, and the signed Python/platform marker environment. Missing, mismatched,
  duplicated, aliased, or internally inconsistent closure evidence fails.
- AutoProcessor evidence must bind the exact local VLM snapshot, offline flags,
  `local_files_only`, observed classes, and safe relative file reads. Network,
  snapshot drift, duplicate/unsafe paths, or any weight/tensor-file read fails.
- Corrected preflight evidence cannot grant a permit or claim replacement
  readiness. It records raw-byte checkpoint inventory separately from tensor
  deserialization and leaves marker, model, inference, and optimizer false.
- Source references are exact-path/schema/identity/file-hash bound. Contract
  drift cannot amend Gate B, authorize Gate C, or create retry/sweep authority.

## Disposition

Verify T20.36j-B. T20.36j remains blocked until the owner authorizes the exact
four-package offline installation and at most one replacement local-MPS
attempt. After installation, the live closure and AutoProcessor smoke must be
signed under contract `cb018b69...`, remotely reviewed, and composed with a
fresh central training decision and one-use permit before a marker exists.

## Withheld Authority

No package installation, environment mutation, network/download, live
AutoProcessor construction, model/checkpoint deserialization, permit, attempt
marker, replacement execution, inference, optimizer, Gate B change, Gate C,
rollout, hardware, external compute, or Brev.

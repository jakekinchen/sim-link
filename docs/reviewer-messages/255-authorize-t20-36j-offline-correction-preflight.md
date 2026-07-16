# Reviewer Decision 255 - Authorize T20.36j Offline Correction And Preflight

**Decision:** `VERIFY_IMPLEMENTATION_AUTHORIZE_EXACT_OFFLINE_CORRECTION_PREFLIGHT`

## Reviewed Boundary

Brief 203; owner instruction recorded 2026-07-16; SmolVLA spec `fb217f3e...`;
corrected contract `cb018b69...`; cache manifest `6cc7235c...`; owner grant and
central decision `aa0992e6...`; implementation
`b35acd182ca6520aa762f9adc11ab3cce1800422`; origin parity; 76 T20.36 tests;
12 pointer tests; exact contract/authority verifiers; compilation; and the
complete scoped diff.

## Adversarial Findings

- The replacement uses fresh T20.36j authority, permit, marker, run, failure,
  checkpoint, and result paths. It cannot overwrite or reuse consumed T20.36h.
- The owner grant binds exactly Accelerate 1.14.0, docopt 0.6.2, num2words
  0.5.14, and psutil 7.2.2 to offline cache manifest `6cc7235c...`; network,
  extra packages, retry, sweep, Gate B amendment, and Gate C execution remain
  false.
- Recursive installed closure is reconstructed from active `Requires-Dist`
  edges, exact versions, raw METADATA hashes, and the Python 3.12 Darwin arm64
  marker environment. Missing, mismatched, duplicate, or aliased packages fail.
- AutoProcessor construction is local-files-only with offline environment,
  socket blocking, opened-file observation, and a hard denial for weight or
  tensor suffixes. It remains before the attempt marker and is not model
  construction.
- The one-use permit binds the signed environment and processor evidence. The
  replacement runner invokes the frozen T20.36h evaluation contract, preserving
  the five deterministic seeds, objective ratio 0.10, and uniform 0.05-rad
  action threshold.
- Result verification intrinsically reconstructs evaluation order, pass/fail,
  checkpoint identity, and all withheld authority flags; a caller cannot turn a
  merely signed but contradictory run into a result.

## Disposition

Verify the remotely preserved implementation and fresh training-only central
authority. The exact four cached distributions may be installed into
`external/lerobot/.venv` with uv offline mode, then the corrected preflight may
construct AutoProcessor and produce signed closure/processor/preflight/permit
evidence. Those artifacts must be reviewed, committed, pushed, and confirmed on
origin before the single replacement attempt marker is created.

## Withheld Authority

No network/download, extra package, attempt marker before remote preflight and
permit, second attempt, retry, sweep, Gate B change, Gate C execution before a
pass, rollout, hardware, physical transfer/promotion, external compute, or Brev.

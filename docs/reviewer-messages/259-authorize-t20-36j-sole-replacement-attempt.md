# Reviewer Decision 259 - Authorize T20.36j Sole Replacement Attempt

**Decision:** `VERIFY_CORRECTED_PREFLIGHT_AUTHORIZE_ONE_COUNTED_REPLACEMENT`

## Reviewed Boundary

Brief 203; owner grant; central decision `aa0992e6...`; exact offline install;
closure `ac8abed1...`; environment manifest `3f645a25...`; processor smoke
`5223d8f0...`; corrected preflight `3c9b5af9...`; permit `effa3b65...`;
artifact commit `a19d48df29465978a96c1a2aa67afbe1a46c7b2c`; origin parity;
independent live stack/batch/checkpoint reconstruction; 16 focused tests; exact
preflight verifier; absent marker/result paths; and the scoped diff.

## Findings

- The installed closure contains 57 active packages, exact authorized versions,
  raw metadata hashes, no missing requirement, and no version mismatch.
- AutoProcessor evidence binds the exact lexical VLM snapshot, expected classes,
  six safe config/tokenizer files, offline/local-only flags, and no network or
  weight/tensor access. It is not full model construction.
- Preflight source and remote source are both `ad3d89c`; live stack, canonical
  batch, and raw checkpoint tree identities independently reproduce.
- Required order is intact: closure and processor complete; marker and full
  policy construction false. No attempt path exists.
- Permit `effa3b65...` authorizes one attempt, imports the frozen T20.36h
  evaluator, binds schedule 0/100/250/500/1000/2000, caps 2,000 updates, and
  preserves objective ratio 0.10 plus maximum physical error 0.05 rad.
- Runtime smoke is counted. Any post-marker exception consumes the permit and
  routes a signed failure with no retry.

## Disposition

Authorize exactly one local-MPS T20.36j replacement attempt after this reviewer
boundary is committed, pushed, and origin-confirmed. Stop at the first Gate B
pass or after 2,000 updates. Preserve either success/fail result or counted
runtime failure without retry.

## Withheld Authority

No second attempt, retry, sweep, Gate B change, Gate C execution before a pass,
closed-loop rollout, hardware, physical transfer/promotion, external compute,
or Brev.

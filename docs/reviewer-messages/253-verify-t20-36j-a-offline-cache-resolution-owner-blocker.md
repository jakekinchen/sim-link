# Reviewer Decision 253 - Verify T20.36j-A Offline Cache Resolution And Owner Blocker

**Decision:** `VERIFY_OFFLINE_CACHE_CLOSURE_BLOCK_INSTALL_AND_REPLACEMENT_PENDING_OWNER`

## Reviewed Boundary

Brief 201; verified T20.36i audit `0804fd4f...`; exact Python 3.12 venv;
read-only offline resolution `8dec69ae...`; cache manifest `6cc7235c...`;
implementation `7734e24`; 63 T20.36 tests; exact verifier; origin parity; and
the complete scoped diff.

## Adversarial Findings

- uv's offline dry-run resolves 28 packages for the exact existing venv. It
  reuses 24 installed distributions and proposes exactly four additions:
  Accelerate 1.14.0, docopt 0.6.2, num2words 0.5.14, and psutil 7.2.2.
- Every proposed package is already available in the local uv cache. The audit
  binds distribution metadata and deterministic content-tree identities; the
  built docopt wheel is additionally bound by artifact SHA-256.
- Network acquisition is not required. A future install must remain offline,
  exact-versioned, bound to cache manifest `6cc7235c...`, and fail closed if
  any cache content drifts.
- The verifier rejects resolver expansion, duplicate/missing cache rows,
  archive aliasing, version drift, content drift, and authority escalation.
- Audit `8dec69ae...` records no package installation, environment mutation,
  network access, AutoProcessor/model construction, checkpoint read, attempt
  marker, inference, or optimizer work. Gate B remains unevaluated.

## Disposition

Verify T20.36j-A. T20.36j remains blocked until the owner explicitly authorizes
both (1) installing only the four signed cached distributions, offline, into
`external/lerobot/.venv`, followed by a new signed environment manifest and
offline AutoProcessor smoke before any marker; and (2) at most one replacement
local-MPS attempt under unchanged Gate B. No network authority is needed or
granted.

## Withheld Authority

No package installation, environment mutation, network/download, replacement
attempt, AutoProcessor/model construction, checkpoint access, inference,
optimizer, policy selection, Gate B change, Gate C, rollout, hardware,
external compute, or Brev.

# Reviewer Decision 209 - Authorize T20.35g Runtime-Corrected Replacement

**Decision:** `AUTHORIZE_ONE_T20_35G_PYTHON_312_REPLACEMENT_ATTEMPT`

## Reviewed Boundary

Brief 173, consumed attempt `788015fa...`, runtime preflight `d476382b...`,
correction `b077d19`, replacement spec `44076248...`, replacement permit
`b3078ea0...`, runner, tests, canonical state, and complete scoped diff were
reviewed before replacement checkpoint access.

## Adversarial Findings

- Attempt 001 is immutable and consumed. It verified the checkpoint tree, then
  loaded checkpoint tensors on CPU and validated their manifest before Python
  3.14's `draccus` parser rejected the pinned PI0.5 type annotation. It produced
  no model construction, inference, optimizer, mutation, result, or Gate B claim.
- The old permit is explicitly non-reusable. Replacement spec v2 binds the old
  spec, permit, attempt, and signed failure/preflight identity rather than
  deleting, rewriting, or silently retrying them.
- A model-free Python 3.12 preflight imports the same pinned LeRobot stack,
  parses the exact cached PI0.5 config as `PI05Config`, and observes the same
  10-step default. It reads no checkpoint tensor and constructs no model.
- The replacement runner fails before authority/checkpoint access unless the
  interpreter major/minor is exactly 3.12. It writes distinct attempt 002 and
  still refuses any existing result.
- Cadences, seeds, checkpoint, target, exact 10-step hash gate, metrics,
  selection, no-optimizer boundary, and all closed authorities are unchanged.
- Five focused and 90 relevant tests pass. Original and replacement specs,
  permits, runtime preflight, and both Python 3.11/3.12 verification surfaces
  reproduce exactly.

## Disposition

Authorize exactly one replacement attempt under permit `b3078ea0...` using the
reviewed Python 3.12 runtime. Do not reuse attempt 001 or permit `ca3dbd3f...`.
Stop again before any further retry, optimizer, cadence expansion, Gate C,
hardware, external compute, or Brev action.

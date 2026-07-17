# Reviewer Decision 317 - Accept T20.43c-R2 Pre-Marker Scoped-Input Restoration

**Date:** 2026-07-16

## Decision

`ACCEPT_PRE_MARKER_SCOPED_INPUT_RESTORATION`

## Finding

The final pre-marker audit found that Brief 229 is included in
`IMPLEMENTATION_SCOPED_PATHS`, but authority commit `391811e...` and acceptance
commit `7ab706a...` had appended status prose to that file after the reviewed
required source `1bc1c773...`. The runner's remote-preservation gate would have
rejected this drift before marker creation. No marker, checkpoint tensor read,
model action, optimizer, rollout, or Gate C action had occurred.

Reviewer 316's signed acceptance remains immutable and correctly bound to
authority commit `391811e...`, permit `f063e034...`, and its own file SHA. Its
claim that all scoped inputs were already clean was incomplete; this decision
records and corrects that discrepancy before the one-use boundary.

## Correction

Restore `docs/briefs/229-t20-43c-manual-replacement.md` byte-for-byte to its
reviewed `1bc1c773...` content. Living status remains in `GOAL.md`, canonical
project state, the active ledger, Reviewer 316, and Sessions 320-321, none of
which are implementation-scoped inputs.

After restoration, every path in `IMPLEMENTATION_SCOPED_PATHS` has zero diff
from required source `1bc1c773...`. The authority artifacts, acceptance, prior
interruption, actual-schema smoke, dataset, recipe, schedule, thresholds, and
output paths are unchanged.

## Authority granted

Preserve this corrective boundary on origin. After origin is exact, re-run the
remote-preservation gate, completion-budget check, authority/acceptance
verification, and output-absence check. If all remain exact, create the sole R2
marker and execute the already accepted unchanged attempt once.

## Authority withheld

No authority rematerialization, acceptance rewrite, retry, second replacement,
recipe/schedule/data/threshold change, hardware, network, external compute,
Brev, transfer, promotion, or destructive operation.

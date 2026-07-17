# Owner Addendum - T20.43c Manual Replacement

**Recorded:** 2026-07-16

The owner directly delegated the overnight foundation run with the instruction:

> W0 finish T20.43c unhurried ... W1/W2 outrank W4/W5 if capacity forces a
> choice.

The first T20.43c continuation had already consumed its sole marker and reached
optimizer update 728 when it was stopped to honor an older final-hour direction.
Its optimizer state was not retained, so exact update-728 continuation is
impossible. The consumed marker, exact-equivalence receipt, partial run tree,
and terminal interruption remain immutable.

For W0 only, the direct instruction authorizes the smallest scientifically
equivalent manual recovery: one separately rooted replacement beginning from
the same bit-exact checkpoint-0 state, empty AdamW state, unadvanced sampler,
unchanged R0 dataset, unchanged ACT recipe, unchanged 10,000-update schedule,
and unchanged dual-semantics strict-v2 evaluation. A fresh central authority
decision, runtime preflight, reviewer decision, acceptance, permit, and marker
are required. A completion-budget check must pass before that marker.

This is a manual owner-directed replacement after an operator-direction
interruption, not reuse of the consumed permit and not an automatic retry. If
the replacement fails after its marker, W0 closes without another retry.

No hardware, camera, serial, physical motion, network, package installation,
external compute, Brev, recipe change, dataset change, threshold change,
transfer, promotion, or destructive operation is authorized by this addendum.

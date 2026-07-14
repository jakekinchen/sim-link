# Reviewer Decision 187 - Verify T20.26 Frame-Zero Inference Variability

`ACCEPT_VERIFIED_CURRENT_RUNTIME_DETERMINISM`

Reviewed Brief 157 through artifact commit `437215b` and gate identity
`b1bbe7b27855ac738cf740ec04e03339b1f7897b03576b3b2757001c63163c0b`.

Four independent local-MPS processes reconstructed the same held-out seed-6
frame-zero observation. Image-byte hashes, qpos, qvel, source identities, stack
identity, and per-candidate checkpoint identities match across all batches.
Source-state maximum error is 3.98e-8, below the 1e-6 tolerance. Each process
captured three same-seed and four distinct-seed frozen actions, then exited
before applying an action or completing a rollout.

Both adapters are bit-exact for same-seed repeats within each process and
across the two independent processes: all four maximum differences are 0.0
rad. The T20.25 clean historical-hash mismatch is therefore not reproduced in
the current pinned runtime. It remains historical-runtime-specific evidence,
not proof of current cross-process nondeterminism.

Declared distinct inference seeds materially change the sampled frame-zero
action. Maximum pairwise difference is 0.18478 rad for clean base and 0.14797
rad for recovery augmented. Single-sample candidate comparisons are therefore
not sufficient to isolate a training effect; the next comparison must pair the
same inference seeds across candidates and report the distribution.

Same-agent adversarial review checked source observation substitution, raw
image/state equality, candidate/batch/sample/seed/joint ordering, finite action
values, reset and random-seed ordering, process separation, hidden action
application, checkpoint/runtime linkage, signed mutation, authority escalation,
and cleanup side effects. Eighty relevant tests pass, and all four batches plus
the aggregate gate reverify from live files.

T20.26 grants only a verified current-runtime inference-variability result. It
does not authorize an optimizer, accept a policy, or grant transfer, promotion,
hardware, external-compute, or Brev authority.

# Reviewer Decision 186 - Verify T20.25 Frozen-Candidate Localization

`ACCEPT_VERIFIED_DIAGNOSTIC_BLOCK_TRAINING_ATTRIBUTION`

Reviewed Brief 156 through artifact commit `c234936` and gate identity
`fdaa6fa9afa6ad45ab66e91f1c8c965556caff278587d6953e92b5d50d7db522`.

Both immutable adapters ran one complete unassisted 244-frame trace on each of
held-out seeds 6 and 7. All four traces begin from the exact source reset,
retain finite requested actions and MuJoCo states, use no projection or
assistance, and remain negative with no strict contact. The source episode,
training summary, checkpoint, seed, frame, phase, and action-sequence bindings
verify.

Both candidates diverge from the source at frame zero. Averaged across seeds,
clean-base frame-zero action MAE is 0.50735 rad and pre-contact MAE is 0.40137
rad. Recovery-augmented frame-zero MAE is 0.61872 rad and pre-contact MAE is
0.35402 rad. Recovery training therefore regresses this sampled frame-zero
metric by 0.11137 rad while improving sampled pre-contact MAE by 0.04735 rad.
The candidates themselves differ at frame zero by 0.11977 / 0.10384 rad on
seeds 6 / 7 and first produce distinct visited qpos at frame 1.

The recovery adapter reproduces both prior action hashes exactly. The clean
adapter does not reproduce its prior seed-6 action hash; an independent rerun
through the original T20.17 evaluation function produces the same new hash as
T20.25, while the current and prior LeRobot stack identities are equal. This
is a measured cross-process frozen-inference reproducibility gap. It prevents
attributing the sampled clean-versus-recovery deltas solely to training.

Same-agent adversarial review checked source substitution, candidate and seed
ordering, frame and phase ordering, joint-vector finiteness, identical reset,
requested-versus-applied action semantics, projection/assistance, checkpoint
identity, prior-hash claims, signed mutation, authority escalation, and cleanup
side effects. Seventy-seven relevant tests pass, and all four traces plus the
aggregate gate reverify from live files.

T20.25 grants only a verified offline diagnostic. It does not authorize more
optimizer work, accept a policy, or grant transfer, promotion, hardware,
external-compute, or Brev authority. The next safe task is repeated frozen
inference to quantify within-candidate variability before any training-effect
claim or additional optimizer rung.

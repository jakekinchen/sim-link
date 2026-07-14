# Reviewer Decision 161 - Verify T20.11 Action Localization

`CONTINUE`

Reviewed implementation boundaries `aa6351c66a83c36b81c56454a176adb5c60cca74`
and `fc02af1dcf7c869a6fa5a48fe7a8dc79286fc1f2`, plus comparison-gate identity
`dcbf6c58a453376358a62c8dbbc6622f6006a07ea861eb785d20ccd5a1a8173a`.

All four frozen T20.7 checkpoints were re-hashed and rerun from the identical
seed-2 reset under T20.10 release semantics. Their action-sequence hashes,
keyframes, strict counts, and behavior outcomes are identical to T20.7. Each
result compares all 244 requested actions to the immutable source action at the
same frame and reports first divergence plus phase/joint error profiles. No
cross-model training-loss scale is used.

Every model diverges at frame 0. PI0.5 is the narrow diagnostic candidate: its
five non-gripper joints average 0.03097 rad absolute error versus the 0.05 rad
audit threshold, while its gripper error is 0.75432 rad versus the 0.5 rad
large-error threshold. SmolVLA's first error is also gripper (1.77453 rad), but
its non-gripper average is 0.25102 rad. ACT and Diffusion are broadly wrong at
the reset, led by wrist roll at 1.72632 rad and elbow flex at 2.52320 rad.
Diffusion still projects 52 frames. No model achieves strict contact.

The gate therefore selects `pi05_gripper_channel_semantics_or_weighting` only
as the next audit hypothesis; PI0.5 is explicitly not a winner. Eighty-three
relevant tests pass, and the signed comparison gate recomposes from all four
outputs. Continue to a source/processor/normalization/postprocessor/loss audit
of PI0.5's gripper channel before any optimizer run. Do not accept a policy or
grant hardware, physical transfer, promotion, external-compute, or Brev
authority.

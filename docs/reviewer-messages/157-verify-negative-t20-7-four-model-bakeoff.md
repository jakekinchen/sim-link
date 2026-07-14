# Reviewer Decision 157 - Verify Negative T20.7 Four-Model Bake-Off

`CONTINUE`

Reviewed implementation boundary `26e68b4f2b36d0c329ac8fbb28e77b981d940d08`,
training gate identity `08d02eb0...`, and evaluation gate identity
`9dd450c9...`.

All four models consumed the exact same 20 starts and completed finite local-
MPS optimizer steps. Their checkpoints were re-hashed before identical
policy-owned seed-2 evaluation. Each rollout contains five verified 256 px
keyframes, all measured-versus-threshold strict margins, an action-sequence
hash, and zero assistance. Initialization asymmetry remains explicit and no
cross-model loss ranking was used.

The behavior comparison has zero strict successes and no winner. PI0.5,
SmolVLA, and Diffusion lift only 0.0003007 mm; ACT reaches 2.4213 mm but misses
the lift threshold by 22.5787 mm and has zero strict contacts. Visual review
shows ACT's gripper remains below and offset from the object. Diffusion also
has 52 projected-action frames versus the allowed zero, so it is comparison-
ineligible in addition to failing strict success.

Verify T20.7 as a negative bake-off and continue only to T20.8's fail-closed
acceptance decision. Do not name a winner, accept a policy, resume the same
training hypothesis, or grant physical transfer, promotion, hardware,
external-compute, or Brev authority.

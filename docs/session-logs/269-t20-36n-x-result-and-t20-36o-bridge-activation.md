# Session Log 269 - T20.36n X Result and T20.36o Bridge Activation

## Evidence

- Attempt identity: `141fc0ba77b4b6347526fda60612c9d433dab3f368ed371f14c3ea912eda0e2b`.
- Tracked tensor identity: `9d7a517a5fef520d68182c127eacf2ff2a29d0f93cf50746d79f6d5a39fd4ab1`;
  file SHA-256 `6e684ede640fffcc0b442b7622ef728b7bac2da026e8f5dcf1ee4c319e185b72`.
- Signed run identity: `95e2279a5597811f6fb83b08ced5c80c83a138f827068fc8d7a16b49b3f03435`.
- Final tracked result identity:
  `f8d7866e852a9b9a288b724016abe104dc94bf631251023faa8d26dbf5b86eb7`;
  file SHA-256 `78b591b503463fedda174031b65ee3568df9cf50fa8cdb694bb55cadb78892d8`.
- Result boundary: `a20f2a4de1b4d8ec7f12142015d44bdecff6a345`, confirmed on origin.
- Verification: all five source hashes reproduced; both repeats bit-identical;
  retained tensor verifier and fresh-checkout rescore pass; 31
  focused/current/pointer tests pass.
- Historical T20.35x spec reconstruction is hardened against at most `5e-14`
  absolute derived-float reduction-order drift while preserving the exact
  signed archive and correction-example hash.

## Result

T20.36n is an exact mixed-negative. The objective ratio `0.0025221206` and the
original uniform Gate B pass for all five seeds. Frozen amendment
`463477dc...` passes three seeds and reports five grasp/gripper-only misses at
timesteps 33-36, each only `0.00034185`-`0.00441953` rad beyond its 0.025-rad
ceiling. Reviewer 266 closes the one-use reproduction without retry.

The owner-directed Gate C route remains open for X, but Gate C execution is
closed. Brief 208 activates T20.36o model-free design. The bridge freezes a new
PI0.5 execution contract at 50 queued actions, one reset, starts
0/50/100/150/200, executed lengths 50/50/50/50/44, and exclusion of the last
six unexecuted predictions from acceptance and actor-valid evidence. No model,
optimizer, rollout, hardware, network, external compute, or Brev action is
authorized by this activation.

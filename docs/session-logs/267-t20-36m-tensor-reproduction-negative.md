# Session Log 267 - T20.36m Tensor Reproduction Negative

## Evidence

- Attempt marker: `c69d3904fe59ccb04e5f3d077d3f8b145eacfa63a874237270336ae62f10cbf4`.
- Tensor artifact: `45a3369d3944b0c7090cc86e571006f0701a7a29d7db37b9e536a3034f62392c`.
- Run summary: `0b7c98b67ee7bcc5bd1b742c7ed0d884c1c3959934bd136f3d9c0fb51fa8217a`.
- Tracked result: `4f101f38c87c2a7d8d64aab8956a0da41d036019f8df697ed2d7c6863bbd9532`;
  file SHA-256 `49168612423d8b9c5a77440c08b39cb2e163bbec67274e3e488bdb41efd0532b`.
- Result boundary: `a5e7c6adf7f2c51b6708640a419a1c14989da6bf`, confirmed on origin.
- All five signed source hashes reproduced and both repeats were bit-identical.
- Frozen amended Gate B: five failures, 162 total violations, no Gate C route.

## Result

Reviewer 264 verifies the exact SmolVLA negative reproduction. The one-use
permit is consumed, SmolVLA has no retry or Gate C route, and T20.36n becomes
the next dependency-ready task because retained T20.35x lacks decoded tensors
for the mandated amended-gate score. No optimizer, gate change, hardware,
network, external compute, or Brev action occurred.

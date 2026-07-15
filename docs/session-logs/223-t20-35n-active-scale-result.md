# Session Log 223 - T20.35n Active-Scale Result

## Evidence

- Result commit: `4e37e19480e384fd9c44f28bcf0c183e5588e9cc`.
- Attempt identity: `c8eecd80ace5a168625038fcb65a6c840eeab137cab653ba0b76d24254f151a8`.
- Result identity: `d3e6e5d96f9ddc462c0840c5baa72f864fb7b6c1ddc2ec00bce0ded03394fe7b`.
- File SHA-256: `81a264c16ad1c820914c1c969b942c86c9fa072531f7fca2a8cc544fff9133f9`.
- Python 3.12 signed verifier and focused tests pass.

## Result

Active scales 0/0.25/0.5/1 produce worst errors
`0.066398`/`0.082665`/`0.102040`/`0.150321` rad with padded noise normal.
Active zero remains best, but Gate B fails.

Reviewer 220 routes T20.35o to one separately reviewed flow-trajectory
consistency audit. No optimizer, training, mutation, rollout, Gate C, hardware,
external compute, or Brev action occurred.

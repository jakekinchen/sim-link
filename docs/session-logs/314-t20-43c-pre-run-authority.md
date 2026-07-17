# Session 314 - T20.43c Pre-Run Authority

**Date:** 2026-07-16
**Task:** T20.43c / Brief 227
**Reviewer:** 310

Reconstructed the six T20.43c authority artifacts from origin commit
`02496f0eb9f09b4d84d06750143ddf06d202592a`. The central decision grants only
`simulation_training_ready`; source failure/checkpoint/trace identities,
dependencies, MPS, disk, origin, implementation cleanliness, smoke output, and
absent/unalias output paths all pass.

Acceptance `010d0a43...` (file SHA `b1afe12f...`) binds permit `166a6cd0...`,
Reviewer 310 file SHA `5973c8ee...`, and authority commit `02496f0...`. No
marker or checkpoint tensor/model/optimizer action occurred before this
acceptance. Once this boundary is exact on origin and the authority window
remains active, the sole marker may be created and the bit-exact equivalence
gate executed before update 1. Hardware, network, external compute, Brev,
retry, and replacement remain closed.

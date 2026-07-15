# Session Log 225 - T20.35o Flow-Trajectory Result

## Evidence

- Result commit: `30b5b0a`.
- Attempt identity: `5161631f161864da872478e1da27cca24efec57db565794f6c7c944199f628a8`.
- Result identity: `5c5b41b99d83b1e5116195bab551277d3b65126066717823342030b23391a582`.
- File SHA-256: `15a768e653871e72d892250d61333252792b945798cdc1b5e43478dfc23cc92a`.
- Size: 5,815,635 bytes.
- Python 3.12 signed verifier and 30 relevant tests pass.

## Result

All five active-zero/padded-normal endpoints reproduce exactly. Active
velocity residual rises from `0.033131` at time 1.0 to `0.368387` at time 0.1,
and the final three steps contain `62.8898%` of active residual mass. The
largest channel share is only `24.7865%`, so Reviewer 222 classifies a
late-step distributed residual and routes one separately reviewed
terminal-time flow-consistency correction. Gate B and Gate C remain closed.

No optimizer, training, mutation, rollout, hardware, external compute, or Brev
action occurred.

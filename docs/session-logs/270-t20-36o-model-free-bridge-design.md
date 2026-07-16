# Session Log 270 - T20.36o Model-Free Bridge Design

## Evidence

- Bridge design identity:
  `8294c63be101dbb1ea3536d2b2da1447d23ca9aa71d2145eb501452547c30c0c`.
- File SHA-256:
  `4a0d2850a279d93df3429fdd98bb27e6bebc734023ecc75b67e06e1b772d5dbb`.
- PI0.5 source SHA-256: `b05b6afe70a4a09f2eb610827b9ae09e8b08e43cd748d435e47879344e3fa619`.
- LeRobot revision: `e40b58a8dfa9e7b86918c374791599d070518d11`.
- Episode-0 source bytes: `586a3e67...`; raw identity `9e186088...`;
  dataset parquet `7843e531...`.
- Verification: exact generator/verifier, six focused semantic/drift tests,
  and project-pointer tests pass.

## Result

The new execution contract is exact: one reset, 50-action queue, starts
0/50/100/150/200, lengths 50/50/50/50/44, and six final tail positions excluded
from loss, acceptance, and actor evidence. All source frames, phases,
observations, images, and targets are directly bound. After manager review,
acceptance uses amendment `463477dc...` unchanged: relative offsets 0-31 use
the signed reach table, 32-49 use the signed grasp table, and only the final
six unexecuted positions are masked. The earlier minimum-envelope artifact is
superseded without rewriting history.

The fallback training schedule is bounded at 250 examples times ten uses,
2,500 updates, unchanged LR, paired unique standard replay, and first confirmed
pass. An update-0 multi-state probe comes first; it can eliminate training.
Reviewer 267 verifies the design and routes only to separate baseline-inference
authority implementation. No model, checkpoint tensor, optimizer, Gate C,
hardware, network, external compute, or Brev action occurred.

# Session Log 270 - T20.36o Model-Free Bridge Design

## Evidence

- Bridge design identity:
  `b44bd55bdf99d684223bf8c1b4c195f12b841ba1b1323df0e488939df60f3845`.
- File SHA-256:
  `7893785bd66b2cd6dbe7c6029bff49b8d5e1bcc168a421fbc7a1bb07dda23ea3`.
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
observations, images, and targets are directly bound. Acceptance uses the
strict per-joint envelope of frozen amendment `463477dc...`.

The fallback training schedule is bounded at 250 examples times ten uses,
2,500 updates, unchanged LR, paired unique standard replay, and first confirmed
pass. An update-0 multi-state probe comes first; it can eliminate training.
Reviewer 267 verifies the design and routes only to separate baseline-inference
authority implementation. No model, checkpoint tensor, optimizer, Gate C,
hardware, network, external compute, or Brev action occurred.
